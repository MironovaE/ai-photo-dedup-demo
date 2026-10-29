**English** | [Русский](README.ru.md)

# Similar shots, side by side

This demo groups visually similar photos and shows them together. Upload your own pictures or open
four real photo series; you decide which shots to keep.

**Live demo:** https://ai-photo-dedup-demo.streamlit.app/

No photos handy? Click **Explore sample photos** in the app. Free Streamlit hosting may put the demo
to sleep after a period of inactivity. If you see **Yes, get this app back up!**, click it and give
the app about a minute to start.

![Groups of similar shots from the sample set](docs/screenshot.jpg)

## How it works

1. ResNet50 without its final classification layer turns each photo into a 2,048-dimensional
   feature vector (embedding).
2. The embeddings are normalized and clustered with DBSCAN using cosine distance.
3. Photos in the same cluster appear together. The **Sensitivity** slider controls DBSCAN's `eps`:
   lower values produce stricter groups.

Uploaded photos stay in the current session. The app creates temporary files for analysis and
removes them as soon as analysis finishes.

## Limits

- The model groups similar shots; it does not choose the best photo or delete anything.
- Uploads support JPG and PNG. Convert iPhone HEIC photos before uploading.
- ResNet50 was trained on ImageNet. It recognizes similar scenes well, but may group distinct
  pictures of the same scene. Adjust the sensitivity when needed.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` targets Streamlit Cloud on Linux and pins CPU builds of PyTorch. On macOS,
install matching `torch` and `torchvision` versions without the `+cpu` suffix.

## Stack

Python, Streamlit, PyTorch / torchvision (ResNet50), scikit-learn (DBSCAN), Pillow.

## Sample photos

The 12 photos in `sample_photos/` are from Katherine Mironova's own collection. The public demo
uses resized copies with EXIF and location metadata removed. See
[`sample_photos/CREDITS.md`](sample_photos/CREDITS.md).
