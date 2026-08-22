from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Task(models.Model):
    STATUS_CHOICES = [
        ('PLANNED', 'Đã lên kế hoạch'),
        ('IN_PROGRESS', 'Đang làm'),
        ('COMPLETED', 'Đã xong'),
        ('CANCELLED', 'Đã hủy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_in_past(self):
        task_datetime = timezone.datetime.combine(self.date, self.time)
        if timezone.is_naive(task_datetime):
            task_datetime = timezone.make_aware(task_datetime)
        return task_datetime < timezone.now()

    def clean(self):
        if not self.pk and self.is_in_past():
            raise ValidationError("Không thể tạo lịch ở thời điểm trong quá khứ.")

    def __str__(self):
        return f"{self.title} - {self.user.username}"