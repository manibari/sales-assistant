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
        # Get a real client_id first
        clients = admin_session.get(f"{BASE_URL}/api/nx/clients/").json()
        assert len(clients) > 0, "Need at least one client in DB to test deal creation"
        client_id = clients[0]["id"]

        resp = admin_session.post(
            f"{BASE_URL}/api/nx/deals",
            json={
                "name": "QA Test Deal",
                "client_id": client_id,
            },
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["name"] == "QA Test Deal"

        # Cleanup
        deal_id = body.get("id")
        if deal_id:
            admin_session.delete(f"{BASE_URL}/api/nx/deals/{deal_id}")
