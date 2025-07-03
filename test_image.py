import streamlit as st
from PIL import Image

st.title("배경 이미지 테스트")

try:
    img = Image.open('./images/soccer_field.png')
    st.image(img, caption="축구장 배경 이미지", use_column_width=True)
except Exception as e:
    st.error(f"이미지 로딩 실패: {e}")
