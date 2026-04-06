"""Deals API smoke tests."""

import pytest
from conftest import BASE_URL


class TestDealsAccess:
    def test_list_deals_as_admin_returns_200(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/nx/deals/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_deals_without_auth_returns_401(self, anon_session):
        resp = anon_session.get(f"{BASE_URL}/api/nx/deals/")
        assert resp.status_code == 401


class TestDealsCreate:
    def test_create_deal_minimal(self, admin_session):
        resp = admin_session.post(
            f"{BASE_URL}/api/nx/deals",
            json={
                "name": "QA Test Deal",
                "stage": "prospect",
            },
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["name"] == "QA Test Deal"

        # Cleanup: deactivate or delete if endpoint exists
        deal_id = body.get("id")
        if deal_id:
            admin_session.delete(f"{BASE_URL}/api/nx/deals/{deal_id}")
