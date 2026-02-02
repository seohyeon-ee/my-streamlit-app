import streamlit as st
import requests
from collections import Counter

st.set_page_config(page_title="🎬 나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# -----------------------------
# TMDB 설정
# -----------------------------
st.sidebar.header("TMDB 설정")
api_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="여기에 API Key 입력")
st.sidebar.caption("키가 없으면 결과를 불러올 수 없어요.")

POSTER_BASE = "https://image.tmdb.org/t/p/w500"
DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"

GENRE_IDS = {
    "action": 28,
    "comedy": 35,
    "drama": 18,
    "scifi": 878,
    "romance": 10749,
    "fantasy": 14,
}

# -----------------------------
# Header
# -----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("5개의 질문에 답하면, 당신과 어울리는 영화 스타일을 추천해드려요! 🎞️✨")
st.caption("※ 결과는 TMDB 인기 영화 데이터를 기반으로 추천합니다.")

st.divider()

# -----------------------------
# 질문 (선택지에 장르 명시 X)
# 각 선택지는 내부적으로 4개 성향 중 하나로 매핑됨:
# - rd: 로맨스/드라마
# - aa: 액션/어드벤처
# - sf: SF/판타지
# - co: 코미디
# -----------------------------
questions = [
    {
        "id": "q1",
        "q": "1. 시험이 끝난 날, 너는 어떤 하루를 보내고 싶어?",
        "options": [
            ("조용한 카페에서 감성적으로 하루를 정리한다", "rd"),
            ("친구들과 바로 여행이나 액티비티를 즐긴다", "aa"),
            ("집에서 새로운 세계관에 빠져든다", "sf"),
            ("가볍게 웃을 수 있는 콘텐츠 보면서 쉰다", "co"),
        ],
    },
    {
        "id": "q2",
        "q": "2. 친구가 갑자기 “오늘 영화 보자!”고 하면?",
        "options": [
            ("여운 남는 이야기가 좋아", "rd"),
            ("박진감 넘치고 몰입감 강한 게 좋아", "aa"),
            ("상상력이 터지는 설정이면 좋아", "sf"),
            ("웃다가 끝나는 편한 분위기가 좋아", "co"),
        ],
    },
    {
        "id": "q3",
        "q": "3. 너의 연애 스타일은 영화로 치면?",
        "options": [
            ("감정선이 중요하고 서사가 탄탄한 편", "rd"),
            ("적극적이고 이벤트가 많은 편", "aa"),
            ("특별한 운명 같은 느낌을 믿는 편", "rd"),  # 연애 문항은 감성 성향 강화
            ("티격태격해도 웃음이 많은 편", "co"),
        ],
    },
    {
        "id": "q4",
        "q": "4. 대학생활에서 가장 기대되는 순간은?",
        "options": [
            ("사람들과 깊은 이야기 나누는 밤", "rd"),
            ("MT나 축제처럼 에너지 넘치는 날", "aa"),
            ("새로운 경험과 낯선 자극", "sf"),
            ("친구들이랑 아무 말이나 하며 웃는 시간", "co"),
        ],
    },
    {
        "id": "q5",
        "q": "5. 네가 주인공이라면 어떤 캐릭터일까?",
        "options": [
            ("감정을 섬세하게 품고 성장하는 주인공", "drama_hint"),
            ("위기 속에서도 돌파하는 주인공", "aa"),
            ("다른 세계를 탐험하는 주인공", "fantasy_hint"),
            ("주변을 즐겁게 만드는 주인공", "co"),
        ],
    },
]

# -----------------------------
# Session state init
# -----------------------------
for item in questions:
    if item["id"] not in st.session_state:
        st.session_state[item["id"]] = None  # 선택된 옵션(문자열) 저장

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

if "result_genre" not in st.session_state:
    st.session_state["result_genre"] = None

if "movies" not in st.session_state:
    st.session_state["movies"] = None

