from __future__ import annotations

from datetime import datetime, time, timezone
from html import escape

import streamlit as st

from src.auth import logged_in_profile, login_screen, logout_button
from src.constants import (
    ASSIGNMENT_STATUSES,
    MAX_DESCRIPTION_LENGTH,
    MAX_FEEDBACK_LENGTH,
    MAX_FEEDBACK_NICKNAME_LENGTH,
    MAX_NICKNAME_LENGTH,
)
from src.database import (
    add_feedback,
    create_app,
    create_assignment,
    delete_app,
    liked_app_ids,
    list_apps,
    list_assignments,
    list_feedback_by_app,
    toggle_like,
    update_assignment,
)
from src.styles import inject_styles
from src.validation import contains_banned_word, https_url


st.set_page_config(page_title="정보 수업 작품 게시판", page_icon="🐥", layout="wide")
inject_styles()

GALLERY_REFRESH_SECONDS = 15
WORK_SORT_OPTIONS = {
    "최신 게시물순": ("created_at", True),
    "좋아요 많은 순": ("likes", True),
    "작성자 이름순": ("nickname", False),
}


def can_submit(assignment: dict) -> bool:
    if assignment["status"] != "open":
        return False
    due_at = assignment.get("due_at")
    if not due_at:
        return True
    return datetime.fromisoformat(due_at.replace("Z", "+00:00")) > datetime.now(timezone.utc)


def assignment_label(assignment: dict) -> str:
    due_at = assignment.get("due_at")
    suffix = f" · 마감 {due_at[:10]}" if due_at else ""
    return f"{assignment['title']}{suffix}"


def render_work_card(work: dict, liked: set[str], profile: dict, feedbacks: list[dict]) -> None:
    assignment = work.get("assignments") or {}
    with st.container(border=True):
        st.markdown(f"<span class='badge'>{escape(assignment.get('title', '과제'))}</span>", unsafe_allow_html=True)
        st.markdown(f"#### {escape(work['nickname'])}")
        st.caption(work["description"])
        left, right = st.columns(2)
        left.link_button("작품 열기", work["url"], use_container_width=True)
        liked_by_me = work["id"] in liked
        like_label = f"♥ {work['likes']}" + (" · 취소" if liked_by_me else "")
        if right.button(like_label, key=f"like-{work['id']}", type="primary" if liked_by_me else "secondary", use_container_width=True):
            try:
                toggle_like(work["id"], profile["id"])
            except Exception:
                st.error("좋아요 설정을 불러오지 못했습니다. Supabase SQL Editor에서 `sql/migrations/002_toggle_like.sql`을 실행한 뒤 다시 시도해 주세요.")
                return
            # This function is rendered inside the gallery fragment. Refreshing
            # only that fragment avoids reloading the auth, submit, and teacher
            # screens after every like.
            st.rerun(scope="fragment")

        if profile["role"] == "teacher":
            with st.expander("교사 관리"):
                confirmed = st.checkbox("이 게시물을 삭제합니다.", key=f"delete-confirm-{work['id']}")
                if st.button("게시물 삭제", key=f"delete-{work['id']}", disabled=not confirmed, type="primary"):
                    delete_app(work["id"])
                    st.session_state["flash_message"] = ("success", "게시물을 삭제했습니다.")
                    st.rerun()

        feedback_state_key = "open_feedback_app_id"
        feedback_is_open = st.session_state.get(feedback_state_key) == work["id"]
        feedback_button_label = f"피드백 {len(feedbacks)}개" + (" 닫기" if feedback_is_open else " 보기")
        if st.button(feedback_button_label, key=f"feedback-toggle-{work['id']}", use_container_width=True):
            st.session_state[feedback_state_key] = None if feedback_is_open else work["id"]
            st.rerun(scope="fragment")

        if feedback_is_open:
            if feedbacks:
                for feedback in feedbacks:
                    st.write(f"**{feedback['nickname']}**  {feedback['content']}")
            else:
                st.caption("첫 피드백을 남겨 보세요.")
            with st.form(f"feedback-{work['id']}", clear_on_submit=True):
                nickname = st.text_input("닉네임", value=profile["display_name"], max_chars=MAX_FEEDBACK_NICKNAME_LENGTH)
                content = st.text_input("피드백", max_chars=MAX_FEEDBACK_LENGTH)
                if st.form_submit_button("피드백 등록"):
                    if not nickname.strip() or not content.strip():
                        st.error("닉네임과 피드백을 모두 입력해 주세요.")
                    elif contains_banned_word(nickname, content):
                        st.error("부적절한 표현이 포함되어 등록할 수 없습니다.")
                    else:
                        add_feedback(work["id"], nickname.strip(), content.strip(), profile["id"])
                        st.rerun(scope="fragment")


@st.fragment(run_every=GALLERY_REFRESH_SECONDS)
def gallery(profile: dict) -> None:
    st.subheader("학생들의 작품 갤러리")
    st.caption(f"새 작품과 과제는 {GALLERY_REFRESH_SECONDS}초마다 자동으로 갱신됩니다.")
    assignments = list_assignments(include_inactive=True)
    options = {"전체": None} | {assignment_label(a): a["id"] for a in assignments if a["status"] != "draft"}
    filter_column, sort_column = st.columns([2, 1])
    selected_label = filter_column.selectbox("과제별 보기", options.keys(), label_visibility="collapsed")
    sort_label = sort_column.selectbox("정렬", WORK_SORT_OPTIONS.keys(), label_visibility="collapsed")
    order_by, descending = WORK_SORT_OPTIONS[sort_label]
    apps = list_apps(options[selected_label], order_by=order_by, descending=descending)
    liked = liked_app_ids(profile["id"])
    feedback_by_app = list_feedback_by_app([work["id"] for work in apps])
    st.caption(f"총 {len(apps)}개 작품")

    if not apps:
        st.info("아직 등록된 작품이 없습니다.")
        return

    for start in range(0, len(apps), 3):
        columns = st.columns(3, gap="small")
        for column, work in zip(columns, apps[start:start + 3]):
            with column:
                render_work_card(work, liked, profile, feedback_by_app.get(work["id"], []))


