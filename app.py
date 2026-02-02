import streamlit as st
import requests

st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# ----------------------------
# TMDB 설정
# ----------------------------
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"

GENRE_IDS = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}

# ----------------------------
# 사이드바: API 키 입력
# ----------------------------
st.sidebar.header("🔑 TMDB 설정")
tmdb_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="여기에 API Key 입력")

# ----------------------------
# 앱 UI
# ----------------------------
st.title("🎬 나와 어울리는 영화는?")
st.write("간단한 5문항으로 당신의 성향을 분석하고, TMDB에서 딱 맞는 인기 영화를 추천해드려요! 🍿")

st.divider()

questions = [
    {
        "id": "q1",
        "q": "1. 주말에 가장 하고 싶은 것은?",
        "options": ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"],
    },
    {
        "id": "q2",
        "q": "2. 스트레스 받으면?",
        "options": ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"],
    },
    {
        "id": "q3",
        "q": "3. 영화에서 중요한 것은?",
        "options": ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"],
    },
    {
        "id": "q4",
        "q": "4. 여행 스타일?",
        "options": ["계획적", "즉흥적", "액티비티", "힐링"],
    },
    {
        "id": "q5",
        "q": "5. 친구 사이에서 나는?",
        "options": ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"],
    },
]

# 각 문항의 4지선다를 (로맨스/드라마, 액션/어드벤처, SF/판타지, 코미디)로 매핑
# 0: 로맨스/드라마, 1: 액션/어드벤처, 2: SF/판타지, 3: 코미디
INDEX_TO_GROUP = {
    0: "romance_drama",
    1: "action_adventure",
    2: "sf_fantasy",
    3: "comedy",
}

GROUP_LABEL = {
    "romance_drama": "로맨스/드라마",
    "action_adventure": "액션/어드벤처",
    "sf_fantasy": "SF/판타지",
    "comedy": "코미디",
}

answers = {}
answer_indexes = {}

for item in questions:
    choice = st.radio(
        item["q"],
        item["options"],
        index=None,  # 선택 전 상태
        key=item["id"],
    )
    answers[item["id"]] = choice
    answer_indexes[item["id"]] = None if choice is None else item["options"].index(choice)
    st.write("")

st.divider()

def analyze_genre(answer_indexes: dict) -> tuple[str, int, str]:
    """
    사용자 응답을 4개 그룹 점수로 분석 후,
    TMDB 장르(genre_name, genre_id)와 추천이유(reason)를 반환.
    """
    scores = {
        "romance_drama": 0,
        "action_adventure": 0,
        "sf_fantasy": 0,
        "comedy": 0,
    }

    # 5문항 * 1선택 → 선택지 인덱스를 그룹으로 점수화
    for qid, idx in answer_indexes.items():
        if idx is None:
            continue
        group = INDEX_TO_GROUP.get(idx)
        if group:
            scores[group] += 1

    # 1) 최다 점수 그룹 선택 (동점이면 우선순위로 처리)
    priority = ["romance_drama", "action_adventure", "sf_fantasy", "comedy"]
    top_group = max(priority, key=lambda g: (scores[g], -priority.index(g)))

    # 2) 세부 장르(드라마/로맨스, SF/판타지 등) 선택 룰 (가볍게)
    if top_group == "romance_drama":
        # 감동 스토리/힐링/듣는 역할 쪽이면 드라마, 수다/주도하기/친구와 놀기 쪽이면 로맨스 약간 가산
        romance_hint = 0
        drama_hint = 0

        # q2: 수다 떨기
        if answer_indexes.get("q2") == 1:
            romance_hint += 1
        # q3: 감동 스토리
        if answer_indexes.get("q3") == 0:
            drama_hint += 2
        # q4: 힐링
        if answer_indexes.get("q4") == 3:
            drama_hint += 1
        # q5: 주도하기
        if answer_indexes.get("q5") == 1:
            romance_hint += 1

        if romance_hint > drama_hint:
            genre_name = "로맨스"
        else:
            genre_name = "드라마"

    elif top_group == "sf_fantasy":
        # q1 탐험/ q4 즉흥이면 판타지 쪽, 아니면 SF 쪽
        fantasy_hint = 0
        if answer_indexes.get("q1") == 2:  # 새로운 곳 탐험
            fantasy_hint += 1
        if answer_indexes.get("q4") == 1:  # 즉흥적
            fantasy_hint += 1

        genre_name = "판타지" if fantasy_hint >= 2 else "SF"

    elif top_group == "action_adventure":
        genre_name = "액션"
    else:
        genre_name = "코미디"

    genre_id = GENRE_IDS[genre_name]

    # 3) 추천 이유(짧게)
    reason_map = {
        "드라마": "감정선과 몰입감 있는 이야기로 ‘여운’이 오래 가는 영화를 좋아하는 편이라서요.",
        "로맨스": "관계와 대화, 설렘 포인트가 있는 이야기에서 에너지를 얻는 스타일이라서요.",
        "액션": "스트레스는 시원한 전개와 강한 타격감으로 푸는 타입이라서요.",
        "SF": "새로운 설정과 상상력을 자극하는 세계관에서 재미를 느끼는 편이라서요.",
        "판타지": "현실을 잠깐 잊게 해주는 ‘다른 세계’ 감성에 끌리는 성향이라서요.",
        "코미디": "가볍게 웃고 기분 전환 되는 영화를 선호하는 편이라서요.",
    }
    reason = reason_map.get(genre_name, "당신의 선택이 이 장르와 가장 잘 맞았어요!")

    return genre_name, genre_id, reason


