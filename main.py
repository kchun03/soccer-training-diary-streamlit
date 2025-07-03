import streamlit as st
from datetime import date
import sqlite3
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io
import os

# ===================== 테스트 모드 분기 =====================
query_params = st.experimental_get_query_params()
is_test = query_params.get("test", ["0"])[0] == "1"

if is_test:
    st.title("🎯 이미지 테스트 모드")
    try:
        test_img_path = os.path.join("images", "soccer_field.jpg")
        st.write(f"테스트모드 이미지 경로: {test_img_path}")
        test_img = Image.open(test_img_path).convert("RGBA")
        st.image(test_img, caption="✅ 이미지 로딩 성공 (RGBA 모드)", use_column_width=True)
    except Exception as e:
        st.error(f"❌ 이미지 로딩 실패: {e}")
    st.stop()
# ==========================================================

# DB 연결 및 테이블 생성
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

# 축구장 배경 이미지 로컬 경로
img_path = os.path.join("images", "soccer_field.jpg")
st.write(f"운영서버 이미지 경로: {img_path}")

bg_image = None
canvas_width, canvas_height = 600, 400  # 기본값

try:
    if os.path.exists(img_path):
        st.write("이미지 파일 존재함.")
        bg_image = Image.open(img_path)
        st.write(f"원본 이미지 모드: {bg_image.mode}")

        bg_image = bg_image.convert("RGBA")
        st.write("RGBA 변환 완료")

        canvas_width = 600
        canvas_height = int(bg_image.height * (canvas_width / bg_image.width))
        st.write(f"리사이즈 예정: {canvas_width}x{canvas_height}")

        bg_image = bg_image.resize((canvas_width, canvas_height))
        st.write("리사이즈 완료")

        # RGB 변환 제거 — RGBA 유지
        st.write(f"최종 bg_image 모드: {bg_image.mode}")
    else:
        st.error("⚠️ 배경 이미지 파일이 없습니다.")
except Exception as e:
    st.error(f"⚠️ 이미지 처리 오류: {e}")

# background_image에 PIL.Image 또는 None 넘김
background_for_canvas = bg_image if isinstance(bg_image, Image.Image) else None
st.write(f"background_for_canvas 타입: {type(background_for_canvas)}")

# 📋 일지 작성 폼
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
            height=canvas_height if background_for_canvas else 400,
            width=canvas_width if background_for_canvas else 600,
            drawing_mode="freedraw",
            key="canvas",
        )
        st.write("캔버스 정상 생성됨")
    except Exception as e:
        st.error(f"캔버스 생성 오류: {e}")

    good = st.text_area("잘한 점")
    bad = st.text_area("못한 점")

    submitted = st.form_submit_button("작성 완료")

    if submitted:
        st.write("폼 제출됨")
        if canvas_result.image_data is not None and bg_image is not None:
            try:
                user_drawing = Image.fromarray(np.uint8(canvas_result.image_data)).convert("RGBA")
                user_drawing = user_drawing.resize(bg_image.size)

                final_img = Image.alpha_composite(bg_image, user_drawing)

                buffer = io.BytesIO()
                final_img.save(buffer, format="PNG")
                drawing_data = buffer.getvalue()
                st.write("이미지 합성 및 저장 성공")
            except Exception as e:
                st.error(f"🖼️ 그림 저장 중 오류 발생: {e}")
                drawing_data = None
        else:
            st.write("캔버스 데이터가 없거나 배경 이미지가 없습니다.")
            drawing_data = None

        cur.execute(
            "INSERT INTO diary (diary_date, status, good, bad, drawing) VALUES (?, ?, ?, ?, ?)",
            (str(diary_date), status, good, bad, drawing_data)
        )
        conn.commit()
        st.success("✅ 일지가 저장되었습니다!")

# 📋 일지 목록
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
            except:
                st.warning("이미지를 불러올 수 없습니다.")
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
