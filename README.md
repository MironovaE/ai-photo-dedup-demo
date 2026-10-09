# Умная чистка фото

Находит почти одинаковые кадры среди загруженных фотографий и собирает их в группы, чтобы
было видно, что можно удалить, а что оставить.

**Демо:** https://ai-photo-dedup-demo.streamlit.app/

Если своих фото под рукой нет, в приложении есть кнопка «Попробовать на примерах».

## Как это работает

1. Каждое фото прогоняется через ResNet50 без последнего слоя — на выходе вектор признаков
   (эмбеддинг) длиной 2048.
2. Векторы нормализуются и кластеризуются DBSCAN по косинусному расстоянию.
3. Фото из одного кластера считаются похожими. Ползунок «Чувствительность» — это `eps` DBSCAN:
   чем меньше, тем строже.

Файлы обрабатываются в памяти и нигде не сохраняются.

## Запуск локально

```bash
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` рассчитан на Streamlit Cloud (Linux, CPU-сборка torch). На macOS поставьте
`torch` и `torchvision` тех же версий без суффикса `+cpu`.

## Стек

Python, Streamlit, PyTorch / torchvision (ResNet50), scikit-learn (DBSCAN), Pillow.

## Примеры фото

Снимки в `sample_photos/` — с [Unsplash](https://unsplash.com), авторы перечислены
в [`sample_photos/CREDITS.md`](sample_photos/CREDITS.md).
