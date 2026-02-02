import streamlit as st

st.set_page_config(page_title="🎬 나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# -----------------------------
# Header
# -----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("5개의 질문에 답하면, 당신과 어울리는 영화 스타일을 알려드려요! 🎞️✨")
st.caption("※ 지금은 화면/흐름만 구현되어 있어요. 결과 분석은 다음 시간에 연결합니다.")

st.divider()

# -----------------------------
# Questions (radio)
# - Choices must NOT explicitly mention movie types
# -----------------------------
questions = [
    {
        "q": "1. 시험이 끝난 날, 너는 어떤 하루를 보내고 싶어?",
        "options": [
            "조용한 카페에서 감성적으로 하루를 정리한다",
            "친구들과 바로 여행이나 액티비티를 즐긴다",
            "집에서 새로운 세계관에 빠져든다",
            "가볍게 웃을 수 있는 콘텐츠 보면서 쉰다",
        ],
    },
    {
        "q": "2. 친구가 갑자기 “오늘 영화 보자!”고 하면?",
        "options": [
            "여운 남는 이야기가 좋아",
            "박진감 넘치고 몰입감 강한 게 좋아",
            "상상력이 터지는 설정이면 좋아",
            "웃다가 끝나는 편한 분위기가 좋아",
        ],
    },
    {
        "q": "3. 너의 연애 스타일은 영화로 치면?",
        "options": [
            "감정선이 중요하고 서사가 탄탄한 편",
            "적극적이고 이벤트가 많은 편",
            "특별한 운명 같은 느낌을 믿는 편",
            "티격태격해도 웃음이 많은 편",
        ],
    },
    {
        "q": "4. 대학생활에서 가장 기대되는 순간은?",
        "options": [
            "사람들과 깊은 이야기 나누는 밤",
            "MT나 축제처럼 에너지 넘치는 날",
            "새로운 경험과 낯선 자극",
            "친구들이랑 아무 말이나 하며 웃는 시간",
        ],
    },
    {
        "q": "5. 네가 주인공이라면 어떤 캐릭터일까?",
        "options": [
            "감정을 섬세하게 품고 성장하는 주인공",
            "위기 속에서도 돌파하는 주인공",
            "다른 세계를 탐험하는 주인공",
            "주변을 즐겁게 만드는 주인공",
        ],
    },
]

answers = {}

for item in questions:
    answers[item["q"]] = st.radio(
        item["q"],
        item["options"],
        index=None,  # 선택 강제 X (원하면 0으로 바꿔서 기본 선택 가능)
        key=item["q"],
    )
    st.write("")  # spacing

st.divider()

# -----------------------------
# Submit
# -----------------------------
col1, col2 = st.columns([1, 2])

with col1:
    submit = st.button("결과 보기", use_container_width=True)

with col2:
    st.caption("모든 질문에 답하면 더 정확한 결과를 받을 수 있어요.")

if submit:
    # 간단한 유효성 검사 (미선택 항목이 있으면 안내)
    unanswered = [q for q, a in answers.items() if a is None]
    if unanswered:
        st.warning("아직 답하지 않은 질문이 있어요! 모두 선택한 뒤 다시 눌러주세요 😊")
    else:
        st.info("분석 중...")  # 다음 시간에 API/분석 로직 연결 예정

