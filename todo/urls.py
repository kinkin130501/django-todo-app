from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path('api/tasks/', views.task_list_api, name='task_list_api'),
    path('api/tasks/create/', views.task_create_api, name='task_create_api'),
    path('api/tasks/update/<int:pk>/', views.task_update_api, name='task_update_api'),
    path('api/tasks/delete/<int:pk>/', views.task_delete_api, name='task_delete_api'),
    path('api/tasks/export/', views.export_excel_api, name='export_excel_api'),
]