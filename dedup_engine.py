import logging
import os
from collections import defaultdict
from functools import lru_cache

import numpy as np
import torch
from PIL import Image
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
from torchvision.models import resnet50, ResNet50_Weights

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')


@lru_cache(maxsize=1)
def _load_model():
    weights = ResNet50_Weights.DEFAULT
    model = resnet50(weights=weights)
    # Без последнего слоя на выходе получаем эмбеддинг, а не классы ImageNet
    model = torch.nn.Sequential(*list(model.children())[:-1])
    model.eval()
    return model, weights.transforms()


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
    image_files = sorted(f for f in os.listdir(folder_path) if f.lower().endswith(IMAGE_EXTENSIONS))
    if not image_files:
        return {}

    model, transform = _load_model()

    embeddings = []
    valid_files = []

    for filename in image_files:
        try:
            img = Image.open(os.path.join(folder_path, filename)).convert('RGB')
            with torch.no_grad():
                emb = model(transform(img).unsqueeze(0)).squeeze().numpy()
        except Exception:
            logger.exception("Не удалось обработать файл %s", filename)
            continue

        embeddings.append(emb)
        valid_files.append(filename)

    if not embeddings:
        return {}

    embeddings = normalize(np.array(embeddings))
    labels = DBSCAN(eps=eps, metric='cosine', min_samples=1).fit_predict(embeddings)

    groups = defaultdict(list)
    for fname, label in zip(valid_files, labels):
        groups[int(label)].append(fname)

    return dict(groups)
