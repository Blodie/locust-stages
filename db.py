"""Module for storing market and vendor information needed for requests."""

from dataclasses import dataclass

from enums import Implementation, Market, Vendor, Version


BEARER_PLACE_HOLDER = "Bearer placeholder"
"""Every Request, when created with random/default data, will have this
as their bearer token. This is enough on e.g. Environment.ALB so token
generation doesn't have to be called. On Environment.PERF however, it
will have to be replaced with a proper bearer token."""


@dataclass
class VendorInfo:
    """Represents a vendor, and some necessary data for constructing a request."""

    vendor: Vendor
    market: Market
    weight: int
    client_id: str
    uuid: str
    implementation: Implementation
    uses_store_uuid: bool
    version: Version
    basic_token: str = ""
    bearer_token: str = BEARER_PLACE_HOLDER


VENDOR_INFOS = [
    VendorInfo(
        vendor=Vendor.DOORDASH,
        market=Market.US,
        weight=1,
        client_id="*******************************",
        uuid="*******************",
        implementation=Implementation.STANDARD,
        basic_token="**************************",
        uses_store_uuid=False,
        version=Version.V1,
    ),
    VendorInfo(
        vendor=Vendor.UBEREATS,
        market=Market.US,
        weight=1,
        client_id="*******************************",
        implementation=Implementation.UBER,
        uuid="*******************",
        uses_store_uuid=True,
        version=Version.V2,
    ),
    VendorInfo(
        vendor=Vendor.GRUBHUB,
        market=Market.US,
        weight=1,
        client_id="*******************************",
        uuid="*******************",
        implementation=Implementation.STANDARD,
        basic_token="**************************",
        uses_store_uuid=False,
        version=Version.V1,
    ),
    VendorInfo(
        vendor=Vendor.POSTMATES,
        market=Market.US,
        weight=1,
        client_id="*******************************",
        uuid="*******************",
        implementation=Implementation.STANDARD,
        basic_token="**************************",
        uses_store_uuid=True,
        version=Version.V1,
    ),
    VendorInfo(
        vendor=Vendor.DOORDASH,
        market=Market.CA,
        weight=1,
        client_id="*******************************",
        uuid="*******************",
        implementation=Implementation.STANDARD,
        basic_token="**************************",
        uses_store_uuid=False,
        version=Version.V1,
    ),
    VendorInfo(
        vendor=Vendor.UBEREATS,
        market=Market.CA,
        weight=1,
        client_id="*******************************",
        implementation=Implementation.UBER,
        uuid="*******************",
        uses_store_uuid=True,
        version=Version.V2,
    ),
    VendorInfo(
        vendor=Vendor.SKIPTHEDISHES,
        market=Market.CA,
        weight=1,
        client_id="*******************************",
        uuid="*******************",
        implementation=Implementation.STANDARD,
        basic_token="**************************",
        uses_store_uuid=False,
        version=Version.V1,
    ),
]
