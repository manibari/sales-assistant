"""Auth API tests — login, logout, /me, user management."""

import pytest
import requests

from conftest import BASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD


class TestLogin:
    def test_login_valid_credentials_returns_user(self):
        resp = requests.post(
            f"{BASE_URL}/api/nx/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == ADMIN_EMAIL
        assert body["role"] == "admin"
        assert "id" in body and "name" in body

    def test_login_sets_cookie(self):
        resp = requests.post(
            f"{BASE_URL}/api/nx/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert resp.status_code == 200
        assert "nexus_token" in resp.cookies

    def test_login_wrong_password_returns_401(self):
        resp = requests.post(
            f"{BASE_URL}/api/nx/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_error_message_is_chinese(self):
        resp = requests.post(
            f"{BASE_URL}/api/nx/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"},
        )
        assert resp.status_code == 401
        assert "帳號或密碼錯誤" in resp.json().get("detail", "")

    def test_login_unknown_email_returns_401(self):
        resp = requests.post(
            f"{BASE_URL}/api/nx/auth/login",
            json={"email": "nobody@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_with_valid_cookie_returns_user(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/nx/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == ADMIN_EMAIL
        assert body["role"] == "admin"

    def test_me_without_cookie_returns_401(self, anon_session):
        resp = anon_session.get(f"{BASE_URL}/api/nx/auth/me")
        assert resp.status_code == 401

    def test_me_response_excludes_password_hash(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/nx/auth/me")
        assert resp.status_code == 200
        assert "password_hash" not in resp.json()


class TestLogout:
    def test_logout_clears_cookie(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/nx/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert "nexus_token" in session.cookies

        resp = session.post(f"{BASE_URL}/api/nx/auth/logout")
        assert resp.status_code == 200

        # After logout, /me should return 401
        me_resp = session.get(f"{BASE_URL}/api/nx/auth/me")
        assert me_resp.status_code == 401


class TestUserManagement:
    def test_list_users_as_admin_returns_200(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/nx/auth/users")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_list_users_without_auth_returns_401(self, anon_session):
        resp = anon_session.get(f"{BASE_URL}/api/nx/auth/users")
        assert resp.status_code == 401

    def test_create_and_delete_user_lifecycle(self, admin_session):
        # Create
        import time
        unique_email = f"test_qa_{int(time.time())}@nexus.local"
        resp = admin_session.post(
            f"{BASE_URL}/api/nx/auth/users",
            json={
                "name": "Test User",
                "email": unique_email,
                "password": "testpass123",
                "role": "sales",
            },
        )
        assert resp.status_code == 201
        user_id = resp.json()["id"]
        assert resp.json()["role"] == "sales"

        # Duplicate email should fail
        dup_resp = admin_session.post(
            f"{BASE_URL}/api/nx/auth/users",
            json={
                "name": "Duplicate",
                "email": unique_email,
                "password": "testpass123",
                "role": "sales",
            },
        )
        assert dup_resp.status_code == 409

        # Deactivate (soft delete)
        patch_resp = admin_session.patch(
            f"{BASE_URL}/api/nx/auth/users/{user_id}",
            json={"is_active": False},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["is_active"] is False
