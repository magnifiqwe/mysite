from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from .models import Teacher, Subject, Student, ClassroomData
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
from datetime import datetime
import cv2
from ultralytics import YOLO


def index(request):
    return render(request, 'index.html')


def login_view(request, role):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if role == 'teacher':
                return redirect('teacher_panel')
            elif role == 'admin':
                return redirect('admin_panel')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'login.html')


def teacher_panel(request):
    return render(request, 'teacher.html')


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('index')
    return render(request, 'admin.html')


def teacher_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'teacher'):
            login(request, user)
            return redirect('teacher')
        else:
            return render(request, 'teacher_login.html', {'error': 'Неверный данные или вы не являетесь преподавателем'})
    return render(request, 'teacher_login.html')


def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Неверный данные или вы не являетесь администратором'})
    return render(request, 'login.html')


@login_required
def teacher_panel(request):
    try:
        teacher = request.user.teacher
    except:
        return redirect('index')

    subjects = Subject.objects.filter(teacher=teacher)
    students = Student.objects.all()
    return render(request, 'teacher.html', {
        'subjects': subjects,
        'students': students
    })


@login_required(login_url='/admin/login/')
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('index')
    return render(request, 'admin.html')


def teacher_check(request):
    if request.user.is_authenticated and hasattr(request.user, 'teacher'):
        return redirect('teacher')
    else:
        return redirect('teacher_login')


def admin_check(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('dashboard')
    else:
        return redirect('admin_login')


def logout_view(request):
    logout(request)
    return redirect('index')


def is_superuser(user):
    return user.is_superuser


@login_required
def admin_panel(request):
    return render(request, 'admin.html')


@login_required(login_url='/teacher/login/')
def classroom_view(request):
    if hasattr(request.user, 'teacher') or request.user.is_superuser:
        return render(request, 'classroom_view.html')
    else:
        return redirect('index')


@csrf_exempt
def get_student_count(request):
    if request.method == 'POST':
        frame = request.POST.get('image', None)

        if not frame:
            return JsonResponse({'count': 'Нет изображения'})

        try:
            model_response = requests.post(
                'http://localhost:5000/count_students',
                json={'image': frame}
            )

            data = model_response.json()
            count = data.get('count', 0)
        except Exception as e:
            count = 'Ошибка'

        return JsonResponse({'count': count})
    else:
        return JsonResponse({'count': '?'})


@login_required(login_url='/teacher/login/')
def classroom_view(request):
    # Проверяем тип пользователя
    is_teacher = hasattr(request.user, 'teacher')
    is_admin = request.user.is_superuser

    if not (is_teacher or is_admin):
        # Если пользователь не преподаватель и не админ - выходим и перенаправляем
        logout(request)
        return redirect('teacher_login')

    # Добавляем информацию о типе пользователя в контекст
    context = {
        'is_teacher': is_teacher,
        'is_admin': is_admin
    }
    return render(request, 'classroom_view.html', context)


@csrf_exempt
def analyze_image_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не разрешен'}, status=405)

    try:
        # Проверка наличия изображения
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Изображение не предоставлено'}, status=400)

        image_file = request.FILES['image']
        seats = int(request.POST.get('seats', 30))

        # Создаем временную папку, если ее нет
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Сохраняем временный файл
        temp_path = os.path.join(temp_dir, image_file.name)
        with open(temp_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        # Анализ изображения с YOLOv8
        result = analyze_with_yolov8(temp_path)

        # Расчет показателей
        student_count = result['person_count']
        occupancy_percent = min(100, round((student_count / seats) * 100, 1)) if seats > 0 else 0

        # Генерируем уникальное имя для обработанного изображения
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processed_filename = f"processed_{timestamp}_{image_file.name}"
        processed_path = os.path.join(settings.MEDIA_ROOT, 'processed', processed_filename)

        # Сохраняем обработанное изображение
        os.makedirs(os.path.dirname(processed_path), exist_ok=True)
        cv2.imwrite(processed_path, result['processed_image'])

        # URL для доступа к изображению
        processed_image_url = request.build_absolute_uri(
            f"{settings.MEDIA_URL}processed/{processed_filename}"
        )

        # Удаляем временный файл
        os.remove(temp_path)

        return JsonResponse({
            'success': True,
            'student_count': student_count,
            'seats': seats,
            'occupancy_percent': occupancy_percent,
            'processed_image_url': processed_image_url
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def analyze_with_yolov8(image_path):
    try:
        model = YOLO(os.path.join(settings.BASE_DIR, 'best (7).pt'))

        # Чтение изображения
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Не удалось прочитать изображение")

        # Детекция объектов
        #results = model(img, conf=0.5)  # Порог уверенности 50%
        results = model(img, conf=0.25)

        # Фильтрация только людей (класс 0)
        person_count = 0
        for result in results:
            for box in result.boxes:
                if int(box.cls) == 0:  # Класс 'person'
                    person_count += 1
                    # Рисуем bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    # Добавляем текст с уверенностью
                    conf = float(box.conf[0])
                    cv2.putText(img, f"{conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Добавляем счетчик на изображение
        cv2.putText(img, f"Students: {person_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return {
            'person_count': person_count,
            'processed_image': img
        }

    except Exception as e:
        raise Exception(f"Ошибка при анализе изображения: {str(e)}")
