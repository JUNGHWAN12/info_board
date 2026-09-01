import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """<style>
        .work-card {border:1px solid #f0e2bc;border-radius:14px;background:#fff6e0;padding:1rem;margin:.5rem 0 1rem}
        .meta {color:#6b5836;font-size:.9rem}.badge {color:#177b76;font-weight:700}
        .stButton button {font-weight:700}.assignment-guide {background:#fff6e0;border-radius:10px;padding:.8rem 1rem}
        [data-testid="stVerticalBlockBorderWrapper"] {padding: .65rem .8rem !important;}
        [data-testid="stVerticalBlockBorderWrapper"] h4 {margin: .35rem 0 !important;}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {min-height: 2.8rem;}
        </style>""",
        unsafe_allow_html=True,
    )
