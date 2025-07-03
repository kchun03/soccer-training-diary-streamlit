import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import requests
import io

@st.cache_data
def load_img(url):
    resp = requests.get(url)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    return img

img_url = "https://m1.daumcdn.net/cfile293/image/222F6F4952E838EF11455C"
img = load_img(img_url)
st.write(type(img))  # <class 'PIL.PngImagePlugin.PngImageFile'> 형태인지 확인

canvas_result = st_canvas(
    background_image=img,
    height=img.height,
    width=img.width,
    stroke_width=3,
    stroke_color="#000000",
    fill_color="rgba(255, 0, 0, 0.3)",
    drawing_mode="freedraw",
    key="test_canvas",
)
