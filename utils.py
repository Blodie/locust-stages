"""Module for generating random data that are required for certain TPO api calls."""

import random
import uuid
from typing import Iterable

from enums import Market, Vendor
from db import VendorInfo, VENDOR_INFOS


def get_random_vendor_info(implemented_vendors: Iterable[Vendor]) -> VendorInfo:
    """Returns a random `VendorInfo` object.

    From the `VENDOR_INFOS` list filters out those that don't belong
    to any of the vendors found in `implemented_vendors` list. From
    the remaining `VendorInfo` items returns one randomly while applying
    the weighting defined in said items' `weight` field.

    Args:
        `implemented_vendors (Iterable[Vendor])`: List of `Vendor` items of which one has to
        belong to the returned `VendorInfo` object.

    Returns:
        `VendorInfo`: Random item from `VENDOR_INFOS` list.
    """
    vendor_infos = [
        vendor_info
        for vendor_info in VENDOR_INFOS
        if vendor_info.vendor in implemented_vendors
    ]
    weights = [vendor_info.weight for vendor_info in vendor_infos]
    return random.choices(vendor_infos, weights)[0]


def get_random_store_id(market: Market) -> str:
    """Returns a random store id that belongs to given `Market`.

    Max store numbers is the `market`'s value and from it randomizes a store id.
    The first 15 stores are used for something else.

    Args:
        `market (Market)`: `Market` that the random store id belongs to.

    Returns:
        `str`: Random store id.
    """

    return str(random.randint(15, market.value))


def convert_store_id_to_store_uuid(store_id: str) -> str:
    """Converts a store id to a store UUID5.

    Some vendors use UUID5 strings as store ids in their requests
    so with this method we can convert a normal store id to uuid.

    Args:
        `store_id (str)`: The store id we want to convert.

    Returns:
        `str`: UUID5 format string that corresponds to the given store id.
    """
    namespace = uuid.UUID("*********************")
    return str(uuid.uuid5(namespace, store_id))


def get_random_order_id() -> str:
    """Returns a random store id in UUID4 format.

    Returns:
        `str`: Random store id.
    """
    return str(uuid.uuid4())
