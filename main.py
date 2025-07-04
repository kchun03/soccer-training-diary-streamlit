import streamlit as st
from datetime import date
import sqlite3
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io
import os
import socket
import traceback

# 버전 확인용 - pkg_resources 제거하고 권장 방식으로 변경
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # Python < 3.8 호환용

# 페이지 설정
st.set_page_config(page_title="훈련 일지", layout="wide")

# --- 꿀렁임 방지용 meta viewport와 CSS ---
st.components.v1.html("""
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<style>
    /* 전체 가로 스크롤 숨기기 */
    html, body, .main {
        overflow-x: hidden;
    }

    /* st_canvas 캔버스 100% 반응형 */
    div[data-testid="stCanvas"] canvas {
        max-width: 100% !important;
        height: auto !important;
    }

    /* 입력 폼 텍스트 입력, 텍스트 영역 최대 너비 */
    .stTextInput, .stTextArea {
        max-width: 100% !important;
        box-sizing: border-box;
    }

    /* 이미지 크기 조정 (일지 내 드로잉 이미지 포함) */
    img {
        max-width: 100% !important;
        height: auto;
        display: block;
    }

    /* 마크다운 텍스트 줄바꿈 강제 */
    .css-1y4p8pa {
        overflow-wrap: break-word;
        word-break: break-word;
    }
</style>
""", height=0)

# 버전 확인 (필요하면 주석처리 가능)
try:
    canvas_version = version("streamlit-drawable-canvas")
    # st.info(f"🧩 streamlit-drawable-canvas version: {canvas_version}")
except Exception:
    pass

# 운영환경 여부 판단
hostname = socket.gethostname()
is_prod = "streamlit" in hostname.lower()

# 테스트 모드
query_params = st.experimental_get_query_params()
is_test = query_params.get("test", ["0"])[0] == "1"

if is_test:
    st.title("🎯 이미지 테스트 모드")
    try:
        test_img_path = os.path.join("images", "soccer_field.jpg")
        test_img = Image.open(test_img_path).convert("RGBA").transpose(Image.ROTATE_90)
        st.image(test_img, caption="✅ 테스트 이미지 로딩 성공", use_column_width=True)
    except Exception as e:
        st.error(f"❌ 테스트 이미지 로딩 실패: {e}")
    st.stop()

# DB 연결
conn = sqlite3.connect("diary.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS diary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diary_date TEXT,
    status TEXT,
    good TEXT,
    bad TEXT,
    drawing BLOB
)
""")
conn.commit()

st.title("⚽ 이윤성 축구 훈련 일지")

# 이미지 로딩
img_path = os.path.join("images", "soccer_field.jpg")
bg_image = None
canvas_width, canvas_height = 600, 400

try:
    if os.path.exists(img_path):
        bg_image = Image.open(img_path).convert("RGBA")
        max_canvas_width = 800
        img_ratio = bg_image.width / bg_image.height
        canvas_width = min(max_canvas_width, bg_image.width)
        canvas_height = int(canvas_width / img_ratio)
        bg_image = bg_image.resize((canvas_width, canvas_height))
    else:
        st.error("⚠️ 이미지 파일이 없습니다.")
except Exception as e:
    st.error(f"❌ 이미지 처리 중 오류: {e}")
    st.text(traceback.format_exc())

# 운영 환경에 따라 캔버스 배경 이미지 타입 결정
if isinstance(bg_image, Image.Image):
    background_for_canvas = np.array(bg_image) if is_prod else bg_image
else:
    background_for_canvas = None

# 입력 폼
with st.form("entry_form"):
    diary_date = st.date_input("날짜", value=date.today())
    status = st.radio("오늘 훈련은 어땠나요?", ["아주 좋았어요 😊", "괜찮았어요 🙂", "힘들었어요 😓", "별로였어요 😞"])

    st.markdown("### ✏️ 오늘은 이런 훈련을 했어요")

    try:
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=3,
            stroke_color="#000000",
            background_image=background_for_canvas,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="freedraw",
            key="canvas",
            display_toolbar=True,
        )
    except Exception as e:
        st.error(f"❌ st_canvas 생성 실패: {e}")
        st.text(traceback.format_exc())

    good = st.text_area("잘한 점")
    bad = st.text_area("못한 점")

    submitted = st.form_submit_button("작성 완료")

    if submitted:
        drawing_data = None
        if canvas_result.image_data is not None and bg_image is not None:
            try:
                user_drawing = Image.fromarray(np.uint8(canvas_result.image_data)).convert("RGBA")
                user_drawing = user_drawing.resize(bg_image.size)
                final_img = Image.alpha_composite(bg_image, user_drawing)

                buffer = io.BytesIO()
                final_img.save(buffer, format="PNG")
                drawing_data = buffer.getvalue()
                st.success("✅ 그림 저장 성공")
            except Exception as e:
                st.error(f"🖼️ 그림 저장 중 오류 발생: {e}")
                st.text(traceback.format_exc())
        else:
            st.warning("⚠️ 드로잉 데이터 또는 배경 이미지 없음")

        cur.execute(
            "INSERT INTO diary (diary_date, status, good, bad, drawing) VALUES (?, ?, ?, ?, ?)",
            (str(diary_date), status, good, bad, drawing_data)
        )
        conn.commit()
        st.success("✅ 일지가 저장되었습니다!")

# 작성된 일지 리스트
st.markdown("---")
st.subheader("📋 작성된 훈련 일지")

cur.execute("SELECT id, diary_date, status, good, bad, drawing FROM diary ORDER BY diary_date DESC")
rows = cur.fetchall()

for row in rows:
    with st.expander(f"📅 {row[1]} - {row[2]}"):
        if row[5]:
            try:
                img = Image.open(io.BytesIO(row[5]))
                st.image(img, caption="오늘은 이런 훈련을 했어요", use_column_width=True)
            except Exception as e:
                st.warning(f"이미지를 불러올 수 없습니다: {e}")
        else:
            st.info("✏️ 드로잉이 없습니다.")

        st.markdown(f"✅ **잘한 점:**\n\n{row[3]}")
        st.markdown(f"❌ **못한 점:**\n\n{row[4]}")

        delete = st.button("🗑️ 삭제", key=f"delete_{row[0]}")
        if delete:
            cur.execute("DELETE FROM diary WHERE id = ?", (row[0],))
            conn.commit()
            st.success(f"삭제 완료: {row[1]} 일지")
            st.experimental_rerun()