def submit_work(profile: dict) -> None:
    st.subheader("내 작품 제출")
    assignments = [a for a in list_assignments() if can_submit(a)]
    if not assignments:
        st.info("현재 제출 가능한 과제가 없습니다.")
        return
    by_label = {assignment_label(a): a for a in assignments}
    with st.form("submit-work", clear_on_submit=True):
        selected = st.selectbox("제출할 과제", by_label.keys())
        nickname = st.text_input("닉네임", value=profile["display_name"], max_chars=MAX_NICKNAME_LENGTH)
        url = st.text_input("작품 URL", placeholder="https://your-app.streamlit.app")
        description = st.text_input("작품 소개", max_chars=MAX_DESCRIPTION_LENGTH)
        if st.form_submit_button("갤러리에 게시하기", type="primary"):
            assignment = by_label[selected]
            if not all([nickname.strip(), url.strip(), description.strip()]):
                st.error("모든 항목을 입력해 주세요.")
            elif not https_url(url):
                st.error("작품 URL은 https://로 시작해야 합니다.")
            elif contains_banned_word(nickname, description):
                st.error("부적절한 표현이 포함되어 등록할 수 없습니다.")
            elif not can_submit(assignment):
                st.error("마감된 과제입니다. 목록을 새로고침해 주세요.")
            else:
                create_app(assignment["id"], nickname.strip(), url.strip(), description.strip(), profile["id"])
                st.session_state["flash_message"] = ("success", "작품을 게시했습니다. 갤러리에 바로 반영되었습니다.")
                st.rerun()


def teacher_dashboard() -> None:
    st.subheader("교사 과제 관리")
    with st.form("new-assignment", clear_on_submit=True):
        title = st.text_input("과제 제목", max_chars=60, placeholder="예: STEP 1 · 인구·고령화 지도")
        description = st.text_area("과제 안내", max_chars=300)
        has_due = st.checkbox("마감일 설정")
        due_date = st.date_input("마감일", disabled=not has_due)
        status = st.selectbox("상태", ASSIGNMENT_STATUSES, format_func=ASSIGNMENT_STATUSES.get)
        if st.form_submit_button("과제 만들기", type="primary"):
            if not title.strip():
                st.error("과제 제목을 입력해 주세요.")
            else:
                due_at = datetime.combine(due_date, time.max).astimezone().isoformat() if has_due else None
                create_assignment(title.strip(), description.strip(), due_at, status)
                st.session_state["flash_message"] = ("success", "과제를 만들었습니다. 학생 갤러리에 자동 반영됩니다.")
                st.rerun()

    st.divider()
    for assignment in list_assignments(include_inactive=True):
        with st.expander(f"{assignment['title']} · {ASSIGNMENT_STATUSES[assignment['status']]}"):
            with st.form(f"edit-{assignment['id']}"):
                title = st.text_input("과제 제목", assignment["title"], max_chars=60)
                description = st.text_area("과제 안내", assignment.get("description") or "", max_chars=300)
                due_value = assignment.get("due_at")
                has_due = st.checkbox("마감일 설정", value=bool(due_value), key=f"due-{assignment['id']}")
                initial_date = datetime.fromisoformat(due_value.replace("Z", "+00:00")).date() if due_value else None
                due_date = st.date_input("마감일", value=initial_date, disabled=not has_due, key=f"date-{assignment['id']}")
                status = st.selectbox("상태", ASSIGNMENT_STATUSES, index=list(ASSIGNMENT_STATUSES).index(assignment["status"]), format_func=ASSIGNMENT_STATUSES.get)
                if st.form_submit_button("저장"):
                    due_at = datetime.combine(due_date, time.max).astimezone().isoformat() if has_due else None
                    update_assignment(assignment["id"], title.strip(), description.strip(), due_at, status)
                    st.session_state["flash_message"] = ("success", "과제 설정을 저장했습니다. 학생 갤러리에 자동 반영됩니다.")
                    st.rerun()


def main() -> None:
    if "SUPABASE_URL" not in st.secrets or "SUPABASE_SERVICE_KEY" not in st.secrets:
        st.error("Supabase 설정이 필요합니다. `.streamlit/secrets.toml.example`을 참고해 secrets를 설정해 주세요.")
        st.stop()
    profile = logged_in_profile()
    if not profile:
        login_screen()
        return

    st.sidebar.success(f"{profile['display_name']}님")
    st.sidebar.caption(profile["email"])
    logout_button()
    if flash := st.session_state.pop("flash_message", None):
        level, message = flash
        getattr(st, level)(message)
    tabs = st.tabs(["작품 갤러리", "내 작품 제출"] + (["과제 관리"] if profile["role"] == "teacher" else []))
    with tabs[0]:
        gallery(profile)
    with tabs[1]:
        submit_work(profile)
    if profile["role"] == "teacher":
        with tabs[2]:
            teacher_dashboard()


if __name__ == "__main__":
    main()
