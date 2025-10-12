# app.py
import streamlit as st
import os
import tempfile
import base64
from dedup_engine import cluster_similar_photos
from PIL import Image

# --- Управление языком ---
if "lang" not in st.session_state:
    st.session_state.lang = "ru"

def toggle_language():
    st.session_state.lang = "ru" if st.session_state.lang == "en" else "en"

# --- Словари локализации ---
LANG = {
    "en": {
        "page_title": "Smart Photo Cleaner — AI Dedup Demo",
        "title": "Smart Photo Cleaner",
        "subtitle": "Tired of hundreds of nearly identical photos from walks and vacations?",
        "how_it_works": """**Just drop them here!**  
AI will find duplicates and similar shots, so you can keep only the best — and enjoy your memories, not the hassle.

ℹ️ Tip: Upload at least 2 photos (JPG/PNG) to start the analysis.  
ℹ️ Security: All files are deleted immediately after analysis — we store nothing.""",
        "upload_label": "Upload your photos",
        "sensitivity_label": "🔍 Sensitivity (lower = stricter)",
        "sensitivity_help": "Lower values mean only very similar photos will be grouped",
        "min_files_msg": "⬆️ Please upload at least 2 photos to start the analysis.",
        "analyzing": "🧠 AI is analyzing {} photos...",
        "no_duplicates": "✅ No duplicates found! All photos look unique.",
        "unique_found": "ℹ️ Found {} unique photos.",
        "duplicates_found": "🎯 Found {} group(s) of similar photos!",
        "group_header": "Group {} ({} similar photos)",
        "summary": "📊 Summary",
        "total_photos": "Total Photos",
        "keep": "Keep",
        "can_remove": "Can Remove",
        "free_space": "✨ You could free up space by removing {} duplicate(s)!",
        "switch_lang": "🇷🇺 Русский",
        "clusters_title": "📸 Clusters",
        "enlarge_title": "🔍 Photo Carousel",
        "select_cluster": "Click on a cluster header to view its photos."
    },
    "ru": {
        "page_title": "Умная чистка фото — Демо ИИ",
        "title": "Умная чистка фото",
        "subtitle": "Устали от сотен почти одинаковых фото с прогулок и отпуска?",
        "how_it_works": """**Просто загрузите их сюда!**  
ИИ найдёт дубликаты и похожие снимки, чтобы вы могли оставить только лучшие — и наслаждаться воспоминаниями, а не рутиной.

ℹ️ Совет: Загрузите минимум 2 фото (JPG/PNG), чтобы начать анализ.  
ℹ️ Безопасность: Все файлы удаляются сразу после анализа — мы ничего не храним.""",
        "upload_label": "Загрузите ваши фото",
        "sensitivity_label": "🔍 Чувствительность (меньше = строже)",
        "sensitivity_help": "Меньшие значения означают, что в группу попадут только очень похожие фото",
        "min_files_msg": "⬆️ Загрузите минимум 2 фото, чтобы начать анализ.",
        "analyzing": "🧠 ИИ анализирует {} фото...",
        "no_duplicates": "✅ Дубликаты не найдены! Все фото выглядят уникальными.",
        "unique_found": "ℹ️ Найдено {} уникальных фото.",
        "duplicates_found": "🎯 Найдено {} групп(ы) похожих фото!",
        "group_header": "Группа {} ({} похожих фото)",
        "summary": "📊 Итог",
        "total_photos": "Всего фото",
        "keep": "Оставить",
        "can_remove": "Можно удалить",
        "free_space": "✨ Вы можете освободить место, удалив {} дубликат(ов)!",
        "switch_lang": "🇺🇸 English",
        "clusters_title": "📸 Кластеры",
        "enlarge_title": "🔍 Карусель фото",
        "select_cluster": "Нажмите на заголовок кластера, чтобы посмотреть его фото."
    }
}

t = LANG[st.session_state.lang]

# --- Настройки страницы ---
st.set_page_config(
    page_title=t["page_title"],
    page_icon="🤖",
    layout="wide"
)

