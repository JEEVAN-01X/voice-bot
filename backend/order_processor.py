from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Order:
    order_id: str
    customer_phone: str
    language: str
    items: List[str]
    address: Optional[str]
    status: str = 'pending'
    retries: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class OrderProcessor:
    MAX_RETRIES = 3

    @staticmethod
    def validate(order: Order) -> tuple:
        if not order.items:
            return False, 'no_items'
        if len(order.items) > 20:
            return False, 'too_many_items'
        return True, 'ok'

    @staticmethod
    def can_retry(order: Order) -> bool:
        return order.retries < OrderProcessor.MAX_RETRIES

    @staticmethod
    def format_summary(order: Order) -> str:
        return ', '.join(order.items)
