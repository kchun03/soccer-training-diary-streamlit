import streamlit as st
from datetime import date
import sqlite3

# DB 연결 및 테이블 생성
conn = sqlite3.connect("diary.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS diary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diary_date TEXT,
    status TEXT,
    good TEXT,
    bad TEXT
)
""")
conn.commit()

st.title("⚽ 이윤성 축구 훈련 일지")

# 📋 일지 작성 폼
with st.form("entry_form"):
    diary_date = st.date_input("날짜", value=date.today())
    status = st.selectbox("오늘 훈련은 어땠나요?", ["아주 좋았어요 😊", "괜찮았어요 🙂", "힘들었어요 😓", "별로였어요 😞"])
    good = st.text_area("잘한 점")
    bad = st.text_area("못한 점")
    submitted = st.form_submit_button("작성 완료")

    if submitted:
        cur.execute("INSERT INTO diary (diary_date, status, good, bad) VALUES (?, ?, ?, ?)",
                    (str(diary_date), status, good, bad))
        conn.commit()
        st.success("✅ 일지가 저장되었습니다!")

# 📋 일지 목록
st.markdown("---")
st.subheader("📋 작성된 훈련 일지")

cur.execute("SELECT * FROM diary ORDER BY diary_date DESC")
rows = cur.fetchall()

for row in rows:
    with st.expander(f"📅 {row[1]} - {row[2]}"):
        st.write(f"✅ 잘한 점: {row[3]}")
        st.write(f"❌ 못한 점: {row[4]}")
        
        delete = st.button("🗑️ 삭제", key=f"delete_{row[0]}")
        if delete:
            cur.execute("DELETE FROM diary WHERE id = ?", (row[0],))
            conn.commit()
            st.success(f"삭제 완료: {row[1]} 일지")
            st.rerun()  # 최신 Streamlit에서는 이 함수로 새로고침
