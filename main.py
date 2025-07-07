import streamlit as st
from datetime import date, datetime
import psycopg2
from psycopg2 import Binary
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io
import os
import socket
import traceback
from collections import defaultdict

# 버전 확인용
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

# 페이지 설정
st.set_page_config(page_title="훈련 일지", layout="wide")

# --- 꿀렁임 방지용 meta viewport와 CSS ---
st.components.v1.html("""
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<style>
    html, body, .main {
        overflow-x: hidden;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    section.main > div:first-child {
        padding-top: 0rem !important;
    }
    header {
        padding: 0 !important;
        margin: 0 !important;
    }
    div.block-container {
        padding-top: 0 !important;
    }
    div[data-testid="stCanvas"] canvas {
        max-width: 100% !important;
        height: auto !important;
    }
    .stTextInput, .stTextArea {
        max-width: 100% !important;
        box-sizing: border-box;
    }
    img {
        max-width: 100% !important;
        height: auto;
        display: block;
    }
    .css-1y4p8pa {
        overflow-wrap: break-word;
        word-break: break-word;
    }
</style>
""", height=0)

# canvas 버전 체크
try:
    canvas_version = version("streamlit-drawable-canvas")
except Exception:
    pass

# 환경 설정
hostname = socket.gethostname()
is_prod = "streamlit" in hostname.lower()

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

# 🔗 Supabase PostgreSQL 연결
try:
    conn = psycopg2.connect(
        host="aws-0-ap-northeast-2.pooler.supabase.com",
        port=6543,
        dbname="postgres",
        user="postgres.cpcgldgyqzvxmsddussr",
        password="Qwer1234!",  # 👉 여기에 실제 비밀번호 입력
        sslmode="require"
    )
    cur = conn.cursor()
    st.success("✅ DB 연결 성공")

    # 🔽 테이블 생성은 연결 성공한 후에만 실행
    cur.execute("""
    CREATE TABLE IF NOT EXISTS diary (
        id serial PRIMARY KEY,
        diary_date date,
        status text,
        good text,
        bad text,
        drawing bytea
    )
    """)
    conn.commit()

except Exception as e:
    st.error(f"❌ DB 연결 실패 또는 테이블 생성 오류: {e}")
    st.stop()  # ⚠️ 이후 코드 중단

# 타이틀
st.markdown("""<h1 style='margin-top: 0;'>⚽ 이윤성 축구 훈련 일지</h1>""", unsafe_allow_html=True)

# 배경 이미지 로딩
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

if isinstance(bg_image, Image.Image):
    background_for_canvas = np.array(bg_image) if is_prod else bg_image
else:
    background_for_canvas = None

# 📝 일지 작성 폼
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

        try:
            cur.execute(
                "INSERT INTO diary (diary_date, status, good, bad, drawing) VALUES (%s, %s, %s, %s, %s)",
                (diary_date, status, good, bad, Binary(drawing_data))
            )
            conn.commit()
            st.success("✅ 일지가 저장되었습니다!")
        except Exception as e:
            st.error(f"DB 저장 중 오류 발생: {e}")
            st.text(traceback.format_exc())

# 📋 일지 목록 조회
st.markdown("---")
st.subheader("📋 작성된 훈련 일지")

try:
    cur.execute("SELECT id, diary_date, status, good, bad, drawing FROM diary ORDER BY diary_date DESC")
    rows = cur.fetchall()
except Exception as e:
    st.error(f"DB 조회 중 오류 발생: {e}")
    rows = []

grouped = defaultdict(list)
for row in rows:
    dt = row[1]  # date 타입
    ym_key = dt.strftime("%Y-%m")
    grouped[ym_key].append(row)

selected_diary = None  # 상세 표시용

for ym in sorted(grouped.keys(), reverse=True):
    dt_obj = datetime.strptime(ym, "%Y-%m")
    with st.expander(f"📆 {dt_obj.year}년 {dt_obj.month}월", expanded=False):
        for r in grouped[ym]:
            toggle_key = f"toggle_{r[0]}"
            if toggle_key not in st.session_state:
                st.session_state[toggle_key] = False

            if st.button(
                f"{'🔽' if st.session_state[toggle_key] else '▶️'} {r[1]} - {r[2]}",
                key=f"btn_{r[0]}"
            ):
                for other in grouped[ym]:
                    st.session_state[f"toggle_{other[0]}"] = (other[0] == r[0] and not st.session_state[toggle_key])
                st.experimental_rerun()

            if st.session_state[toggle_key]:
                selected_diary = r

if selected_diary:
    st.markdown("---")
    st.subheader(f"📝 {selected_diary[1]} 훈련 일지 상세")
    st.markdown(f"**상태:** {selected_diary[2]}")
    st.markdown(f"**잘한 점:**\n{selected_diary[3]}")
    st.markdown(f"**못한 점:**\n{selected_diary[4]}")

    if selected_diary[5]:
        try:
            img = Image.open(io.BytesIO(selected_diary[5]))
            st.image(img, caption="훈련 그림", use_column_width=True)
        except Exception as e:
            st.error(f"그림 표시 중 오류: {e}")
else:
    st.info("날짜를 클릭하면 해당 훈련 일지 상세를 볼 수 있습니다.")
