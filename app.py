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
        "id": "q1",
        "q": "1. 시험이 끝난 날, 너는 어떤 하루를 보내고 싶어?",
        "options": [
            "조용한 카페에서 감성적으로 하루를 정리한다",
            "친구들과 바로 여행이나 액티비티를 즐긴다",
            "집에서 새로운 세계관에 빠져든다",
            "가볍게 웃을 수 있는 콘텐츠 보면서 쉰다",
        ],
    },
    {
        "id": "q2",
        "q": "2. 친구가 갑자기 “오늘 영화 보자!”고 하면?",
        "options": [
            "여운 남는 이야기가 좋아",
            "박진감 넘치고 몰입감 강한 게 좋아",
            "상상력이 터지는 설정이면 좋아",
            "웃다가 끝나는 편한 분위기가 좋아",
        ],
    },
    {
        "id": "q3",
        "q": "3. 너의 연애 스타일은 영화로 치면?",
        "options": [
            "감정선이 중요하고 서사가 탄탄한 편",
            "적극적이고 이벤트가 많은 편",
            "특별한 운명 같은 느낌을 믿는 편",
            "티격태격해도 웃음이 많은 편",
        ],
    },
    {
        "id": "q4",
        "q": "4. 대학생활에서 가장 기대되는 순간은?",
        "options": [
            "사람들과 깊은 이야기 나누는 밤",
            "MT나 축제처럼 에너지 넘치는 날",
            "새로운 경험과 낯선 자극",
            "친구들이랑 아무 말이나 하며 웃는 시간",
        ],
    },
    {
        "id": "q5",
        "q": "5. 네가 주인공이라면 어떤 캐릭터일까?",
        "options": [
            "감정을 섬세하게 품고 성장하는 주인공",
            "위기 속에서도 돌파하는 주인공",
            "다른 세계를 탐험하는 주인공",
            "주변을 즐겁게 만드는 주인공",
        ],
    },
]

# -----------------------------
# Session state init
# -----------------------------
for item in questions:
    if item["id"] not in st.session_state:
        st.session_state[item["id"]] = None

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

# -----------------------------
# Reset handler
# -----------------------------
def reset_test():
    for item in questions:
        st.session_state[item["id"]] = None
    st.session_state["submitted"] = False

# -----------------------------
# Render questions
# -----------------------------
for item in questions:
    st.radio(
        item["q"],
        item["options"],
        index=None,  # 기본 선택 없음
        key=item["id"],  # session_state에 저장됨
    )
    st.write("")

st.divider()

# -----------------------------
# Buttons
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("결과 보기", use_container_width=True):
        st.session_state["submitted"] = True

with col2:
    st.button("다시 테스트하기", use_container_width=True, on_click=reset_test)

# -----------------------------
# Results area
# -----------------------------
if st.session_state["submitted"]:
    # 모든 답변 수집
    collected = []
    unanswered = []

    for item in questions:
        ans = st.session_state.get(item["id"])
        if ans is None:
            unanswered.append(item["q"])
        collected.append({"question": item["q"], "answer": ans})

    if unanswered:
        st.warning("아직 답하지 않은 질문이 있어요! 모두 선택한 뒤 다시 눌러주세요 😊")
    else:
        st.subheader("🧾 당신의 답변 모아보기")
        for row in collected:
            st.markdown(f"**{row['question']}**  \n- {row['answer']}")
        st.info("분석 중...")
