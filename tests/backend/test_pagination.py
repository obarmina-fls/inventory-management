"""
Tests for opt-in pagination (limit/offset + X-Total-Count) on list endpoints.
"""
import pytest

import main

# List endpoints that accept limit/offset. Each must keep returning a plain JSON array.
PAGINATED_ENDPOINTS = [
    "/api/inventory",
    "/api/orders",
    "/api/demand",
    "/api/backlog",
    "/api/spending/transactions",
    "/api/restocking/orders",
    "/api/tasks",
]


class TestPagination:
    """Test suite for limit/offset pagination."""

    @pytest.mark.parametrize("path", PAGINATED_ENDPOINTS)
    def test_unpaginated_request_returns_full_list_with_total(self, client, path):
        """Test that omitting limit returns everything, with the total in X-Total-Count."""
        response = client.get(path)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert response.headers["x-total-count"] == str(len(data))

    def test_get_orders_first_page(self, client):
        """Test that limit returns the first N orders and the full total."""
        all_orders = client.get("/api/orders").json()

        response = client.get("/api/orders?limit=25")
        assert response.status_code == 200
        assert response.json() == all_orders[:25]
        assert response.headers["x-total-count"] == str(len(all_orders))

    def test_get_orders_second_page(self, client):
        """Test that offset moves to the next page without overlap."""
        all_orders = client.get("/api/orders").json()

        page2 = client.get("/api/orders?limit=25&offset=25").json()
        assert page2 == all_orders[25:50]

    def test_pages_cover_all_items_exactly_once(self, client):
        """Test that walking every page yields each inventory item exactly once."""
        all_ids = [item["id"] for item in client.get("/api/inventory").json()]

        seen = []
        offset = 0
        while True:
            page = client.get(f"/api/inventory?limit=10&offset={offset}").json()
            if not page:
                break
            seen.extend(item["id"] for item in page)
            offset += 10

        assert seen == all_ids

    def test_pagination_applies_after_filters(self, client):
        """Test that the total and the page reflect the filtered list, not the whole dataset."""
        filtered = client.get("/api/orders?warehouse=Tokyo").json()

        response = client.get("/api/orders?warehouse=Tokyo&limit=5")
        assert response.headers["x-total-count"] == str(len(filtered))
        page = response.json()
        assert page == filtered[:5]
        for order in page:
            assert order["warehouse"] == "Tokyo"

    def test_offset_past_end_returns_empty_page(self, client):
        """Test that an offset beyond the total returns an empty list but the real total."""
        total = len(client.get("/api/orders").json())

        response = client.get(f"/api/orders?limit=10&offset={total + 100}")
        assert response.status_code == 200
        assert response.json() == []
        assert response.headers["x-total-count"] == str(total)

    @pytest.mark.parametrize(
        "query",
        ["limit=0", "limit=-1", f"limit={main.MAX_PAGE_SIZE + 1}", "offset=-1", "limit=abc"],
    )
    def test_invalid_pagination_params_rejected(self, client, query):
        """Test that out-of-range or non-numeric limit/offset values are a 422."""
        response = client.get(f"/api/orders?{query}")
        assert response.status_code == 422

    def test_total_header_exposed_to_browser(self, client):
        """Test that CORS lets the frontend read X-Total-Count."""
        response = client.get("/api/orders?limit=5", headers={"Origin": "http://localhost:3000"})
        exposed = response.headers.get("access-control-expose-headers", "").lower()
        assert "x-total-count" in exposed
