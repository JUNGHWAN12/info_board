from __future__ import annotations

import streamlit as st

from src.database import ensure_profile


def logged_in_profile() -> dict | None:
    if not st.user.is_logged_in:
        return None
    identity = dict(st.user)
    email = identity.get("email")
    google_sub = identity.get("sub")
    if not email or not google_sub:
        st.error("Google 계정 정보를 가져오지 못했습니다. 다시 로그인해 주세요.")
        return None
    name = identity.get("name") or email.split("@", 1)[0]
    return ensure_profile(google_sub, email, name)


def login_screen() -> None:
    st.title("정보 수업 작품 게시판")
    st.write("작품을 제출하거나 피드백을 남기려면 학교 Google 계정으로 로그인하세요.")
    st.login("google")


def logout_button() -> None:
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.logout()
