import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import requests
import io
import numpy as np
from datetime import date
import sqlite3
import base64

# DB 초기화
conn = sqlite3.connect("diary.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS diary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diary_date TEXT,
    status TEXT,
    good TEXT,
    bad TEXT,
    drawing TEXT
)
""")
conn.commit()

# 이미지 로드 함수
@st.cache_data
def load_image_from_url(url):
    response = requests.get(url, timeout=5)
    image = Image.open(io.BytesIO(response.content)).convert("RGBA")
    return image

# 이미지 URL
court_img_url = "https://m1.daumcdn.net/cfile293/image/222F6F4952E838EF11455C"

# 이미지 로딩
try:
    court_img = load_image_from_url(court_img_url)
    canvas_width, canvas_height = court_img.size
except Exception as e:
    st.warning("⚠️ 축구 코트 이미지를 불러올 수 없습니다. 빈 캔버스를 사용합니다.")
    court_img = None
    canvas_width = 700
    canvas_height = 400

st.title("⚽ 축구 훈련 일지 & 코트 드로잉")

st.markdown("### 오늘은 이런 훈련을 했어요? (코트 위에 자유롭게 그림)")

# canvas 출력
canvas_result = st_canvas(
    fill_color="rgba(255, 0, 0, 0.3)",
    stroke_width=3,
    stroke_color="#000000",
    background_image=court_img if court_img else None,
    height=canvas_height,
    width=canvas_width,
    drawing_mode="freedraw",
    key="soccer_court",
)

# 일지 작성 폼
with st.form("entry_form"):
    diary_date = st.date_input("날짜", value=date.today())
    status = st.radio("오늘 훈련은 어땠나요?", ["아주 좋았어요 😊", "괜찮았어요 🙂", "힘들었어요 😓", "별로였어요 😞"])
    good = st.text_area("잘한 점")
    bad = st.text_area("못한 점")

    submitted = st.form_submit_button("작성 완료")

    if submitted:
        drawing_b64 = None
        if canvas_result.image_data is not None:
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            drawing_b64 = base64.b64encode(buffered.getvalue()).decode()

        cur.execute("""
            INSERT INTO diary (diary_date, status, good, bad, drawing)
            VALUES (?, ?, ?, ?, ?)
        """, (str(diary_date), status, good, bad, drawing_b64))
        conn.commit()
        st.success("✅ 일지가 저장되었습니다!")

# 작성된 일지 목록 출력
st.markdown("---")
st.subheader("📋 작성된 훈련 일지")

cur.execute("SELECT * FROM diary ORDER BY diary_date DESC")
rows = cur.fetchall()

for row in rows:
    with st.expander(f"📅 {row[1]} - {row[2]}"):
        st.write(f"✅ 잘한 점: {row[3]}")
        st.write(f"❌ 못한 점: {row[4]}")
        if row[5]:
            img_bytes = base64.b64decode(row[5])
            img = Image.open(io.BytesIO(img_bytes))
            st.image(img, caption="훈련 코트 드로잉", use_column_width=True)
        delete = st.button("🗑️ 삭제", key=f"delete_{row[0]}")
        if delete:
            cur.execute("DELETE FROM diary WHERE id = ?", (row[0],))
            conn.commit()
            st.success(f"삭제 완료: {row[1]} 일지")
            st.rerun()
