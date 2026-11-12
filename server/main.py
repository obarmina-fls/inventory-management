import math
import os
import threading
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
import mock_data
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    # Match on the YYYY-MM prefix of order_date. The old substring check let values like
    # "-" match every order; MonthParam now rejects such values, and this keeps matching exact.
    if month.startswith('Q'):
        # A well-formed quarter we have no data mapping for matches nothing (it used to return everything)
        months = set(QUARTER_MAP.get(month, []))
    else:
        months = {month}
    return [item for item in items if item.get('order_date', '')[:7] in months]

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS: only the Vite dev server may call the API from a browser. A wildcard origin let
# any website the developer visited drive the write endpoints (orders, POs, tasks) on
# localhost. Override with CORS_ORIGINS="https://a.example,https://b.example".
# No cookies or auth headers are used, so credentials stay off: with them on, Starlette
# reflects the caller's Origin, which would undo the allow-list once auth is added.
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
    # Lets the browser read the total behind a paginated list response
    expose_headers=["X-Total-Count"],
)

# Compress JSON responses over 1KB (/api/orders is ~110KB raw, ~10x smaller gzipped)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Read-only endpoints serve static mock data, so browsers may reuse them briefly.
# Everything else is no-store: endpoints whose data the write endpoints change, and the
# financial (/api/spending) endpoints, which must never sit in a shared cache once auth exists.
CACHEABLE_PATHS = {
    "/api/inventory", "/api/orders", "/api/demand", "/api/dashboard/summary",
    "/api/reports/quarterly", "/api/reports/monthly-trends",
}

@app.middleware("http")
async def cache_control(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/") and "cache-control" not in response.headers:
        cacheable = request.method == "GET" and response.status_code == 200 and request.url.path in CACHEABLE_PATHS
        response.headers["Cache-Control"] = "public, max-age=60" if cacheable else "no-store"
    return response

# Shared query-param types. Free-form strings used to be accepted unbounded.
# month: 'all', 'YYYY-MM' or 'Qn-YYYY' (what FilterBar sends); anything else is a 422.
MonthParam = Annotated[Optional[str], Query(pattern=r"^(all|\d{4}-(0[1-9]|1[0-2])|Q[1-4]-\d{4})$")]
# warehouse/category/status stay free text (matching is case-insensitive) but are length-bounded
FilterParam = Annotated[Optional[str], Query(max_length=50)]

# Opt-in pagination for list endpoints. Without `limit` the full list is returned, exactly as
# before, because the dashboard and status counts aggregate over the whole list client-side.
# The body stays a plain JSON array (no envelope) so existing clients keep working; the
# pre-pagination total is always sent in the X-Total-Count header.
MAX_PAGE_SIZE = 500
LimitParam = Annotated[Optional[int], Query(ge=1, le=MAX_PAGE_SIZE)]
OffsetParam = Annotated[int, Query(ge=0)]

def paginate(items: list, response: Response, limit: Optional[int], offset: int) -> list:
    """Slice an already filtered and sorted list, and report its full length in X-Total-Count."""
    response.headers["X-Total-Count"] = str(len(items))
    end = None if limit is None else offset + limit
    return items[offset:end]

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False
    # Set when has_purchase_order is True; the Dashboard uses it to show "View PO"
    purchase_order_id: Optional[str] = None

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0)
    unit_cost: float = Field(ge=0)
    expected_delivery_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: Optional[str] = Field(default=None, max_length=1000)

class Task(BaseModel):
    # String ids ("TASK-n") so API tasks never collide with the numeric ids of the
    # mock tasks in client/src/composables/useAuth.js, which App.vue checks first.
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    # camelCase dueDate matches the payload TasksModal.vue already sends
    title: str = Field(min_length=1, max_length=200)
    priority: str = Field(pattern=r"^(high|medium|low)$")
    dueDate: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

class RestockItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    # None for lines ordered straight from inventory (low-stock restock), which have no forecast
    trend: Optional[str] = None

class RestockRecommendation(BaseModel):
    budget: float
    items: List[RestockItem]
    total_cost: float
    remaining_budget: float
    full_cost: float  # cost of restocking every item at full quantity (useful as slider max)

