import streamlit as st
import requests
from collections import Counter

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

# ✅ 중요: 기존 코드는 “선택지 인덱스(0~3)”를 장르로 고정 매핑해서,
# 질문 내용/선택지 의미와 장르가 안 맞는 경우가 생겼어요.
# 아래는 “각 질문의 각 선택지”를 장르(4그룹)로 명확히 매핑해서 해결합니다.

QUESTIONS = [
    {
        "id": "q1",
        "q": "1. 주말에 가장 하고 싶은 것은?",
        "options": ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"],
        # 로맨스/드라마, 코미디, 액션/어드벤처, SF/판타지
        "map": {
            "집에서 휴식": "romance_drama",
            "친구와 놀기": "comedy",
            "새로운 곳 탐험": "action_adventure",
            "혼자 취미생활": "sf_fantasy",
        },
    },
    {
        "id": "q2",
        "q": "2. 스트레스 받으면?",
        "options": ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"],
        "map": {
            "혼자 있기": "romance_drama",
            "수다 떨기": "comedy",
            "운동하기": "action_adventure",
            "맛있는 거 먹기": "comedy",
        },
    },
    {
        "id": "q3",
        "q": "3. 영화에서 중요한 것은?",
        "options": ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"],
        "map": {
            "감동 스토리": "romance_drama",
            "시각적 영상미": "action_adventure",
            "깊은 메시지": "sf_fantasy",
            "웃는 재미": "comedy",
        },
    },
    {
        "id": "q4",
        "q": "4. 여행 스타일?",
        "options": ["계획적", "즉흥적", "액티비티", "힐링"],
        "map": {
            "계획적": "sf_fantasy",
            "즉흥적": "comedy",
            "액티비티": "action_adventure",
            "힐링": "romance_drama",
        },
    },
    {
        "id": "q5",
        "q": "5. 친구 사이에서 나는?",
        "options": ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"],
        "map": {
            "듣는 역할": "romance_drama",
            "주도하기": "action_adventure",
            "분위기 메이커": "comedy",
            "필요할 때 나타남": "sf_fantasy",
        },
    },
]

GROUP_LABEL = {
    "romance_drama": "로맨스/드라마",
    "action_adventure": "액션/어드벤처",
    "sf_fantasy": "SF/판타지",
    "comedy": "코미디",
}

answers = {}

for item in QUESTIONS:
    choice = st.radio(item["q"], item["options"], index=None, key=item["id"])
    answers[item["id"]] = choice
    st.write("")

st.divider()


