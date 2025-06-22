import os
import cv2
from ultralytics import YOLO
from django.conf import settings
import numpy as np


def analyze_image_with_yolov8(image_path):
    """Анализирует изображение с помощью YOLOv8 и возвращает результаты"""
    # Загрузка модели YOLOv8n
    model = YOLO('best1.pt')  # Убедитесь, что модель скачана

    # Обработка изображения
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Не удалось прочитать изображение")

    # Детекция объектов
    results = model(img, conf=0.5)  # Порог уверенности 50%

    # Фильтрация только людей (класс 0)
    person_count = 0
    for result in results:
        for box in result.boxes:
            if box.cls == 0:  # Класс 'person'
                person_count += 1

                # Рисуем bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Добавляем счетчик на изображение
    cv2.putText(img, f"Students: {person_count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Сохраняем обработанное изображение
    processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    processed_path = os.path.join(processed_dir, os.path.basename(image_path))
    cv2.imwrite(processed_path, img)

    return {
        'person_count': person_count,
        'processed_image_path': processed_path
    }