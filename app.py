import streamlit as st

st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="centered")

st.title("🎬 나와 어울리는 영화는?")
st.write("간단한 5문항으로 당신의 성향을 알아보고, 어울리는 영화 타입을 찾아봐요! 🍿")

st.divider()

questions = [
    {
        "q": "1. 주말에 가장 하고 싶은 것은?",
        "options": ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"]
    },
    {
        "q": "2. 스트레스 받으면?",
        "options": ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"]
    },
    {
        "q": "3. 영화에서 중요한 것은?",
        "options": ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"]
    },
    {
        "q": "4. 여행 스타일?",
        "options": ["계획적", "즉흥적", "액티비티", "힐링"]
    },
    {
        "q": "5. 친구 사이에서 나는?",
        "options": ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"]
    }
]

answers = {}

for item in questions:
    answers[item["q"]] = st.radio(
        item["q"],
        item["options"],
        index=None,  # 아무것도 선택 안 된 상태로 시작
        key=item["q"]
    )
    st.write("")

st.divider()

if st.button("결과 보기", use_container_width=True):
    # 아직 API 연동 전: 버튼 누르면 분석 중...만 표시
    st.info("분석 중... 🔎 잠시만 기다려줘!")
