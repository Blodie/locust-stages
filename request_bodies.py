"""Module for storing all request bodies."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


# region STANDARD
@dataclass
class StandardV1OrderItem:
    external_data: str = "5"
    item_id: str = "1006182"
    quantity: int = 1
    price: float = 3.19


@dataclass
class StandardV1OrderBody:
    store_id: str
    order_id: str
    order_short_code: str = "13b4c"
    rider_name: str = "Gordon Ramsay"
    order_time: str = date.today().strftime("%Y-%m-%d 16:23:48")
    currency: str = "USD"
    total_amount: float = 3.19
    order_items: Optional[list[StandardV1OrderItem]] = None

    def __post_init__(self):
        if self.order_items is None:
            self.order_items = [StandardV1OrderItem()]


@dataclass
class StandarV1ReleaseBody:
    store_id: str
    order_id: str


# endregion

# region UBER
@dataclass
class UberV2OrderItem:
    quantity: int = 1
    price: float = 0.0
    tax: float = 0.0
    external_id: str = "PLU|7346"


@dataclass
class UberV2OrderBody:
    store_id: str
    order_id: str
    order_number: str = "12345"
    order_time: str = date.today().strftime("%Y-%m-%d 16:23:48")
    total_amount: float = 0.0
    total_tax: float = 0.0
    order_items: Optional[list[UberV2OrderItem]] = None

    def __post_init__(self):
        if self.order_items is None:
            self.order_items = [UberV2OrderItem()]


@dataclass
class UberV2ReleaseBody:
    StoreId: str
    OrderId: str


# endregion
