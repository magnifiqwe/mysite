from django.db import models
from django.contrib.auth.models import User


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField("ФИО", max_length=100)

    def __str__(self):
        return self.full_name


class Student(models.Model):
    name = models.CharField("ФИО студента", max_length=100)
    group = models.CharField("Группа", max_length=50)

    def __str__(self):
        return f"{self.name} ({self.group})"


class Subject(models.Model):
    name = models.CharField("Название предмета", max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")

    def __str__(self):
        return self.name


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    date = models.DateField("Дата")
    present = models.BooleanField("Присутствовал", default=False)

    def __str__(self):
        return f"{self.student} | {self.subject} | {self.date}"


class ClassroomData(models.Model):
    student_count = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now=True)