def fetch_movies(api_key: str, genre_id: int, limit: int = 5) -> list[dict]:
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "include_video": "false",
        "page": 1,
    }
    r = requests.get(DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])[:limit]
    return results


def movie_reason_for_user(genre_name: str, base_reason: str, title: str) -> str:
    # 영화별로 너무 길지 않게: 장르 + 개인성향 한 문장
    return f"**{title}**은(는) {genre_name} 감성을 잘 살린 인기 작품이라, {base_reason}"


if st.button("결과 보기", use_container_width=True):
    # 0) 필수 체크
    if not tmdb_key:
        st.error("사이드바에 TMDB API Key를 먼저 입력해줘!")
        st.stop()

    if any(v is None for v in answers.values()):
        st.warning("5개 질문을 모두 선택해야 결과를 볼 수 있어요 🙂")
        st.stop()

    # 1) 분석
    st.info("분석 중... 🔎 잠시만 기다려줘!")

    try:
        genre_name, genre_id, base_reason = analyze_genre(answer_indexes)

        st.subheader(f"✅ 당신에게 어울리는 장르: {genre_name}")
        st.write(f"**추천 이유:** {base_reason}")

        st.divider()
        st.markdown("### 🎥 추천 인기 영화 TOP 5 (TMDB)")

        movies = fetch_movies(tmdb_key, genre_id, limit=5)

        if not movies:
            st.warning("해당 장르에서 영화를 찾지 못했어요. 잠시 후 다시 시도해줘!")
            st.stop()

        for m in movies:
            title = m.get("title") or m.get("name") or "제목 없음"
            rating = m.get("vote_average", 0)
            overview = m.get("overview") or "줄거리 정보가 없어요."
            poster_path = m.get("poster_path")

            col1, col2 = st.columns([1, 2], gap="large")
            with col1:
                if poster_path:
                    st.image(f"{POSTER_BASE}{poster_path}", use_container_width=True)
                else:
                    st.caption("포스터 없음")

            with col2:
                st.markdown(f"#### {title}")
                st.caption(f"⭐ 평점: {rating:.1f}/10")
                st.write(overview)
                st.markdown(
                    f"💡 **이 영화를 추천하는 이유:** {movie_reason_for_user(genre_name, base_reason, title)}"
                )

            st.divider()

    except requests.HTTPError as e:
        st.error("TMDB 요청에 실패했어요. API Key가 맞는지 확인해줘!")
        st.caption(f"에러: {e}")
    except Exception as e:
        st.error("문제가 발생했어요. 잠시 후 다시 시도해줘!")
        st.caption(f"에러: {e}")
