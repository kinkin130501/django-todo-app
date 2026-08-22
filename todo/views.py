import openpyxl
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone
from .models import Task

# Auth Views
def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Tự động đăng nhập ngay sau khi đăng ký thành công
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'todo/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'todo/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# Helper filter logic
def get_filtered_tasks(request):
    tasks = Task.objects.filter(user=request.user)
    
    date_filter = request.GET.get('date_filter')
    specific_date = request.GET.get('specific_date')
    week = request.GET.get('week')
    month = request.GET.get('month')
    year = request.GET.get('year')
    search = request.GET.get('search')
    status = request.GET.get('status')

    if date_filter == 'current_week':
        today = timezone.now().date()
        start_week = today - timezone.timedelta(days=today.weekday())
        end_week = start_week + timezone.timedelta(days=6)
        tasks = tasks.filter(date__range=[start_week, end_week])
    elif specific_date:
        tasks = tasks.filter(date=specific_date)
    
    if week:
        tasks = tasks.filter(date__week=week)
    if month:
        tasks = tasks.filter(date__month=month)
    if year:
        tasks = tasks.filter(date__year=year)
    if status:
        tasks = tasks.filter(status=status)
    if search:
        tasks = tasks.filter(Q(title__icontains=search) | Q(note__icontains=search))

    return tasks.order_by('date', 'time')

# Main Dashboard View
@login_required
def index_view(request):
    return render(request, 'todo/index.html')

# AJAX API Endpoints
@login_required
def task_list_api(request):
    tasks = get_filtered_tasks(request)
    data = []
    for t in tasks:
        data.append({
            'id': t.id,
            'title': t.title,
            'description': t.description or '',
            'note': t.note or '',
            'date': str(t.date),
            'time': str(t.time),
            'status': t.status,
            'status_display': t.get_status_display(),
            'is_past': t.is_in_past()
        })
    return JsonResponse({'tasks': data})

@login_required
def task_create_api(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        note = request.POST.get('note')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        status = request.POST.get('status', 'PLANNED')

        task_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        if timezone.make_aware(task_dt) < timezone.now():
            return JsonResponse({'error': 'Không thể tạo lịch trong quá khứ!'}, status=400)

        task = Task.objects.create(
            user=request.user, title=title, description=description,
            note=note, date=date_str, time=time_str, status=status
        )
        return JsonResponse({'message': 'Tạo công việc thành công!'})

@login_required
def task_update_api(request, pk):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk, user=request.user)
        note = request.POST.get('note')
        
        if task.is_in_past():
            # Chỉ cho phép sửa ghi chú nếu công việc ở quá khứ
            task.note = note
            task.save()
            return JsonResponse({'message': 'Đã cập nhật ghi chú cho công việc trong quá khứ.'})
        
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.note = note
        task.date = request.POST.get('date')
        task.time = request.POST.get('time')
        task.status = request.POST.get('status')
        task.save()
        return JsonResponse({'message': 'Cập nhật thành công!'})

@login_required
def task_delete_api(request, pk):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.delete()
        return JsonResponse({'message': 'Đã xoá công việc!'})

@login_required
def export_excel_api(request):
    tasks = get_filtered_tasks(request)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách công việc"

    headers = ['ID', 'Tên công việc', 'Mô tả', 'Ghi chú', 'Ngày', 'Giờ', 'Trạng thái']
    ws.append(headers)

    for t in tasks:
        ws.append([t.id, t.title, t.description, t.note, str(t.date), str(t.time), t.get_status_display()])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=danh_sach_cong_viec.xlsx'
    wb.save(response)
    return response