# Register your models here.
from django.contrib import admin
from .models import Student, Subject, Attendance, Teacher

admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(Attendance)
admin.site.register(Teacher)
