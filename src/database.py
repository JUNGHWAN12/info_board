from __future__ import annotations

from typing import Any

import streamlit as st
from supabase import Client, create_client


def client() -> Client:
    """Create a short-lived client for each DB operation.

    Community Cloud may keep an app process alive while the upstream HTTP
    connection has already closed. Caching this client then causes intermittent
    ``Broken pipe`` failures during gallery auto-refresh.
    """
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])


def ensure_profile(google_sub: str, email: str, display_name: str) -> dict[str, Any]:
    db = client()
    result = db.table("profiles").select("*").eq("google_sub", google_sub).limit(1).execute()
    if result.data:
        return result.data[0]
    created = db.table("profiles").insert(
        {"google_sub": google_sub, "email": email, "display_name": display_name, "role": "student"}
    ).execute()
    return created.data[0]


def list_assignments(include_inactive: bool = False) -> list[dict[str, Any]]:
    query = client().table("assignments").select("*").order("sort_order").order("created_at")
    if not include_inactive:
        query = query.eq("status", "open")
    return query.execute().data or []


def create_assignment(title: str, description: str, due_at: str | None, status: str) -> None:
    rows = client().table("assignments").select("sort_order").order("sort_order", desc=True).limit(1).execute().data
    next_order = (rows[0]["sort_order"] + 1) if rows else 1
    client().table("assignments").insert(
        {"title": title, "description": description or None, "due_at": due_at, "status": status, "sort_order": next_order}
    ).execute()


def update_assignment(assignment_id: str, title: str, description: str, due_at: str | None, status: str) -> None:
    client().table("assignments").update(
        {"title": title, "description": description or None, "due_at": due_at, "status": status}
    ).eq("id", assignment_id).execute()


def list_apps(assignment_id: str | None = None) -> list[dict[str, Any]]:
    query = client().table("apps").select("*, assignments(title, status, due_at)").order("created_at", desc=True)
    if assignment_id:
        query = query.eq("assignment_id", assignment_id)
    return query.execute().data or []


def create_app(assignment_id: str, nickname: str, url: str, description: str, profile_id: str) -> None:
    client().table("apps").insert(
        {"assignment_id": assignment_id, "nickname": nickname, "url": url, "description": description, "profile_id": profile_id}
    ).execute()


def delete_app(app_id: str) -> None:
    """Delete one work; its feedback and likes cascade in the database."""
    client().table("apps").delete().eq("id", app_id).execute()


def list_feedback(app_id: str) -> list[dict[str, Any]]:
    return client().table("feedback").select("*").eq("app_id", app_id).order("created_at").execute().data or []


def list_feedback_by_app(app_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Load feedback for every visible work in one query, not one query per card."""
    if not app_ids:
        return {}
    rows = (
        client()
        .table("feedback")
        .select("*")
        .in_("app_id", app_ids)
        .order("created_at")
        .execute()
        .data
        or []
    )
    feedback_by_app: dict[str, list[dict[str, Any]]] = {app_id: [] for app_id in app_ids}
    for row in rows:
        feedback_by_app.setdefault(row["app_id"], []).append(row)
    return feedback_by_app


def add_feedback(app_id: str, nickname: str, content: str, profile_id: str) -> None:
    client().table("feedback").insert(
        {"app_id": app_id, "nickname": nickname, "content": content, "profile_id": profile_id}
    ).execute()


def liked_app_ids(profile_id: str) -> set[str]:
    rows = client().table("app_likes").select("app_id").eq("profile_id", profile_id).execute().data or []
    return {row["app_id"] for row in rows}


def add_like(app_id: str, profile_id: str) -> bool:
    result = client().rpc("add_app_like", {"p_app_id": app_id, "p_profile_id": profile_id}).execute()
    return bool(result.data)