def pick_final_genre(answers: dict) -> tuple[str, int, str, str]:
    """
    1) 4그룹(로맨스/드라마, 액션/어드벤처, SF/판타지, 코미디) 중 최다 득표 선택
    2) TMDB 장르로 변환:
       - 로맨스/드라마 → 로맨스 vs 드라마를 추가 힌트로 결정
       - SF/판타지 → SF vs 판타지를 추가 힌트로 결정
       - 나머지는 액션/코미디로 확정
    반환: (group_key, genre_name, genre_id, reason)
    """
    # 그룹 점수 계산
    group_counts = Counter()
    for q in QUESTIONS:
        a = answers.get(q["id"])
        group = q["map"].get(a)
        if group:
            group_counts[group] += 1

    # 최다 득표 그룹 (동점이면 우선순위로 안정적으로 처리)
    priority = ["romance_drama", "action_adventure", "sf_fantasy", "comedy"]
    top_group = max(priority, key=lambda g: (group_counts.get(g, 0), -priority.index(g)))

    # 세부 장르 결정 로직(간단하지만 일관되게)
    if top_group == "romance_drama":
        romance_hint = 0
        drama_hint = 0

        # 로맨스 쪽 힌트: 친구/수다/즉흥/관계 중심
        if answers["q1"] == "친구와 놀기":
            romance_hint += 1
        if answers["q2"] == "수다 떨기":
            romance_hint += 1
        if answers["q5"] == "주도하기":
            romance_hint += 1

        # 드라마 쪽 힌트: 감동/힐링/혼자/경청
        if answers["q3"] == "감동 스토리":
            drama_hint += 2
        if answers["q4"] == "힐링":
            drama_hint += 1
        if answers["q2"] == "혼자 있기":
            drama_hint += 1
        if answers["q5"] == "듣는 역할":
            drama_hint += 1

        genre_name = "로맨스" if romance_hint > drama_hint else "드라마"

    elif top_group == "sf_fantasy":
        # 판타지 힌트(모험/즉흥/상상) vs SF 힌트(계획/메시지)
        fantasy_hint = 0
        sf_hint = 0
        if answers["q1"] == "새로운 곳 탐험":
            fantasy_hint += 1
        if answers["q4"] == "즉흥적":
            fantasy_hint += 1
        if answers["q4"] == "계획적":
            sf_hint += 1
        if answers["q3"] == "깊은 메시지":
            sf_hint += 1

        genre_name = "판타지" if fantasy_hint > sf_hint else "SF"

    elif top_group == "action_adventure":
        genre_name = "액션"
    else:
        genre_name = "코미디"

    genre_id = GENRE_IDS[genre_name]

    # 추천 이유(그룹 기반 + 세부 장르 반영)
    base_reason_map = {
        "romance_drama": "감정선/여운/힐링 포인트를 중시하는 선택이 많았어요.",
        "action_adventure": "활동적이고 시원한 전개에서 스트레스를 푸는 선택이 많았어요.",
        "sf_fantasy": "상상력 자극, 메시지, 새로운 세계관 성향이 두드러졌어요.",
        "comedy": "가볍게 웃고 기분 전환하는 선택이 많았어요.",
    }
    detail_reason_map = {
        "드라마": "특히 ‘감동 스토리’와 ‘힐링’ 쪽 선택이 드라마 취향에 가까워요.",
        "로맨스": "특히 사람/관계 중심의 선택이 로맨스 취향에 가까워요.",
        "SF": "특히 ‘깊은 메시지’/‘계획적’ 성향이 SF 쪽과 잘 맞아요.",
        "판타지": "즉흥/탐험 성향이 판타지 감성과 잘 어울려요.",
        "액션": "액티비티/시각적 쾌감 선호가 액션과 잘 맞아요.",
        "코미디": "수다/웃는 재미 선호가 코미디와 찰떡이에요.",
    }

    reason = f"{base_reason_map.get(top_group,'')} {detail_reason_map.get(genre_name,'')}".strip()
    return top_group, genre_name, genre_id, reason


def fetch_movies(api_key: str, genre_id: int, limit: int = 5) -> list[dict]:
    params = {
        "api_key": api_key,
        "with_genres": genre_id,          # ✅ 여기 값이 '결과 장르'와 1:1로 연결됨
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "include_video": "false",
        "page": 1,
    }
    r = requests.get(DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    return (r.json().get("results", []) or [])[:limit]


def per_movie_reason(genre_name: str, user_reason: str, title: str) -> str:
    return f"{title}은(는) **{genre_name}** 장르에서 인기가 높은 작품이라, {user_reason}"


if st.button("결과 보기", use_container_width=True):
    if not tmdb_key:
        st.error("사이드바에 TMDB API Key를 먼저 입력해줘!")
        st.stop()

    if any(v is None for v in answers.values()):
        st.warning("5개 질문을 모두 선택해야 결과를 볼 수 있어요 🙂")
        st.stop()

    st.info("분석 중... 🔎 잠시만 기다려줘!")

    try:
        top_group, genre_name, genre_id, reason = pick_final_genre(answers)

        st.subheader(f"✅ 당신에게 어울리는 장르: {genre_name}")
        st.caption(f"({GROUP_LABEL[top_group]} 성향 기반)")
        st.write(f"**추천 이유:** {reason}")

        st.divider()
        st.markdown("### 🎥 추천 인기 영화 TOP 5 (TMDB)")

        movies = fetch_movies(tmdb_key, genre_id, limit=5)

        if not movies:
            st.warning("해당 장르에서 영화를 찾지 못했어요. 잠시 후 다시 시도해줘!")
            st.stop()

        for m in movies:
            title = m.get("title") or "제목 없음"
            rating = m.get("vote_average", 0.0)
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
                st.markdown(f"💡 **이 영화를 추천하는 이유:** {per_movie_reason(genre_name, reason, title)}")

            st.divider()

    except requests.HTTPError as e:
        st.error("TMDB 요청에 실패했어요. API Key/요청 제한/네트워크 상태를 확인해줘!")
        st.caption(f"에러: {e}")
    except Exception as e:
        st.error("문제가 발생했어요. 잠시 후 다시 시도해줘!")
        st.caption(f"에러: {e}")
