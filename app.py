import streamlit as st
import requests
from collections import Counter

st.set_page_config(page_title="🎬 나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# -----------------------------
# TMDB 설정
# -----------------------------
st.sidebar.header("TMDB 설정")
api_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="여기에 API Key 입력")

min_rating = st.sidebar.slider(
    "최소 평점(10점 만점)",
    min_value=0.0,
    max_value=10.0,
    value=6.5,
    step=0.5,
)

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

GENRE_LABEL = {
    "action": "액션",
    "comedy": "코미디",
    "drama": "드라마",
    "scifi": "SF",
    "romance": "로맨스",
    "fantasy": "판타지",
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
            ("특별한 운명 같은 느낌을 믿는 편", "rd"),
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
        st.session_state[item["id"]] = None

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

# -----------------------------
# Reset
# -----------------------------
def reset_test():
    for item in questions:
        st.session_state[item["id"]] = None
    st.session_state["submitted"] = False

# -----------------------------
# 유틸
# -----------------------------
def option_to_trait(q_item, selected_text):
    for text, trait in q_item["options"]:
        if text == selected_text:
            return trait
    return None

def decide_genre(answers_by_qid):
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
            if trait == "drama_hint":
                traits.append("rd")
            elif trait == "fantasy_hint":
                traits.append("sf")

    if not traits:
        return "drama"

    counts = Counter(traits)
    top_trait, _ = counts.most_common(1)[0]

    # 동점 처리: rd > aa > sf > co
    top_count = counts[top_trait]
    tied = [t for t, c in counts.items() if c == top_count]
    if len(tied) > 1:
        for pref in ["rd", "aa", "sf", "co"]:
            if pref in tied:
                top_trait = pref
                break

    if top_trait == "aa":
        return "action"
    if top_trait == "co":
        return "comedy"
    if top_trait == "rd":
        if hints["drama_hint"] >= 1:
            return "drama"
        q3 = answers_by_qid.get("q3") or ""
        if "운명" in q3:
            return "romance"
        return "romance"
    if top_trait == "sf":
        if hints["fantasy_hint"] >= 1:
            return "fantasy"
        return "scifi"

    return "drama"

@st.cache_data(show_spinner=False, ttl=600)
def fetch_movies_by_genre_with_min_rating(api_key: str, genre_id: int, min_rating: float, n: int = 5):
    """
    TMDB discover에서 인기순으로 가져오되,
    사용자가 설정한 최소 평점 이상만 필터링해서 n개를 채움.
    (페이지를 넘기며 최대 몇 페이지까지 탐색)
    """
    collected = []
    page = 1
    max_pages = 5  # 너무 많이 돌지 않게 제한

    while len(collected) < n and page <= max_pages:
        params = {
            "api_key": api_key,
            "with_genres": genre_id,
            "language": "ko-KR",
            "sort_by": "popularity.desc",
            "page": page,
            "vote_average.gte": min_rating,  # TMDB 필터
        }
        r = requests.get(DISCOVER_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])

        # 혹시 API 필터가 느슨할 경우를 대비해 한 번 더 로컬 필터
        results = [m for m in results if (m.get("vote_average") or 0) >= min_rating]

        collected.extend(results)
        page += 1

        if not results and page == 2:
            # 첫 페이지부터 비었다면 더 탐색해도 의미 없을 가능성이 큼
            break

    return collected[:n]

def short_overview(text: str, max_len: int = 120) -> str:
    text = (text or "").strip()
    if not text:
        return "줄거리 정보가 없어요."
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"

# -----------------------------
# Render questions
# -----------------------------
for item in questions:
    option_texts = [t for t, _ in item["options"]]
    st.radio(
        item["q"],
        option_texts,
        index=None,
        key=item["id"],
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

    if not api_key:
        st.error("사이드바에 TMDB API Key를 입력해 주세요.")
        st.stop()

    # 1) 장르 결정
    genre_key = decide_genre(answers_by_qid)
    genre_id = GENRE_IDS[genre_key]
    genre_label = GENRE_LABEL[genre_key]

    # 2) TMDB 호출 (spinner)
    with st.spinner("분석 중..."):
        try:
            movies = fetch_movies_by_genre_with_min_rating(
                api_key=api_key,
                genre_id=genre_id,
                min_rating=min_rating,
                n=5,
            )
        except requests.HTTPError as e:
            st.error("TMDB API 요청에 실패했어요. API Key가 올바른지 확인해 주세요.")
            st.exception(e)
            st.stop()
        except requests.RequestException as e:
            st.error("네트워크 오류로 TMDB에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.")
            st.exception(e)
            st.stop()

    if not movies:
        st.info(f"최소 평점 {min_rating:.1f} 이상인 영화가 부족해요. 최소 평점을 낮춰서 다시 시도해볼까요?")
        st.stop()

    # 3) 결과 제목
    st.subheader(f"🎉 당신에게 딱인 장르는: {genre_label}!")
    st.caption(f"최소 평점 **{min_rating:.1f}** 이상인 인기 영화만 골랐어요. (TMDB 기준)")
    st.write("")

    # 4) 영화 카드 3열 표시
    cols = st.columns(3)
    for i, m in enumerate(movies):
        title = m.get("title") or m.get("name") or "제목 없음"
        vote = m.get("vote_average")
        overview = m.get("overview") or ""
        poster_path = m.get("poster_path")
        poster_url = f"{POSTER_BASE}{poster_path}" if poster_path else None

        col = cols[i % 3]
        with col:
            with st.container(border=True):
                if poster_url:
                    st.image(poster_url, use_container_width=True)
                else:
                    st.caption("포스터 없음")

                st.markdown(f"**{title}**")
                st.caption(f"⭐ 평점: {vote:.1f}" if vote is not None else "⭐ 평점: 정보 없음")

                with st.expander("상세 보기"):
                    st.write(short_overview(overview, max_len=700))
                    st.markdown("**이 영화를 추천하는 이유**")
                    st.write(
                        f"당신의 답변 결과가 **{genre_label}** 분위기와 잘 맞고, "
                        f"평점이 **{min_rating:.1f}** 이상인 작품이라 추천해요."
                    )