class RestockOrderLine(BaseModel):
    # Bounded because an unknown SKU is echoed back in the 400 error detail
    sku: str = Field(min_length=1, max_length=32)
    # Upper bound guards against absurd totals being persisted to submitted_orders.json
    quantity: int = Field(gt=0, le=100_000)

class SubmitRestockRequest(BaseModel):
    items: List[RestockOrderLine] = Field(min_length=1)

class SubmittedOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockItem]
    total_cost: float
    status: str
    submitted_date: str
    lead_time_days: int
    expected_delivery: str

# Upper bound on budget: also rejects 'inf', which would overflow math.floor in the greedy fill
MAX_RESTOCK_BUDGET = 100_000_000

# Serializes order numbering + append + file write across FastAPI's threadpool workers
_submit_lock = threading.Lock()

# Caps on what the unauthenticated write endpoints can accumulate. Each restock submission
# rewrites the whole JSON file under _submit_lock, so an unbounded list makes every POST
# slower (~290ms at 10k orders) and lets a script fill the disk. Tasks and POs live in
# memory only, but are capped for the same reason.
MAX_SUBMITTED_ORDERS = 1_000
MAX_TASKS = 500

# Inventory items carry no supplier lead time; orders for SKUs that are only in inventory
# (e.g. low-stock restocks from the Inventory page) assume this standard lead time.
DEFAULT_INVENTORY_LEAD_TIME_DAYS = 14

# Trend rank used for restock priority: rising demand is the most urgent to cover.
TREND_PRIORITY = {'increasing': 0, 'stable': 1, 'decreasing': 2}

def recommended_quantity(forecast: dict) -> int:
    """Units needed to cover the forecast period.

    Shortfall = forecasted - current demand. Stable/decreasing items have little or no
    shortfall, so they fall back to a 10% safety-stock buffer of forecasted demand
    to keep every forecast item eligible for restocking."""
    shortfall = forecast['forecasted_demand'] - forecast['current_demand']
    if shortfall > 0:
        return shortfall
    return max(1, math.ceil(forecast['forecasted_demand'] * 0.10))

