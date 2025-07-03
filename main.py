import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import requests
import io
import base64  # ← 이 부분 꼭 추가

@st.cache_data
def load_img(url):
    resp = requests.get(url)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    return img

img_url = "https://m1.daumcdn.net/cfile293/image/222F6F4952E838EF11455C"
img = load_img(img_url)

buffered = io.BytesIO()
img.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()

canvas_result = st_canvas(
    background_image=None,
    background_image_url=f"data:image/png;base64,{img_b64}",
    height=img.height,
    width=img.width,
    stroke_width=3,
    stroke_color="#000000",
    fill_color="rgba(255, 0, 0, 0.3)",
    drawing_mode="freedraw",
    key="test_canvas",
)
