"""Shared Work Order and Service Visit status rules for Task 46."""

from __future__ import annotations

WORK_ORDER_STATUSES = frozenset({"Open", "In Progress", "Completed", "Cancelled"})
SERVICE_VISIT_STATUSES = frozenset({"Planned", "In Progress", "Completed", "Cancelled"})
TERMINAL_FILTER = frozenset({"Deleted"})

WORK_ORDER_TRANSITIONS: dict[str, frozenset[str]] = {
    "Open": frozenset({"Open", "In Progress", "Completed", "Cancelled"}),
    "In Progress": frozenset({"Open", "In Progress", "Completed", "Cancelled"}),
    "Completed": frozenset({"Completed", "Cancelled"}),
    "Cancelled": frozenset({"Cancelled"}),
}

SERVICE_VISIT_TRANSITIONS: dict[str, frozenset[str]] = {
    "Planned": frozenset({"Planned", "In Progress", "Completed", "Cancelled"}),
    "In Progress": frozenset({"In Progress", "Completed", "Cancelled"}),
    "Completed": frozenset({"Completed", "Cancelled"}),
    "Cancelled": frozenset({"Cancelled"}),
}


def normalize_status(value: str | None, *, field: str) -> str:
    status = str(value or "").strip()
    if not status:
        raise ValueError(f"{field} is required")
    return status


def ensure_work_order_transition(current: str, target: str) -> str:
    current = normalize_status(current, field="work order status")
    target = normalize_status(target, field="work order status")
    allowed = WORK_ORDER_TRANSITIONS.get(current)
    if target not in WORK_ORDER_STATUSES:
        raise ValueError(f"Unsupported work order status: {target}")
    if allowed is None or target not in allowed:
        raise ValueError(f"Work order cannot move from {current} to {target}")
    return target


def ensure_service_visit_transition(current: str, target: str) -> str:
    current = normalize_status(current, field="service visit status")
    target = normalize_status(target, field="service visit status")
    allowed = SERVICE_VISIT_TRANSITIONS.get(current)
    if target not in SERVICE_VISIT_STATUSES:
        raise ValueError(f"Unsupported service visit status: {target}")
    if allowed is None or target not in allowed:
        raise ValueError(f"Service visit cannot move from {current} to {target}")
    return target


def derive_work_order_status(visit_statuses: list[str], *, remaining_schedules: bool = False) -> str | None:
    """Execution affects activity, never whole-job terminal decisions."""
    active = [status for status in visit_statuses if status not in TERMINAL_FILTER]
    if not active:
        return None
    if any(status == "In Progress" for status in active):
        return "In Progress"
    if remaining_schedules or any(status == "Planned" for status in active):
        return "Open"
    if active:
        return "Open"
    return None
