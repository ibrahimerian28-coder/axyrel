from backend.repositories.asset import AssetRepository
from backend.repositories.customer import CustomerRepository
from backend.repositories.service_request import ServiceRequestRepository
from backend.repositories.work_order import WorkOrderRepository
from backend.repositories.schedule import ScheduleRepository

__all__ = [
    "AssetRepository",
    "CustomerRepository",
    "ServiceRequestRepository",
    "WorkOrderRepository",
    "ScheduleRepository",
]

from backend.repositories.service_visit import ServiceVisitRepository

from backend.repositories.service_history import ServiceHistoryRepository

from backend.repositories.inventory import InventoryRepository

__all__ = [
    "AssetRepository", "CustomerRepository", "ServiceRequestRepository",
    "WorkOrderRepository", "ScheduleRepository", "ServiceVisitRepository",
    "ServiceHistoryRepository", "InventoryRepository",
]

from backend.repositories.inventory_transactions import InventoryTransactionRepository

from backend.repositories.service_contract import ServiceContractRepository

from backend.repositories.profitability import ProfitabilityRepository
from backend.repositories.notification import NotificationRepository

__all__ += ["NotificationRepository"]
from backend.repositories.audit_log import AuditLogRepository