# -----------------------------
# Reset
# -----------------------------
def reset_test():
    for item in questions:
        st.session_state[item["id"]] = None
    st.session_state["submitted"] = False
    st.session_state["result_genre"] = None
    st.session_state["movies"] = None

# -----------------------------
# 유틸: 선택지 텍스트 -> 성향 코드
# -----------------------------
def option_to_trait(q_item, selected_text):
    for text, trait in q_item["options"]:
        if text == selected_text:
            return trait
    return None

def decide_genre(answers_by_qid):
    """
    1) 4개 성향(rd/aa/sf/co) 투표로 대표 성향 결정
    2) rd는 romance vs drama, sf는 scifi vs fantasy를 힌트로 세분화
    """
    traits = []
    hints = {"drama_hint": 0, "fantasy_hint": 0}

    for q_item in questions:
        sel = answers_by_qid.get(q_item["id"])
        if not sel:
            continue
        trait = option_to_trait(q_item, sel)
        if trait in ("rd", "aa", "sf", "co"):
            traits.append(trait)
        elif trait in hints:
            hints[trait] += 1
            # 힌트 문항도 큰 성향에 반영되도록 처리
            if trait == "drama_hint":
                traits.append("rd")
            elif trait == "fantasy_hint":
                traits.append("sf")

    if not traits:
        return "drama"

    counts = Counter(traits)
    top_trait, _ = counts.most_common(1)[0]

    # 동점 처리: 우선순위(사용자 경험 기준) rd > aa > sf > co
    top_count = counts[top_trait]
    tied = [t for t, c in counts.items() if c == top_count]
    if len(tied) > 1:
        for pref in ["rd", "aa", "sf", "co"]:
            if pref in tied:
                top_trait = pref
                break

    # 세분화 규칙
    if top_trait == "aa":
        return "action"
    if top_trait == "co":
        return "comedy"
    if top_trait == "rd":
        # q5가 성장/서사 힌트면 drama 쪽, 아니면 romance 쪽 살짝 우선
        if hints["drama_hint"] >= 1:
            return "drama"
        # q3가 "운명" 선택(=rd 두 번째)면 romance 쪽 가중
        q3 = answers_by_qid.get("q3") or ""
        if "운명" in q3:
            return "romance"
        return "romance"
    if top_trait == "sf":
        if hints["fantasy_hint"] >= 1:
            return "fantasy"
        # 설정/세계관 키워드가 강하면 scifi 쪽
        joined = " ".join([v for v in answers_by_qid.values() if v])
        if any(k in joined for k in ["설정", "자극", "미지", "세계관"]):
            return "scifi"
        return "scifi"

    return "drama"

def make_reason(genre_key, answers_by_qid):
    genre_name = {
        "action": "액션",
        "comedy": "코미디",
        "drama": "드라마",
        "scifi": "SF",
        "romance": "로맨스",
        "fantasy": "판타지",
    }.get(genre_key, "드라마")

    # 짧은 맞춤형 이유
    a1 = answers_by_qid.get("q1") or ""
    a2 = answers_by_qid.get("q2") or ""
    a5 = answers_by_qid.get("q5") or ""

    if genre_key == "action":
        return f"에너지 넘치고 몰입감 강한 전개를 선호하는 답변이 많았어요. 특히 “{a2}” 같은 선택이 액션 취향을 보여줘요."
    if genre_key == "comedy":
        return f"가볍게 웃으면서 스트레스 푸는 스타일이 강해요. “{a1}” 같은 답변이 편안한 분위기를 선호한다는 신호예요."
    if genre_key == "romance":
        return f"감정의 흐름과 관계의 설렘을 중요하게 보는 편이에요. “{a2}”에서 여운/감성 쪽을 선택한 점이 로맨스와 잘 맞아요."
    if genre_key == "drama":
        return f"인물의 성장이나 깊이 있는 이야기에 끌리는 타입이에요. “{a5}” 같은 선택이 드라마 취향과 잘 맞아요."
    if genre_key == "scifi":
        return f"상상력과 새로운 설정에 끌리는 편이에요. “{a2}”나 ‘세계관/설정’ 계열 선택이 SF 선호를 보여줘요."
    if genre_key == "fantasy":
        return f"현실을 잠깐 벗어나 다른 세계를 탐험하는 이야기에 잘 몰입해요. “{a5}” 같은 선택이 판타지 감성을 딱 찍었어요."
    return f"답변 패턴을 보면 {genre_name} 분위기의 영화가 가장 잘 맞아 보여요."

