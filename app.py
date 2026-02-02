import streamlit as st
import requests
from collections import Counter
from datetime import date

st.set_page_config(page_title="🎬 나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# -----------------------------
# TMDB 설정 + 필터(사이드바)
# -----------------------------
st.sidebar.header("TMDB 설정")
api_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="여기에 API Key 입력")

st.sidebar.divider()
st.sidebar.subheader("추천 필터")

min_rating = st.sidebar.slider(
    "최소 평점(10점 만점)",
    min_value=0.0,
    max_value=10.0,
    value=6.5,
    step=0.5,
)

release_range = st.sidebar.date_input(
    "개봉일 범위",
    value=(date(2000, 1, 1), date.today()),
)
if isinstance(release_range, tuple) and len(release_range) == 2:
    release_start, release_end = release_range
else:
    release_start, release_end = date(2000, 1, 1), date.today()

runtime_min, runtime_max = st.sidebar.slider(
    "러닝타임(분)",
    min_value=0,
    max_value=240,
    value=(80, 140),
    step=5,
)

continent_options = ["전체", "아시아", "유럽", "북미", "남미", "아프리카", "오세아니아"]
selected_continents = st.sidebar.multiselect(
    "제작 국가(대륙)",
    options=continent_options,
    default=["전체"],
    help="대륙을 선택하면 해당 대륙 국가에서 제작된 영화만 추천해요.",
)

include_unknown_runtime = st.sidebar.checkbox(
    "러닝타임 정보가 없는 영화도 포함",
    value=False,
)

st.sidebar.caption("※ TMDB 데이터 특성상 일부 영화는 러닝타임/제작국가 정보가 비어 있을 수 있어요.")

# -----------------------------
# TMDB 엔드포인트/상수
# -----------------------------
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
MOVIE_DETAIL_URL = "https://api.themoviedb.org/3/movie/{movie_id}"

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

CONTINENT_TO_COUNTRIES = {
    "아시아": [
        "KR", "JP", "CN", "HK", "TW", "TH", "VN", "PH", "ID", "MY", "SG",
        "IN", "PK", "BD", "LK", "NP", "MM", "KH", "LA", "MN", "KZ", "UZ",
        "IR", "IQ", "IL", "SA", "AE", "TR", "QA", "KW", "JO", "LB",
    ],
    "유럽": [
        "GB", "IE", "FR", "DE", "IT", "ES", "PT", "NL", "BE", "CH", "AT",
        "SE", "NO", "DK", "FI", "IS", "PL", "CZ", "SK", "HU", "RO", "BG",
        "GR", "UA", "RU",
    ],
    "북미": ["US", "CA", "MX"],
    "남미": ["BR", "AR", "CL", "CO", "PE", "VE", "UY", "PY", "EC", "BO"],
    "아프리카": ["ZA", "NG", "EG", "KE", "MA", "TN", "DZ", "GH", "ET", "UG"],
    "오세아니아": ["AU", "NZ", "FJ", "PG"],
}

