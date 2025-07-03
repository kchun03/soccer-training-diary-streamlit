import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import requests
import io
from datetime import date
import sqlite3
import base64

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

@st.cache_data(show_spinner=False)
def load_image(url):
    resp = requests.get(url)
    img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    return img

court_img_url = "https://m1.daumcdn.net/cfile293/image/222F6F4952E838EF11455C"

try:
    court_img = load_image(court_img_url)
    canvas_width, canvas_height = court_img.size
except Exception:
    st.warning("이미지 로드 실패, 기본 크기로 설정합니다.")
    court_img = None
    canvas_width, canvas_height = 700, 400

st.title("⚽ 축구 훈련 일지 & 드로잉")
st.markdown("### 축구 코트 위에 자유롭게 훈련 내용을 그림으로 표현하세요!")

# background_image가 None일 땐 인자에서 제외
canvas_kwargs = dict(
    fill_color="rgba(255, 0, 0, 0.3)",
    stroke_width=3,
    stroke_color="#000000",
    height=canvas_height,
    width=canvas_width,
    drawing_mode="freedraw",
    key="canvas",
)

if isinstance(court_img, Image.Image):
    canvas_kwargs["background_image"] = court_img

canvas_result = st_canvas(**canvas_kwargs)

with st.form("form"):
    diary_date = st.date_input("날짜", value=date.today())
    status = st.radio("오늘 훈련은 어땠나요?", ["아주 좋았어요 😊", "괜찮았어요 🙂", "힘들었어요 😓", "별로였어요 😞"])
    good = st.text_area("잘한 점")
    bad = st.text_area("못한 점")
    submitted = st.form_submit_button("저장")

    if submitted:
        drawing_b64 = None
        if canvas_result.image_data is not None:
            img = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            drawing_b64 = base64.b64encode(buf.getvalue()).decode()

        cur.execute(
            "INSERT INTO diary (diary_date, status, good, bad, drawing) VALUES (?, ?, ?, ?, ?)",
            (str(diary_date), status, good, bad, drawing_b64)
        )
        conn.commit()
        st.success("일지가 저장되었습니다!")

st.markdown("---")
st.subheader("작성된 훈련 일지")

cur.execute("SELECT * FROM diary ORDER BY diary_date DESC")
rows = cur.fetchall()

for row in rows:
    with st.expander(f"{row[1]} - {row[2]}"):
        st.write(f"✅ 잘한 점: {row[3]}")
        st.write(f"❌ 못한 점: {row[4]}")
        if row[5]:
            img = Image.open(io.BytesIO(base64.b64decode(row[5])))
            st.image(img, caption="훈련 드로잉", use_column_width=True)
        if st.button("삭제", key=f"del_{row[0]}"):
            cur.execute("DELETE FROM diary WHERE id=?", (row[0],))
            conn.commit()
            st.success("삭제 완료!")
            st.experimental_rerun()
