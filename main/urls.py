from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('teacher/', views.teacher_panel, name='teacher'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('teacher/check/', views.teacher_check, name='teacher_check'),
    path('admin/check/', views.admin_check, name='admin_check'),
    path('logout/', views.logout_view, name='logout'),
    path('classroom/', views.classroom_view, name='classroom_view'),
    path('api/analyze-image/', views.analyze_image_view, name='analyze_image'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)