# -----------------------------
# UI CSS (결과 하이라이트 + 카드)
# -----------------------------
st.markdown(
    """
    <style>
      .result-banner{
        padding: 16px 18px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.18);
        background: linear-gradient(135deg, rgba(255,215,0,0.18), rgba(0,191,255,0.12));
        box-shadow: 0 10px 24px rgba(0,0,0,0.08);
        margin: 14px 0 6px 0;
      }
      .result-banner .title{
        font-size: 1.35rem;
        font-weight: 800;
        margin: 0 0 6px 0;
      }
      .result-banner .meta{
        font-size: 0.95rem;
        opacity: 0.9;
        margin: 0;
      }
      .movie-title{
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 3.0em;
      }
      .step-card h3{
        margin: 0 0 6px 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# 질문(선택지에 장르 명시 X)
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

TOTAL_STEPS = len(questions)

# -----------------------------
# Session state init
# -----------------------------
for item in questions:
    if item["id"] not in st.session_state:
        st.session_state[item["id"]] = None

if "step" not in st.session_state:
    st.session_state["step"] = 0  # 0-based index

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

def reset_test():
    for item in questions:
        st.session_state[item["id"]] = None
    st.session_state["step"] = 0
    st.session_state["submitted"] = False

# -----------------------------
# 유틸
# -----------------------------
def selected_country_codes_from_continents(conts):
    if not conts or "전체" in conts:
        return set()
    codes = set()
    for c in conts:
        codes.update(CONTINENT_TO_COUNTRIES.get(c, []))
    return codes

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
            traits.append("rd" if trait == "drama_hint" else "sf")

    if not traits:
        return "drama"

    counts = Counter(traits)
    top_trait, _ = counts.most_common(1)[0]

    # 동점: rd > aa > sf > co
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
        return "romance" if "운명" in q3 else "romance"
    if top_trait == "sf":
        return "fantasy" if hints["fantasy_hint"] >= 1 else "scifi"
    return "drama"

def short_overview(text: str, max_len: int = 120) -> str:
    text = (text or "").strip()
    if not text:
        return "줄거리 정보가 없어요."
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"

def build_reason(min_rating: float, release_start: str, release_end: str, runtime_min: int, runtime_max: int, conts):
    parts = [
        f"평점 **{min_rating:.1f}** 이상",
        f"개봉일 **{release_start} ~ {release_end}**",
        f"러닝타임 **{runtime_min}~{runtime_max}분**",
    ]
    if conts and "전체" not in conts:
        parts.append(f"제작국가(대륙) **{', '.join(conts)}**")
    return " · ".join(parts)

# -----------------------------
# TMDB 호출(캐시)
# -----------------------------
@st.cache_data(show_spinner=False, ttl=600)
def fetch_discover_page(api_key: str, genre_id: int, page: int, release_start: str, release_end: str):
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "page": page,
        "primary_release_date.gte": release_start,
        "primary_release_date.lte": release_end,
    }
    r = requests.get(DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False, ttl=600)
def fetch_movie_detail(api_key: str, movie_id: int):
    url = MOVIE_DETAIL_URL.format(movie_id=movie_id)
    params = {"api_key": api_key, "language": "ko-KR"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def continent_match(detail: dict, allowed_country_codes: set) -> bool:
    if not allowed_country_codes:
        return True
    pcs = detail.get("production_countries") or []
    codes = {c.get("iso_3166_1") for c in pcs if c.get("iso_3166_1")}
    return len(codes.intersection(allowed_country_codes)) > 0

def runtime_match(detail: dict, rt_min: int, rt_max: int, include_unknown: bool) -> bool:
    rt = detail.get("runtime")
    if rt is None:
        return include_unknown
    return rt_min <= int(rt) <= rt_max

def rating_match(movie: dict, min_rating: float) -> bool:
    return (movie.get("vote_average") or 0.0) >= float(min_rating)

def fetch_movies_with_filters(
    api_key: str,
    genre_id: int,
    min_rating: float,
    release_start: date,
    release_end: date,
    runtime_min: int,
    runtime_max: int,
    allowed_country_codes: set,
    include_unknown_runtime: bool,
    n: int = 5,
):
    collected = []
    seen_ids = set()

    max_pages = 6
    max_candidates_to_check = 80
    checked = 0

    for page in range(1, max_pages + 1):
        data = fetch_discover_page(
            api_key=api_key,
            genre_id=genre_id,
            page=page,
            release_start=release_start.isoformat(),
            release_end=release_end.isoformat(),
        )
        results = data.get("results", [])
        if not results:
            break

        for m in results:
            if len(collected) >= n:
                return collected
            mid = m.get("id")
            if not mid or mid in seen_ids:
                continue
            seen_ids.add(mid)

            if not rating_match(m, min_rating):
                continue

            if checked >= max_candidates_to_check:
                return collected
            checked += 1

            detail = fetch_movie_detail(api_key, int(mid))

            if not runtime_match(detail, runtime_min, runtime_max, include_unknown_runtime):
                continue
            if not continent_match(detail, allowed_country_codes):
                continue

            merged = dict(m)
            merged["_detail"] = detail
            collected.append(merged)

    return collected

# -----------------------------
# Header
# -----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("질문을 **한 단계씩** 풀어가면, 당신에게 어울리는 영화 스타일을 추천해드려요! 🎞️✨")
st.caption("※ 결과는 TMDB 인기 영화 데이터를 기반으로 추천합니다.")
st.divider()

# -----------------------------
# 단계형 UI + 진행바
# -----------------------------
if not st.session_state["submitted"]:
    step = st.session_state["step"]
    current = questions[step]

    # 진행바 (0~1)
    st.progress((step + 1) / TOTAL_STEPS, text=f"진행도: {step + 1} / {TOTAL_STEPS}")

    with st.container(border=True):
        st.markdown(
            f"<div class='step-card'><h3>📝 {current['q']}</h3>"
            f"<p style='opacity:0.85;margin:0;'>아래에서 하나를 선택해 주세요.</p></div>",
            unsafe_allow_html=True,
        )
        option_texts = [t for t, _ in current["options"]]
        st.radio(
            label="",
            options=option_texts,
            index=None,
            key=current["id"],
            label_visibility="collapsed",
        )

    st.write("")
    c1, c2, c3 = st.columns([1, 1, 1])

    # 이전
    with c1:
        prev_disabled = step == 0
        if st.button("⬅️ 이전", use_container_width=True, disabled=prev_disabled):
            st.session_state["step"] = max(0, step - 1)
            st.rerun()

    # 다시하기
    with c2:
        st.button("🔄 다시 테스트하기", use_container_width=True, on_click=reset_test)

    # 다음 / 결과보기
    with c3:
        selected = st.session_state.get(current["id"])
        if step < TOTAL_STEPS - 1:
            if st.button("다음 ➡️", use_container_width=True, disabled=(selected is None)):
                st.session_state["step"] = min(TOTAL_STEPS - 1, step + 1)
                st.rerun()
        else:
            # 마지막 단계
            if st.button("🎯 결과 보기", use_container_width=True, disabled=(selected is None)):
                # 마지막 문항도 선택되었는지 최종 확인
                answers_by_qid = {q["id"]: st.session_state.get(q["id"]) for q in questions}
                unanswered = [q for q in questions if not answers_by_qid.get(q["id"])]
                if unanswered:
                    st.warning("아직 답하지 않은 질문이 있어요. 이전으로 돌아가서 선택해 주세요 😊")
                else:
                    st.session_state["submitted"] = True
                    st.rerun()

# -----------------------------
# 결과 화면
# -----------------------------
if st.session_state["submitted"]:
    if st.button("🔄 다시 테스트하기", use_container_width=True, on_click=reset_test):
        st.stop()

    answers_by_qid = {q["id"]: st.session_state.get(q["id"]) for q in questions}

    if not api_key:
        st.error("사이드바에 TMDB API Key를 입력해 주세요.")
        st.stop()

    allowed_country_codes = selected_country_codes_from_continents(selected_continents)

    genre_key = decide_genre(answers_by_qid)
    genre_id = GENRE_IDS[genre_key]
    genre_label = GENRE_LABEL[genre_key]

    with st.spinner("분석 중..."):
        try:
            movies = fetch_movies_with_filters(
                api_key=api_key,
                genre_id=genre_id,
                min_rating=min_rating,
                release_start=release_start,
                release_end=release_end,
                runtime_min=runtime_min,
                runtime_max=runtime_max,
                allowed_country_codes=allowed_country_codes,
                include_unknown_runtime=include_unknown_runtime,
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
        st.info(
            "조건에 맞는 영화가 부족해요. "
            "✅ 최소 평점을 낮추거나 / ✅ 개봉일 범위를 넓히거나 / ✅ 러닝타임 범위를 조정하거나 / ✅ 대륙 필터를 ‘전체’로 바꿔보세요."
        )
        st.stop()

    st.markdown(
        f"""
        <div class="result-banner">
          <div class="title">🔥 당신에게 딱인 장르는: {genre_label}!</div>
          <p class="meta">{build_reason(min_rating, release_start.isoformat(), release_end.isoformat(), runtime_min, runtime_max, selected_continents)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("추천 장르", genre_label)
    m2.metric("최소 평점", f"{min_rating:.1f}")
    m3.metric("추천 개수", f"{len(movies)}편")

    st.write("")
    st.subheader("🎥 추천 영화 TOP 5")

    cols = st.columns(3, gap="large")
    for i, m in enumerate(movies):
        title = m.get("title") or m.get("name") or "제목 없음"
        vote = m.get("vote_average")
        poster_path = m.get("poster_path")
        poster_url = f"{POSTER_BASE}{poster_path}" if poster_path else None

        detail = m.get("_detail") or {}
        overview = detail.get("overview") or m.get("overview") or ""
        runtime = detail.get("runtime")
        pcs = detail.get("production_countries") or []
        country_names = [c.get("name") for c in pcs if c.get("name")]
        release_date = detail.get("release_date") or m.get("release_date")

        reason = (
            f"**{genre_label}** 취향과 잘 맞고, "
            f"평점이 **{min_rating:.1f}** 이상이며, "
            f"설정한 개봉일/러닝타임/제작국가 필터를 만족해요."
        )

        col = cols[i % 3]
        with col:
            with st.container(border=True):
                if poster_url:
                    st.image(poster_url, use_container_width=True)
                else:
                    st.caption("포스터 없음")

                st.markdown(f"<div class='movie-title'><b>{title}</b></div>", unsafe_allow_html=True)
                st.caption(f"⭐ 평점: {vote:.1f}" if vote is not None else "⭐ 평점: 정보 없음")

                with st.expander("상세 보기"):
                    if release_date:
                        st.write(f"📅 개봉일: {release_date}")
                    if runtime is not None:
                        st.write(f"⏱️ 러닝타임: {runtime}분")
                    else:
                        st.write("⏱️ 러닝타임: 정보 없음")

                    if country_names:
                        st.write("🌍 제작 국가: " + ", ".join(country_names))
                    else:
                        st.write("🌍 제작 국가: 정보 없음")

                    st.write(short_overview(overview, max_len=700))
                    st.markdown("**이 영화를 추천하는 이유**")
                    st.write(reason)