def build_restock_recommendation(budget: float, forecasts: List[dict]) -> dict:
    """Priority-greedy fill of the budget with demand-forecast items.

    Priority: trend (increasing > stable > decreasing), then growth ratio
    forecasted/current descending. Each item is added at full recommended quantity if it
    fits; otherwise as many whole units as the remaining budget allows, then we continue
    down the list (a cheaper lower-priority item may still fit)."""
    ranked = sorted(
        forecasts,
        key=lambda f: (
            TREND_PRIORITY.get(f['trend'], len(TREND_PRIORITY)),
            -(f['forecasted_demand'] / f['current_demand']) if f['current_demand'] else float('-inf'),
        ),
    )
    remaining = budget
    items = []
    full_cost = 0.0
    for f in ranked:
        qty = recommended_quantity(f)
        full_cost += qty * f['unit_cost']
        affordable = min(qty, math.floor(round(remaining / f['unit_cost'], 6)))
        if affordable < 1:
            continue
        line_total = round(affordable * f['unit_cost'], 2)
        remaining = round(remaining - line_total, 2)
        items.append({
            'sku': f['item_sku'],
            'name': f['item_name'],
            'quantity': affordable,
            'unit_cost': f['unit_cost'],
            'line_total': line_total,
            'lead_time_days': f['lead_time_days'],
            'trend': f['trend'],
        })
    total_cost = round(sum(i['line_total'] for i in items), 2)
    return {
        'budget': budget,
        'items': items,
        'total_cost': total_cost,
        'remaining_budget': round(budget - total_cost, 2),
        'full_cost': round(full_cost, 2),
    }

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    response: Response,
    warehouse: FilterParam = None,
    category: FilterParam = None,
    limit: LimitParam = None,
    offset: OffsetParam = 0,
):
    """Get inventory items with optional filtering and pagination"""
    return paginate(apply_filters(inventory_items, warehouse, category), response, limit, offset)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    response: Response,
    warehouse: FilterParam = None,
    category: FilterParam = None,
    status: FilterParam = None,
    month: MonthParam = None,
    limit: LimitParam = None,
    offset: OffsetParam = 0,
):
    """Get orders with optional filtering and pagination"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return paginate(filtered_orders, response, limit, offset)

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts(response: Response, limit: LimitParam = None, offset: OffsetParam = 0):
    """Get demand forecasts, optionally paginated"""
    return paginate(demand_forecasts, response, limit, offset)

@app.get("/api/restocking/recommendations", response_model=RestockRecommendation)
def get_restock_recommendations(budget: float = Query(..., ge=0, le=MAX_RESTOCK_BUDGET)):
    """Recommend demand-forecast items to restock within the given budget"""
    return build_restock_recommendation(budget, demand_forecasts)

@app.get("/api/restocking/orders", response_model=List[SubmittedOrder])
def get_submitted_orders(response: Response, limit: LimitParam = None, offset: OffsetParam = 0):
    """Get submitted restocking orders, newest first, optionally paginated"""
    # Tie-break on the numeric order sequence: submitted_date has 1-second resolution
    ordered = sorted(mock_data.submitted_orders, key=lambda o: (o['submitted_date'], _order_seq(o)), reverse=True)
    return paginate(ordered, response, limit, offset)

def _order_seq(order: dict) -> int:
    """Numeric sequence from an id like 'RST-12' (0 if malformed)."""
    try:
        return int(order['id'].rsplit('-', 1)[1])
    except (KeyError, IndexError, ValueError):
        return 0

@app.post("/api/restocking/orders", response_model=SubmittedOrder, status_code=201)
def submit_restock_order(request: SubmitRestockRequest):
    """Submit a restocking order. Prices and lead times are looked up server-side
    rather than trusted from the client.

    A SKU is resolved from demand forecasts first (they carry supplier lead time and
    trend), then from inventory, so low-stock items can be restocked from the Inventory
    page even when they have no forecast."""
    forecasts_by_sku = {f['item_sku']: f for f in demand_forecasts}
    inventory_by_sku = {i['sku']: i for i in inventory_items}
    skus = [line.sku for line in request.items]
    if len(skus) != len(set(skus)):
        raise HTTPException(status_code=400, detail="Duplicate SKUs in order; combine quantities into one line")
    lines = []
    for line in request.items:
        forecast = forecasts_by_sku.get(line.sku)
        if forecast:
            name, unit_cost = forecast['item_name'], forecast['unit_cost']
            lead_time_days, trend = forecast['lead_time_days'], forecast['trend']
        elif line.sku in inventory_by_sku:
            item = inventory_by_sku[line.sku]
            name, unit_cost = item['name'], item['unit_cost']
            lead_time_days, trend = DEFAULT_INVENTORY_LEAD_TIME_DAYS, None
        else:
            raise HTTPException(status_code=400, detail=f"Unknown SKU: {line.sku}")
        lines.append({
            'sku': line.sku,
            'name': name,
            'quantity': line.quantity,
            'unit_cost': unit_cost,
            'line_total': round(line.quantity * unit_cost, 2),
            'lead_time_days': lead_time_days,
            'trend': trend,
        })

    # The order arrives complete only when its slowest item arrives.
    lead_time = max(l['lead_time_days'] for l in lines)
    with _submit_lock:
        if len(mock_data.submitted_orders) >= MAX_SUBMITTED_ORDERS:
            raise HTTPException(status_code=409, detail="Submitted order limit reached")
        now = datetime.now().replace(microsecond=0)
        # max+1 rather than len+1 so ids stay unique even if the JSON file was hand-edited
        next_num = max((_order_seq(o) for o in mock_data.submitted_orders), default=0) + 1
        order = {
            'id': f"RST-{next_num}",
            'order_number': f"RST-{now.year}-{next_num:04d}",
            'items': lines,
            'total_cost': round(sum(l['line_total'] for l in lines), 2),
            'status': 'Submitted',
            'submitted_date': now.isoformat(),
            'lead_time_days': lead_time,
            'expected_delivery': (now + timedelta(days=lead_time)).isoformat(),
        }
        mock_data.submitted_orders.append(order)
        mock_data.save_submitted_orders()
    return order

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog(response: Response, limit: LimitParam = None, offset: OffsetParam = 0):
    """Get backlog items with purchase order status, optionally paginated"""
    # Add has_purchase_order flag to each backlog item
    po_by_backlog = {po["backlog_item_id"]: po["id"] for po in purchase_orders}
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        po_id = po_by_backlog.get(item["id"])
        item_dict["has_purchase_order"] = po_id is not None
        item_dict["purchase_order_id"] = po_id
        result.append(item_dict)
    return paginate(result, response, limit, offset)

_po_lock = threading.Lock()

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one PO per backlog item).
    Stored in memory only, like the rest of the mock data."""
    if not any(b["id"] == request.backlog_item_id for b in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")
    with _po_lock:
        if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail=f"Backlog item {request.backlog_item_id} already has a purchase order")
        # max+1 rather than len+1 so ids stay unique if purchase_orders.json was hand-edited
        next_num = max((_order_seq(po) for po in purchase_orders), default=0) + 1
        po = {
            "id": f"PO-{next_num}",
            **request.model_dump(),
            "status": "Pending",
            "created_date": datetime.now().replace(microsecond=0).isoformat(),
        }
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order attached to a backlog item."""
    for po in purchase_orders:
        if po["backlog_item_id"] == backlog_item_id:
            return po
    raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")

_task_lock = threading.Lock()

def _find_task(task_id: str) -> dict:
    for task in mock_data.tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/api/tasks", response_model=List[Task])
def get_tasks(response: Response, limit: LimitParam = None, offset: OffsetParam = 0):
    """Get tasks created through the API (newest first), optionally paginated.
    Mock profile tasks live client-side."""
    return paginate(list(reversed(mock_data.tasks)), response, limit, offset)

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a pending task. Stored in memory only."""
    with _task_lock:
        if len(mock_data.tasks) >= MAX_TASKS:
            raise HTTPException(status_code=409, detail="Task limit reached")
        next_num = max((_order_seq(t) for t in mock_data.tasks), default=0) + 1
        task = {"id": f"TASK-{next_num}", **request.model_dump(), "status": "pending"}
        mock_data.tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed. The client sends no body,
    so PATCH here means "flip status" rather than a partial update."""
    with _task_lock:
        task = _find_task(task_id)
        task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}", response_model=Task)
def delete_task(task_id: str):
    """Delete a task and return it."""
    with _task_lock:
        task = _find_task(task_id)
        mock_data.tasks.remove(task)
    return task

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: FilterParam = None,
    category: FilterParam = None,
    status: FilterParam = None,
    month: MonthParam = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions(response: Response, limit: LimitParam = None, offset: OffsetParam = 0):
    """Get recent transactions, optionally paginated"""
    return paginate(recent_transactions, response, limit, offset)

@app.get("/api/reports/quarterly")
def get_quarterly_reports(
    warehouse: FilterParam = None,
    category: FilterParam = None,
    status: FilterParam = None,
    month: MonthParam = None
):
    """Get quarterly performance reports, honoring the same filters as /api/orders"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    # Reverse lookup of QUARTER_MAP: 'YYYY-MM' -> quarter label
    month_to_quarter = {m: q for q, months in QUARTER_MAP.items() for m in months}

    quarters = {}

    for order in filtered_orders:
        quarter = month_to_quarter.get(order.get('order_date', '')[:7])
        if not quarter:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends(
    warehouse: FilterParam = None,
    category: FilterParam = None,
    status: FilterParam = None,
    month: MonthParam = None
):
    """Get month-over-month trends, honoring the same filters as /api/orders"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    months = {}

    for order in filtered_orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    # Loopback only by default: 0.0.0.0 exposed the unauthenticated write endpoints to
    # anyone on the same network. Set HOST=0.0.0.0 to opt in (e.g. inside a container).
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=8001)
