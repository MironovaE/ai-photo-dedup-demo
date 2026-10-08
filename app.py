import base64
import io
import os
import tempfile

import streamlit as st
from PIL import Image, ImageOps

from dedup_engine import cluster_similar_photos

REPO_URL = "https://github.com/MironovaE/ai-photo-dedup-demo"
LOGO_PATH = "ai_bot.png"
SAMPLES_DIR = "sample_photos"
THUMB_SIZE = 240
THUMBS_PER_ROW = 4

if "lang" not in st.session_state:
    st.session_state.lang = "ru"


def toggle_language():
    st.session_state.lang = "ru" if st.session_state.lang == "en" else "en"


def plural_ru(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


TEXTS = {
    "en": {
        "page_title": "Smart Photo Cleaner",
        "title": "Smart Photo Cleaner",
        "tagline": "Finds near-identical shots so you keep only the best ones.",
        "intro": "Drop in photos from a walk or a trip. Similar frames are grouped together, "
                 "so it's easy to see what can go.",
        "privacy": "Files are processed in memory and deleted right after the analysis.",
        "upload_label": "Photos (JPG or PNG, at least 2)",
        "sensitivity_label": "Sensitivity",
        "sensitivity_help": "Lower is stricter: only near-identical shots get grouped together.",
        "min_files": "Add at least two photos to start.",
        "try_samples": "Try with sample photos",
        "samples_active": "Showing sample photos. Upload your own to analyze them instead.",
        "analyzing": "Analyzing {} photos…",
        "no_duplicates": "No similar photos found — every shot is unique.",
        "groups_title": "Similar shots",
        "viewer_title": "Preview",
        "group_header": "Group {} · {} photos",
        "open": "Open",
        "opened": "Viewing",
        "total_photos": "Total photos",
        "keep": "Keep",
        "can_remove": "Can remove",
        "switch_lang": "RU",
        "footer": "Demo · ResNet50 embeddings + DBSCAN · [Source code]({})",
    },
    "ru": {
        "page_title": "Умная чистка фото",
        "title": "Умная чистка фото",
        "tagline": "Находит почти одинаковые кадры, чтобы оставить только лучшие.",
        "intro": "Загрузите снимки с прогулки или из отпуска. Похожие кадры соберутся в группы — "
                 "сразу видно, что можно удалить.",
        "privacy": "Файлы обрабатываются в памяти и удаляются сразу после анализа.",
        "upload_label": "Фотографии (JPG или PNG, минимум 2)",
        "sensitivity_label": "Чувствительность",
        "sensitivity_help": "Чем меньше, тем строже: в группу попадут только почти одинаковые кадры.",
        "min_files": "Добавьте хотя бы две фотографии, чтобы начать.",
        "try_samples": "Попробовать на примерах",
        "samples_active": "Показаны примеры. Загрузите свои фото, чтобы проверить их.",
        "analyzing": "Анализируем фото: {}…",
        "no_duplicates": "Похожих фото не нашлось — все кадры разные.",
        "groups_title": "Похожие группы",
        "viewer_title": "Просмотр",
        "group_header": "Группа {} · {} фото",
        "open": "Открыть",
        "opened": "Открыта",
        "total_photos": "Всего фото",
        "keep": "Оставить",
        "can_remove": "Можно удалить",
        "switch_lang": "EN",
        "footer": "Демо · эмбеддинги ResNet50 + DBSCAN · [Исходный код]({})",
    },
}


def groups_found_text(n):
    if st.session_state.lang == "en":
        return f"Found {n} group{'s' if n != 1 else ''} of similar photos."
    return f"{plural_ru(n, 'Найдена', 'Найдено', 'Найдено')} {n} " \
           f"{plural_ru(n, 'группа', 'группы', 'групп')} похожих фото."


t = TEXTS[st.session_state.lang]

st.set_page_config(
    page_title=t["page_title"],
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else None,
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2.5rem; max-width: 1200px; }
    .app-header { display: flex; align-items: center; gap: 14px; }
    .app-header img { width: 56px; height: 56px; border-radius: 12px; }
    .app-header h1 { font-size: 1.75rem; margin: 0; padding: 0; line-height: 1.2; }
    .app-header p { margin: 2px 0 0; color: #6b6f76; }
    .intro { max-width: 680px; margin: 1.25rem 0 0.25rem; line-height: 1.6; }
    .muted { color: #6b6f76; font-size: 0.875rem; }
    .viewer {
        aspect-ratio: 4 / 3;
        max-height: 70vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f0efea;
        border-radius: 10px;
    }
    .viewer img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        border-radius: 6px;
    }
    /* Streamlit гасит виджеты на время перерисовки — при листании это выглядит как мигание */
    [data-stale="true"] { opacity: 1 !important; transition: none !important; }
    .viewer-caption { text-align: center; margin: 8px 0 0; }
    .counter { text-align: center; padding-top: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_sample_photos():
    if not os.path.isdir(SAMPLES_DIR):
        return []
    names = sorted(f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    return [(name, os.path.getsize(os.path.join(SAMPLES_DIR, name)), os.path.join(SAMPLES_DIR, name))
            for name in names]


def select_group(cid):
    st.session_state.selected_group = cid
    st.session_state.viewer_index = 0


def step_viewer(delta):
    st.session_state.viewer_index += delta


def image_to_base64(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()


header_col, lang_col = st.columns([10, 1])

with header_col:
    logo_html = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_html = f'<img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}">'
    st.markdown(
        f"""
        <div class="app-header">
            {logo_html}
            <div><h1>{t['title']}</h1><p>{t['tagline']}</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with lang_col:
    st.button(t["switch_lang"], on_click=toggle_language, use_container_width=True)

st.markdown(
    f'<p class="intro">{t["intro"]}<br><span class="muted">{t["privacy"]}</span></p>',
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    t["upload_label"],
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.session_state.use_samples = False
    photos = [(f.name, f.size, f) for f in uploaded_files]
elif st.session_state.get("use_samples"):
    photos = load_sample_photos()
    st.caption(t["samples_active"])
else:
    photos = []
    if os.path.isdir(SAMPLES_DIR):
        st.button(t["try_samples"], on_click=lambda: st.session_state.update(use_samples=True))

slider_col, _ = st.columns([2, 3])
with slider_col:
    eps = st.slider(
        t["sensitivity_label"],
        min_value=0.05,
        max_value=0.50,
        value=0.25,
        step=0.05,
        help=t["sensitivity_help"],
    )

if len(photos) < 2:
    st.caption(t["min_files"])
else:
    file_info = tuple(sorted((name, size) for name, size, _ in photos))
    cache_key = (file_info, eps)

    if st.session_state.get("last_cache_key") != cache_key:
        all_images = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            for name, _, source in photos:
                img = Image.open(source).convert("RGB")
                all_images[name] = img
                img.save(os.path.join(tmpdir, name))

            with st.spinner(t["analyzing"].format(len(photos))):
                clusters = cluster_similar_photos(tmpdir, eps=eps)

        st.session_state.clusters = clusters
        st.session_state.all_images = all_images
        st.session_state.last_cache_key = cache_key
        st.session_state.selected_group = None
        st.session_state.viewer_index = 0

    clusters = st.session_state.clusters
    all_images = st.session_state.all_images

    duplicate_groups = {k: v for k, v in clusters.items() if len(v) > 1}
    total_remove = sum(len(files) - 1 for files in duplicate_groups.values())

    st.divider()
    a, b, c = st.columns(3)
    a.metric(t["total_photos"], len(photos))
    b.metric(t["keep"], len(photos) - total_remove)
    c.metric(t["can_remove"], total_remove)

    if not duplicate_groups:
        st.info(t["no_duplicates"])
    else:
        st.write(groups_found_text(len(duplicate_groups)))

        if st.session_state.get("selected_group") not in duplicate_groups:
            st.session_state.selected_group = next(iter(duplicate_groups))
            st.session_state.viewer_index = 0

        groups_col, viewer_col = st.columns([5, 7], gap="large")

        with groups_col:
            st.subheader(t["groups_title"])
            for number, (cid, files) in enumerate(duplicate_groups.items(), start=1):
                is_selected = cid == st.session_state.selected_group
                with st.container(border=True):
                    st.markdown(f"**{t['group_header'].format(number, len(files))}**")

                    for row_start in range(0, len(files), THUMBS_PER_ROW):
                        cols = st.columns(THUMBS_PER_ROW)
                        for col, filename in zip(cols, files[row_start:row_start + THUMBS_PER_ROW]):
                            thumb = ImageOps.fit(all_images[filename], (THUMB_SIZE, THUMB_SIZE))
                            col.image(thumb, use_column_width=True)

                    st.button(
                        t["opened"] if is_selected else t["open"],
                        key=f"open_{cid}",
                        type="primary" if is_selected else "secondary",
                        on_click=select_group,
                        args=(cid,),
                    )

        with viewer_col:
            st.subheader(t["viewer_title"])
            files = duplicate_groups[st.session_state.selected_group]
            idx = st.session_state.viewer_index % len(files)
            current_name = files[idx]
            preview = all_images[current_name].copy()
            preview.thumbnail((1600, 1600))

            st.markdown(
                f"""
                <div class="viewer">
                    <img src="data:image/jpeg;base64,{image_to_base64(preview, 'JPEG')}" alt="{current_name}">
                </div>
                <p class="viewer-caption muted">{current_name}</p>
                """,
                unsafe_allow_html=True,
            )

            _, prev_col, counter_col, next_col, _ = st.columns([2, 1, 1, 1, 2])
            prev_col.button("←", key="prev", use_container_width=True, on_click=step_viewer, args=(-1,))
            counter_col.markdown(
                f'<p class="counter muted">{idx + 1} / {len(files)}</p>',
                unsafe_allow_html=True,
            )
            next_col.button("→", key="next", use_container_width=True, on_click=step_viewer, args=(1,))

st.divider()
st.caption(t["footer"].format(REPO_URL))
