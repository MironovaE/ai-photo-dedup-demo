# dedup_engine.py
import os
from PIL import Image
import torch
import torchvision.transforms as T
from torchvision.models import resnet50, ResNet50_Weights
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
import numpy as np
from collections import defaultdict


def cluster_similar_photos(folder_path, eps=0.25):
    """
    Группирует похожие фотографии в папке по кластерам.

    Аргументы:
        folder_path (str): путь к папке с изображениями
        eps (float): порог сходства для DBSCAN (меньше → строже)

    Возвращает:
        dict: {номер_кластера: [имя_файла1, имя_файла2, ...]}
        или пустой dict, если изображений нет
    """
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]

    if not image_files:
        return {}

    # Загружаем модель
    weights = ResNet50_Weights.DEFAULT
    model = resnet50(weights=weights)
    model.eval()
    model = torch.nn.Sequential(*list(model.children())[:-1])  # Убираем последний слой

    transform = weights.transforms()

    # Устройство — всегда CPU для надёжности
    device = torch.device("cpu")
    model = model.to(device)

    embeddings = []
    valid_files = []

    for filename in image_files:
        try:
            img_path = os.path.join(folder_path, filename)
            img = Image.open(img_path).convert('RGB')

            # Применяем трансформацию и отправляем на устройство
            inp = transform(img).unsqueeze(0).to(device)

            with torch.no_grad():
                emb = model(inp)
                emb = emb.squeeze().cpu().numpy()  # Явно переносим в CPU и в numpy

            embeddings.append(emb)
            valid_files.append(filename)

        except Exception as e:
            import traceback
            print(f"❌ Ошибка при обработке файла {filename}:")
            traceback.print_exc()
            continue

    if not embeddings:
        return {}

    # Нормализуем и кластеризуем
    embeddings = np.array(embeddings)
    embeddings = normalize(embeddings)
    clustering = DBSCAN(eps=eps, metric='cosine', min_samples=1)
    labels = clustering.fit_predict(embeddings)

    # Группируем
    groups = defaultdict(list)
    for fname, label in zip(valid_files, labels):
        groups[int(label)].append(fname)

    return dict(groups)