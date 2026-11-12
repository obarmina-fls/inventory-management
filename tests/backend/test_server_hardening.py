"""
Tests for API hardening: CORS allow-list and caps on the write endpoints.
"""
import pytest

import main
import mock_data


@pytest.fixture
def isolated_submitted_orders(tmp_path, monkeypatch):
    """Persist orders to a temp file and start empty, restoring the shared list in place."""
    path = tmp_path / "submitted_orders.json"
    path.write_text("[]")
    monkeypatch.setattr(mock_data, "SUBMITTED_ORDERS_FILE", str(path))
    saved = list(mock_data.submitted_orders)
    mock_data.submitted_orders.clear()
    yield path
    mock_data.submitted_orders.clear()
    mock_data.submitted_orders.extend(saved)


@pytest.fixture
def isolated_tasks():
    """Start with no tasks and restore in place (main.py shares the list object)."""
    saved = list(mock_data.tasks)
    mock_data.tasks.clear()
    yield
    mock_data.tasks[:] = saved


@pytest.fixture
def valid_sku():
    """A SKU the restocking endpoint accepts (it looks prices up in demand forecasts)."""
    return mock_data.demand_forecasts[0]["item_sku"]


class TestCorsPolicy:
    """Test suite for the CORS allow-list."""

    def test_cors_allows_dev_frontend(self, client):
        """Test that the Vite dev server origin is allowed."""
        response = client.get("/api/inventory", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_rejects_unknown_origin(self, client):
        """Test that an arbitrary website gets no CORS grant."""
        response = client.get("/api/inventory", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in response.headers

    def test_cors_preflight_rejects_unknown_origin_for_writes(self, client):
        """Test that a cross-site preflight for a write endpoint is refused."""
        response = client.options(
            "/api/restocking/orders",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers

    def test_cors_does_not_allow_credentials(self, client):
        """Test that credentials are not allowed, so Origin is never reflected for cookies."""
        response = client.get("/api/inventory", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-credentials" not in response.headers


class TestWriteEndpointCaps:
    """Test suite for the caps on unauthenticated write endpoints."""

    def test_submit_restock_order_rejected_at_cap(self, client, isolated_submitted_orders, valid_sku, monkeypatch):
        """Test that restock submissions stop at MAX_SUBMITTED_ORDERS."""
        monkeypatch.setattr(main, "MAX_SUBMITTED_ORDERS", 2)
        payload = {"items": [{"sku": valid_sku, "quantity": 1}]}

        for _ in range(2):
            assert client.post("/api/restocking/orders", json=payload).status_code == 201

        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 409
        assert "limit" in response.json()["detail"].lower()
        # Nothing past the cap was stored
        assert len(mock_data.submitted_orders) == 2

    def test_create_task_rejected_at_cap(self, client, isolated_tasks, monkeypatch):
        """Test that task creation stops at MAX_TASKS."""
        monkeypatch.setattr(main, "MAX_TASKS", 1)
        payload = {"title": "Check stock", "priority": "low", "dueDate": "2025-12-01"}

        assert client.post("/api/tasks", json=payload).status_code == 201

        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 409
        assert "limit" in response.json()["detail"].lower()
        assert len(mock_data.tasks) == 1


class TestQueryParamValidation:
    """Test suite for month/filter query-param validation."""

    @pytest.mark.parametrize("month", ["-", "2025", "2025-13", "Q5-2025", "january", "2025-01-01"])
    def test_invalid_month_rejected(self, client, month):
        """Test that malformed month values are a 422 instead of matching everything."""
        response = client.get(f"/api/orders?month={month}")
        assert response.status_code == 422

    def test_month_matches_order_date_prefix(self, client):
        """Test that a month filter returns only orders from that month."""
        data = client.get("/api/orders?month=2025-03").json()
        assert len(data) > 0
        assert all(order["order_date"].startswith("2025-03") for order in data)

    def test_unmapped_quarter_returns_no_orders(self, client):
        """Test that a well-formed quarter with no data returns nothing (it used to return everything)."""
        response = client.get("/api/orders?month=Q1-2030")
        assert response.status_code == 200
        assert response.json() == []

    def test_overlong_filter_rejected(self, client):
        """Test that warehouse/category/status values are length-bounded."""
        response = client.get("/api/orders?warehouse=" + "x" * 51)
        assert response.status_code == 422

    def test_overlong_sku_rejected(self, client, isolated_submitted_orders):
        """Test that restock SKUs are length-bounded before being echoed in errors."""
        response = client.post("/api/restocking/orders", json={"items": [{"sku": "x" * 33, "quantity": 1}]})
        assert response.status_code == 422
        assert len(mock_data.submitted_orders) == 0


class TestResponseHeaders:
    """Test suite for compression and caching headers."""

    def test_large_response_is_gzipped(self, client):
        """Test that large JSON responses are compressed when the client accepts gzip."""
        response = client.get("/api/orders", headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "gzip"
        assert len(response.json()) > 0

    def test_static_endpoint_is_cacheable(self, client):
        """Test that read-only mock-data endpoints allow short browser caching."""
        response = client.get("/api/inventory")
        assert response.headers["cache-control"] == "public, max-age=60"

    @pytest.mark.parametrize("path", ["/api/spending/summary", "/api/spending/transactions", "/api/tasks", "/api/backlog", "/api/restocking/orders"])
    def test_financial_and_mutable_endpoints_not_cached(self, client, path):
        """Test that financial and write-affected endpoints are never cached."""
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"

    def test_error_responses_not_cached(self, client):
        """Test that error responses on cacheable paths are not cached."""
        response = client.get("/api/orders?month=bad")
        assert response.status_code == 422
        assert response.headers["cache-control"] == "no-store"