@st.cache_data(show_spinner=False, ttl=600)
def fetch_popular_movies_by_genre(api_key: str, genre_id: int, n: int = 5):
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "page": 1,
    }
    r = requests.get(DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])[:n]
    return results

# -----------------------------
# Render questions
# -----------------------------
for item in questions:
    option_texts = [t for t, _ in item["options"]]
    st.radio(
        item["q"],
        option_texts,
        index=None,
        key=item["id"],  # 선택 결과가 session_state에 저장됨
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
# Results
# -----------------------------
if st.session_state["submitted"]:
    answers_by_qid = {q["id"]: st.session_state.get(q["id"]) for q in questions}
    unanswered = [q for q in questions if not answers_by_qid.get(q["id"])]

    if unanswered:
        st.warning("아직 답하지 않은 질문이 있어요! 모든 질문에 답한 뒤 다시 눌러주세요 😊")
        st.stop()

    st.subheader("🧾 당신의 답변")
    for q in questions:
        st.markdown(f"**{q['q']}**  \n- {answers_by_qid[q['id']]}")

    st.divider()

    if not api_key:
        st.error("사이드바에 TMDB API Key를 입력해 주세요.")
        st.stop()

    # 1) 사용자 답변 분석 -> 장르 결정
    genre_key = decide_genre(answers_by_qid)
    genre_id = GENRE_IDS[genre_key]

    genre_label = {
        "action": "액션",
        "comedy": "코미디",
        "drama": "드라마",
        "scifi": "SF",
        "romance": "로맨스",
        "fantasy": "판타지",
    }[genre_key]

    st.subheader(f"✅ 추천 장르: {genre_label}")
    st.caption(make_reason(genre_key, answers_by_qid))

    # 2) TMDB로 인기 영화 5개 가져오기
    with st.spinner("분석 중..."):
        try:
            movies = fetch_popular_movies_by_genre(api_key, genre_id, n=5)
        except requests.HTTPError as e:
            st.error("TMDB API 요청에 실패했어요. API Key가 올바른지 확인해 주세요.")
            st.exception(e)
            st.stop()
        except requests.RequestException as e:
            st.error("네트워크 오류로 TMDB에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.")
            st.exception(e)
            st.stop()

    if not movies:
        st.info("해당 장르에서 영화를 찾지 못했어요. 다른 답변으로 다시 시도해볼까요?")
        st.stop()

    st.divider()
    st.subheader("🎥 인기 영화 TOP 5")

    # 3) 영화 카드 렌더
    for m in movies:
        title = m.get("title") or m.get("name") or "제목 없음"
        vote = m.get("vote_average")
        overview = m.get("overview") or "줄거리 정보가 없어요."
        poster_path = m.get("poster_path")
        poster_url = f"{POSTER_BASE}{poster_path}" if poster_path else None

        reason = f"당신의 선택이 **{genre_label}** 성향과 잘 맞아서, 이 장르에서 인기가 높은 작품을 골랐어요."

        card = st.container(border=True)
        with card:
            left, right = st.columns([1, 2], gap="large")
            with left:
                if poster_url:
                    st.image(poster_url, use_container_width=True)
                else:
                    st.caption("포스터 없음")
            with right:
                st.markdown(f"### {title}")
                if vote is not None:
                    st.write(f"⭐ 평점: {vote:.1f}")
                else:
                    st.write("⭐ 평점: 정보 없음")

                st.write(overview)
                st.markdown("**이 영화를 추천하는 이유**")
                st.write(reason)