# --- Общий CSS (включая стили карусели — НЕ ТРОГАТЬ!) ---
st.markdown(
    """
    <style>
    div[data-testid="stColumn"]:nth-child(2) .stVerticalBlock {
        align-items: flex-end !important;
    }
    .custom-gradient-box {
        background: linear-gradient(90deg, #e6fff2 0%, #fff2cc 50%, #ffe6e6 100%);
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #003366;
        font-size: 16px;
        line-height: 1.6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Убираем лишние отступы у кнопок */
    div[data-testid="column"] > div > div > div > button {
        margin-bottom: 0 !important;
        padding: 8px 16px !important;
    }

    /* СТИЛИ КАРУСЕЛИ — СВЯЩЕННЫЕ, НЕ МЕНЯТЬ! */
    .carousel-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-top: 8px;
    }
    .carousel-img {
        max-height: 80vh;
        max-width: 900px;
        width: auto;
        height: auto;
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        background: white;
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Заголовок ---
header_col1, header_col2 = st.columns([8, 2])

with header_col1:
    if os.path.exists("ai_bot.png"):
        with open("ai_bot.png", "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="data:image/png;base64,{img_data}" width="80" style="margin: 0; padding: 0;">
                <h3 style="margin: 0; padding: 0; line-height: 1.2;">{t['title']}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"### {t['title']}")

with header_col2:
    st.button(t["switch_lang"], on_click=toggle_language)

# --- Основной текст ---
st.subheader(t["subtitle"])

text = t["how_it_works"]
lines = text.split('\n')
formatted_lines = []
if lines and lines[0].strip():
    first_line = lines[0].strip().replace("**", "<strong>", 1).replace("**", "</strong>", 1)
    formatted_lines.append(f"<p style='margin:0; padding:0; line-height:1.6;'>{first_line}</p>")
if len(lines) > 1 and lines[1].strip():
    formatted_lines.append(f"<p style='margin:0; padding:0; line-height:1.6;'>{lines[1].strip()}</p>")
formatted_lines.append("<p style='margin:0; padding:0; line-height:1.6;'>&nbsp;</p>")
for line in lines[2:]:
    if line.strip():
        line_html = line.strip().replace("ℹ️", '<span style="color:#0066cc;">ℹ️</span>')
        formatted_lines.append(f"<p style='margin:0; padding:0; line-height:1.6;'>{line_html}</p>")
text_html = "\n".join(formatted_lines)
st.markdown(f'<div class="custom-gradient-box">{text_html}</div>', unsafe_allow_html=True)

# --- Загрузка ---
uploaded_files = st.file_uploader(
    t["upload_label"],
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

col1, col2 = st.columns([3, 1])
with col1:
    eps = st.slider(
        t["sensitivity_label"],
        min_value=0.05,
        max_value=0.50,
        value=0.25,
        step=0.05,
        help=t["sensitivity_help"]
    )
with col2:
    st.write("")

# --- Состояние для карусели ---
if "carousel_images" not in st.session_state:
    st.session_state.carousel_images = []
if "carousel_filenames" not in st.session_state:
    st.session_state.carousel_filenames = []
if "carousel_index" not in st.session_state:
    st.session_state.carousel_index = 0

# --- Анализ с кэшированием (всё в памяти, без временных файлов после анализа) ---
if uploaded_files and len(uploaded_files) >= 2:
    file_info = tuple(sorted((f.name, f.size) for f in uploaded_files))
    cache_key = ("clusters", file_info, eps)

    if ("last_cache_key" not in st.session_state) or (st.session_state.last_cache_key != cache_key):
        all_images = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            for f in uploaded_files:
                img = Image.open(f).convert('RGB')
                all_images[f.name] = img.copy()
                img.save(os.path.join(tmpdir, f.name))

            with st.spinner(t["analyzing"].format(len(uploaded_files))):
                clusters = cluster_similar_photos(tmpdir, eps=eps)

        st.session_state.clusters = clusters
        st.session_state.all_images = all_images
        st.session_state.last_cache_key = cache_key
    else:
        clusters = st.session_state.clusters
        all_images = st.session_state.all_images

    duplicate_groups = {k: v for k, v in clusters.items() if len(v) > 1}
    unique_count = sum(1 for v in clusters.values() if len(v) == 1)

    if not duplicate_groups:
        st.success(t["no_duplicates"])
        if unique_count > 0:
            st.info(t["unique_found"].format(unique_count))
    else:
        st.success(t["duplicates_found"].format(len(duplicate_groups)))

        left_col, right_col = st.columns([1, 2])

        with left_col:
            st.markdown(f"<h3 style='text-align: center; margin: 0;'>{t['clusters_title']}</h3>", unsafe_allow_html=True)
            for cid, files in duplicate_groups.items():
                image_objects = [all_images[f] for f in files]

                btn_label = f"📁 {t['group_header'].format(cid, len(files))}"
                if st.button(btn_label, key=f"cluster_btn_{cid}"):
                    st.session_state.carousel_images = image_objects
                    st.session_state.carousel_filenames = files
                    st.session_state.carousel_index = 0
                    # ✅ НЕТ st.rerun() — Streamlit сам обновит UI

                cols = st.columns(min(3, len(files)))
                for i, (img_obj, filename) in enumerate(zip(image_objects, files)):
                    with cols[i % len(cols)]:
                        ratio = 150 / img_obj.width
                        new_height = int(img_obj.height * ratio)
                        thumb = img_obj.resize((150, new_height), Image.LANCZOS)
                        st.image(
                            thumb,
                            caption=filename[:25] + ("..." if len(filename) > 25 else ""),
                            width=150
                        )
                st.divider()

        with right_col:
            st.markdown(f"<h3 style='text-align: center; margin: 0;'>{t['enlarge_title']}</h3>", unsafe_allow_html=True)
            if st.session_state.carousel_images:
                images = st.session_state.carousel_images
                filenames = st.session_state.carousel_filenames
                idx = st.session_state.carousel_index % len(images)
                current_img = images[idx]
                current_name = filenames[idx]

                import io
                buf = io.BytesIO()
                current_img.save(buf, format="PNG")
                img_base64 = base64.b64encode(buf.getvalue()).decode()

                html = f"""
                <div class="carousel-container">
                    <img src="data:image/png;base64,{img_base64}" class="carousel-img" alt="{current_name}">
                </div>
                <p style="text-align:center; margin-top:8px; font-size:14px; color:#666;"><i>{current_name}</i></p>
                """
                st.markdown(html, unsafe_allow_html=True)

                col_center = st.columns([1, 2, 1])
                with col_center[1]:
                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        if st.button("⬅️", key="prev_btn", use_container_width=True):
                            st.session_state.carousel_index = (st.session_state.carousel_index - 1) % len(images)
                            # ✅ НЕТ st.rerun() — Streamlit сам обновит
                    with btn_cols[1]:
                        if st.button("➡️", key="next_btn", use_container_width=True):
                            st.session_state.carousel_index = (st.session_state.carousel_index + 1) % len(images)
                            # ✅ НЕТ st.rerun() — Streamlit сам обновит

            else:
                st.info(t["select_cluster"])

        # --- Итог ---
        total_keep = len(duplicate_groups)
        total_remove = sum(len(files) - 1 for files in duplicate_groups.values())
        st.subheader(t["summary"])
        a, b, c = st.columns(3)
        a.metric(t["total_photos"], len(uploaded_files))
        b.metric(t["keep"], total_keep)
        c.metric(t["can_remove"], total_remove)
        if total_remove > 0:
            st.success(t["free_space"].format(total_remove))

# --- Footer ---
st.markdown("---")
if st.session_state.lang == "en":
    st.caption("Smart Photo Cleaner Demo • Powered by ResNet50 + DBSCAN • [Source Code on GitHub]")
else:
    st.caption("Демо умной чистки фото • На основе ResNet50 + DBSCAN • [Исходный код на GitHub]")