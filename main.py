import streamlit as st
from datetime import date
import sqlite3
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io
import os

# 페이지 레이아웃 설정
st.set_page_config(page_title="훈련 일지", layout="wide")

# CSS - 캔버스 최대 너비 100%
st.markdown(
    """
    <style>
    div[data-testid="stCanvas"] canvas {
        max-width: 100% !important;
        height: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 테스트 모드
query_params = st.experimental_get_query_params()
is_test = query_params.get("test", ["0"])[0] == "1"

if is_test:
    st.title("🎯 이미지 테스트 모드")
    try:
        test_img_path = os.path.join("images", "soccer_field.jpg")
        st.write(f"✅ [TEST] 이미지 경로: {test_img_path}")
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

# 이미지 경로 지정
img_path = os.path.join("images", "soccer_field.jpg")
st.write(f"📁 이미지 경로 확인: `{img_path}`")

bg_image = None
canvas_width, canvas_height = 600, 400

try:
    if os.path.exists(img_path):
        st.success("✅ 이미지 파일 존재 확인")
        try:
            bg_image = Image.open(img_path)
            st.write(f"📐 원본 이미지 크기: {bg_image.size}")
            bg_image = bg_image.convert("RGBA")
            st.write("🔁 RGBA 변환 완료")
        except Exception as e:
            st.error(f"❌ 이미지 열기 실패: {e}")
            bg_image = None

        if bg_image:
            try:
                max_canvas_width = 800
                img_ratio = bg_image.width / bg_image.height
                canvas_width = min(max_canvas_width, bg_image.width)
                canvas_height = int(canvas_width / img_ratio)
                st.write(f"📏 캔버스 크기 설정: {canvas_width} x {canvas_height}")
                bg_image = bg_image.resize((canvas_width, canvas_height))
                st.success("✅ 이미지 리사이즈 완료")
            except Exception as e:
                st.error(f"❌ 이미지 리사이즈 실패: {e}")
    else:
        st.error("⚠️ 이미지 파일이 존재하지 않습니다.")
except Exception as e:
    st.error(f"❌ 이미지 처리 중 예외 발생: {e}")

background_for_canvas = bg_image if isinstance(bg_image, Image.Image) else None
st.write(f"🧾 background_for_canvas 타입: {type(background_for_canvas)}")

# 작성 폼
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
        st.write("🖼️ st_canvas 정상 생성됨")
    except Exception as e:
        st.error(f"❌ st_canvas 생성 실패: {e}")

    good = st.text_area("잘한 점")
    bad = st.text_area("못한 점")

    submitted = st.form_submit_button("작성 완료")

    if submitted:
        st.write("📥 폼 제출됨")
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
        else:
            st.warning("⚠️ 그림 데이터 또는 배경 이미지가 없습니다.")

        cur.execute(
            "INSERT INTO diary (diary_date, status, good, bad, drawing) VALUES (?, ?, ?, ?, ?)",
            (str(diary_date), status, good, bad, drawing_data)
        )
        conn.commit()
        st.success("✅ 일지가 저장되었습니다!")

# 작성된 일지 목록
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
