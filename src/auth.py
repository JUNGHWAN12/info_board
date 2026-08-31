from __future__ import annotations

import streamlit as st

from src.database import ensure_profile


def logged_in_profile() -> dict | None:
    # `is_logged_in` is only added when Streamlit has loaded a valid [auth]
    # configuration. Use dict access so an incomplete deployment configuration
    # shows the login screen instead of crashing with AttributeError.
    identity = st.user.to_dict()
    if not identity.get("is_logged_in", False):
        return None
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
    auth_settings = st.secrets.get("auth", {})
    google_settings = auth_settings.get("google", {})
    if not auth_settings.get("redirect_uri") or not google_settings.get("client_id") or not google_settings.get("client_secret"):
        st.error("Google 로그인 설정이 없습니다. Community Cloud Settings → Secrets에 [auth]와 [auth.google] 설정을 추가해 주세요.")
        st.stop()
    st.login("google")


def logout_button() -> None:
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.logout()
