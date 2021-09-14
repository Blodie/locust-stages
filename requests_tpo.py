"""Module for storing all requests."""

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Optional

import utils
from config import ENVIRONMENT
from db import VendorInfo
from enums import Environment, Implementation, Vendor, Version
from request_bodies import (
    StandarV1ReleaseBody,
    StandardV1OrderBody,
    UberV2OrderBody,
    UberV2ReleaseBody,
)


class RequestNotImplementedException(Exception):
    """Not every request can be called on every vendor.
    e.g. canadian Skip The Dishes doesn't have GetMenu implemented.
    """


class RouteNotImplementedException(Exception):
    """Among the request's `routes` dict, for the current environment,
    a value cannot be found
    """


class RequestBodyNotImplementedException(Exception):
    """In the _set_up_request_body method of the request
    for current environment and the request's vendor's version
    a body cannot be found."""


@dataclass
class Request(ABC):
    """Abstract class for representing a request. When creating a request, any fields left `None`
    will be automatically filled with random/default data defined in each request's internal methods.

    Fields:
        These are the necessary fields for a request to be sent:
        `request_method`: Request method used in request. Defaults to 'POST'.
        `url`: The final url for the request. Built from `base_urls` and `routes` if not explicitly given.
        `request_headers`: Request headers used for the request.
        `request_body`: Request body used for the request.

        These fields are used for random/default data creation for the fields above in case some of them are `None`:
        `vendor_implementations`: Which vendors have the request implemented, and their ALB ports as well.
        `vendor_info`: Needed for automatic header, url and bearer token creation.
        `base_urls`: Base urls for each environment.
        `routes`: Request's routes for each environment.
        `success_status_codes`: List of status codes that are considered a success.
        (These can be 400-599 codes as well if we want to test that.)
    """

    method: str = "POST"
    url: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    body: Optional[str] = None

    vendor_implementations: Optional[dict[Vendor, int]] = None
    vendor_info: Optional[VendorInfo] = None
    base_urls: Optional[dict[Environment, str]] = None
    routes: Optional[dict[Environment, str]] = None
    success_status_codes: Optional[list[int]] = None

    @property
    def bearer_token(self) -> str:
        assert self.headers is not None
        return self.headers["Authorization"]

    @bearer_token.setter
    def bearer_token(self, token: str) -> None:
        assert self.headers is not None
        self.headers["Authorization"] = token

    @property
    def locust_display_name(self) -> str:
        """This is seen when locust is printing the request results on the console."""
        assert self.vendor_info is not None
        return f"{ENVIRONMENT}_{self.vendor_info.market}_{self.__class__.__name__}_{self.vendor_info.vendor}_{self.vendor_info.version}".upper()

    def __post_init__(self) -> None:
        """Automatically runs after object creation.
        Checks all the necessary fields in the required order.
        Any fields left `None` when creating the request object will
        be filled with random/default data defined in the internal methods.
        """
        self._setup_vendor_implementations()
        self._setup_vendor_info()
        self._setup_base_urls()
        self._setup_routes()
        self._setup_request_headers()
        self._setup_success_status_codes()

    @abstractmethod
    def _setup_vendor_implementations(self) -> None:
        """If not given, sets up which vendors have the request implemented."""

    def _setup_vendor_info(self) -> None:
        """If not given, generates a random vendor for the request.
        If we gave a `VendorInfo` when creating the request object then checks
        whether that particular vendor has the request implemented.
        """
        assert self.vendor_implementations is not None
        if self.vendor_info is None:
            self.vendor_info = utils.get_random_vendor_info(self.vendor_implementations)
            return

        if self.vendor_info.vendor not in self.vendor_implementations:
            raise RequestNotImplementedException(
                f'Request "{self.__class__.__name__}" is not implemented for vendor "{self.vendor_info.vendor}".'
            )

    def _setup_base_urls(self) -> None:
        """If not given, sets up base urls for every environment."""
        if self.base_urls is not None:
            return

        self.base_urls = {
            Environment.PERF: "https://*****************.com/default",
            Environment.ALB: "http://{market}-**********.com:{port}",
            Environment.NLB: "http://{market}-**********.com:9000",
        }

    @abstractmethod
    def _setup_routes(self) -> None:
        """If not given, sets up routes for every environment and the given request."""

    def _setup_url(self, **kwargs: str) -> None:
        """Used for each request's url setup process."""
        if self.url is not None:
            return

        assert self.base_urls is not None
        assert self.routes is not None
        assert self.vendor_info is not None
        assert self.vendor_implementations is not None
        try:
            self.url = (
                f"{self.base_urls[ENVIRONMENT]}{self.routes[ENVIRONMENT]}".format(
                    market=f"{self.vendor_info.market}",
                    version=f"{self.vendor_info.version}",
                    vendor=f"{self.vendor_info.vendor}",
                    port=next(
                        alb_port
                        for vendor, alb_port in self.vendor_implementations.items()
                        if vendor is self.vendor_info.vendor
                    ),
                    **kwargs,
                )
            )
        except KeyError:
            raise RouteNotImplementedException(
                f"Route for request '{self.__class__.__name__}' on environment '{ENVIRONMENT}' cannot be found."
            )

    def _setup_request_headers(self) -> None:
        """If not given, sets up `request_headers` from `vendor_info`."""
        if self.headers is not None:
            return

        assert self.vendor_info is not None
        self.headers = {
            "Content-Type": "application/json",
            "mcd-clientid": self.vendor_info.client_id,
            "mcd-marketid": f"{self.vendor_info.market}",
            "mcd-uuid": self.vendor_info.uuid,
            "Authorization": self.vendor_info.bearer_token,
        }

    def _setup_request_body(self) -> None:
        """If not given, sets up `request_body`."""
        if self.body is None:
            self.body = ""

    def _setup_success_status_codes(self) -> None:
        """If not given, defaults `success_status_codes` to [200, 201]"""
        if self.success_status_codes is None:
            self.success_status_codes = [200, 201]


@dataclass
class GetMenu(Request):
    """Class used for get menu api calls.

    Fields:
        request_method: Different from base class. Defaults to 'GET'.
        store_id: Store id whose menu we want to get.
    """

    request_method: str = "GET"
    store_id: Optional[str] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self._setup_store_id()
        self._setup_get_menu_url()

    def _setup_vendor_implementations(self) -> None:
        if self.vendor_implementations is not None:
            return

        self.vendor_implementations = {
            Vendor.DOORDASH: 9019,
            Vendor.GRUBHUB: 9025,
            Vendor.POSTMATES: 9033,
        }

    def _setup_routes(self) -> None:
        """Sets up default routes for request if not given."""
        if self.routes is not None:
            return

        self.routes = {
            Environment.PERF: "/{version}/vendors/{vendor}/menu/{store_id}",
            Environment.ALB: "/{version}/stores/menu/{vendor}/{market}/{store_id}",
            Environment.NLB: "/{version}/stores/menu/{vendor}/{market}/{store_id}",
        }

    def _setup_store_id(self) -> None:
        """Generates random store id for request if not given."""
        if self.store_id is not None:
            return

        assert self.vendor_info is not None
        self.store_id = utils.get_random_store_id(self.vendor_info.market)
        if self.vendor_info.uses_store_uuid:
            self.store_id = utils.convert_store_id_to_store_uuid(self.store_id)

    def _setup_get_menu_url(self) -> None:
        """Sets up the url for this request, if not given."""
        assert self.store_id is not None
        self._setup_url(store_id=self.store_id)


@dataclass
class Order(Request):
    """Class used for submit order api calls.

    Fields:
        store_id: Store id needed for url and request_body.
        order_id: Order id needed for request_body.
    """

    store_id: Optional[str] = None
    order_id: Optional[str] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self._setup_store_id()
        self._setup_order_url()
        self._setup_order_id()
        self._setup_request_body()

    def _setup_vendor_implementations(self) -> None:
        if self.vendor_implementations is not None:
            return

        self.vendor_implementations = {
            Vendor.DOORDASH: 9020,
            Vendor.UBEREATS: 9002,
            Vendor.GRUBHUB: 9026,
            Vendor.POSTMATES: 9034,
            Vendor.SKIPTHEDISHES: 9012,
        }

    def _setup_routes(self) -> None:
        if self.routes is not None:
            return

        self.routes = {
            Environment.PERF: "/{version}/vendors/{vendor}/order",
            Environment.ALB: "/{version}/orders/{vendor}/{market}/{store_id}",
            Environment.NLB: "/{version}/orders/{vendor}/{market}/{store_id}",
        }

    def _setup_store_id(self) -> None:
        """Generates random store id if not given."""
        if self.store_id is not None:
            return

        assert self.vendor_info is not None
        self.store_id = utils.get_random_store_id(self.vendor_info.market)
        if self.vendor_info.uses_store_uuid:
            self.store_id = utils.convert_store_id_to_store_uuid(self.store_id)

    def _setup_order_url(self) -> None:
        """Sets up the url for this request, if not given."""
        assert self.store_id is not None
        self._setup_url(store_id=self.store_id)

    def _setup_order_id(self) -> None:
        """Generates random order id if not given."""
        if self.order_id is None:
            self.order_id = utils.get_random_order_id()

    def _setup_request_body(self) -> None:
        if self.body is not None:
            return

        order_bodies = {
            Implementation.STANDARD: {
                Version.V1: StandardV1OrderBody,
            },
            Implementation.UBER: {
                Version.V2: UberV2OrderBody,
            },
        }

        assert self.vendor_info is not None
        assert self.store_id is not None
        assert self.order_id is not None
        try:
            self.body = json.dumps(
                asdict(
                    order_bodies[self.vendor_info.implementation][
                        self.vendor_info.version
                    ](self.store_id, self.order_id)
                )
            )
        except KeyError:
            raise RequestBodyNotImplementedException(
                f"Request body for request 'OrderRequest', implementation '{self.vendor_info.implementation}' and version '{self.vendor_info.version}' cannot be found."
            )


@dataclass
class Release(Request):
    """Class used for order release api calls.

    Fields:
        store_id: Store id needed for url and request_body.
        order_id: Order id needed for request_body.
    """

    store_id: Optional[str] = None
    order_id: Optional[str] = None
    vendor_implementations: Optional[dict[Vendor, int]] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self._setup_store_id()
        self._setup_release_url()
        self._setup_order_id()
        self._setup_request_body()

    def _setup_vendor_implementations(self) -> None:
        if self.vendor_implementations is not None:
            return

        self.vendor_implementations = {
            Vendor.DOORDASH: 9020,
            Vendor.UBEREATS: 9002,
            Vendor.GRUBHUB: 9026,
            Vendor.POSTMATES: 9034,
            Vendor.SKIPTHEDISHES: 9012,
        }

    def _setup_routes(self) -> None:
        if self.routes is not None:
            return

        self.routes = {
            Environment.PERF: "/{version}/vendors/{vendor}/order/release",
            Environment.ALB: "/{version}/orders/release/{vendor}/{market}/{store_id}",
            Environment.NLB: "/{version}/orders/release/{vendor}/{market}/{store_id}",
        }

    def _setup_store_id(self) -> None:
        """Generates random store id if not given."""
        if self.store_id is not None:
            return

        assert self.vendor_info is not None
        self.store_id = utils.get_random_store_id(self.vendor_info.market)
        if self.vendor_info.uses_store_uuid:
            self.store_id = utils.convert_store_id_to_store_uuid(self.store_id)

    def _setup_release_url(self) -> None:
        """Sets up the url for this request, if not given."""
        assert self.store_id is not None
        self._setup_url(store_id=self.store_id)

    def _setup_order_id(self) -> None:
        """Generates random order id if not given."""
        if self.order_id is None:
            self.order_id = utils.get_random_order_id()

    def _setup_request_body(self) -> None:
        if self.body is not None:
            return

        release_bodies = {
            Implementation.STANDARD: {
                Version.V1: StandarV1ReleaseBody,
            },
            Implementation.UBER: {
                Version.V2: UberV2ReleaseBody,
            },
        }

        assert self.vendor_info is not None
        assert self.store_id is not None
        assert self.order_id is not None
        try:
            self.body = json.dumps(
                asdict(
                    release_bodies[self.vendor_info.implementation][
                        self.vendor_info.version
                    ](self.store_id, self.order_id)
                )
            )
        except KeyError:
            raise RequestBodyNotImplementedException(
                f"Request body for request 'ReleaseRequest', implementation '{self.vendor_info.implementation}' and version '{self.vendor_info.version}' cannot be found."
            )


@dataclass
class TokenGeneration(Request):
    """Class used for token generation api calls."""

    def __post_init__(self) -> None:
        super().__post_init__()
        self._setup_token_generation_url()
        self._setup_request_body()

    def _setup_vendor_info(self) -> None:
        """Overrides base method. Every vendor has tokengeneration.
        Gets random vendor if not given.
        """
        if self.vendor_info is None:
            self.vendor_info = utils.get_random_vendor_info(Vendor)

    def _setup_vendor_implementations(self) -> None:
        """Overrides base class's method. No need for implementations,
        every vendor has tokengeneration.
        """

    def _setup_routes(self) -> None:
        """Overrides base class's method. No need for routes,
        _setup_token_generation_url takes care of everything.
        """

    def _setup_token_generation_url(self) -> None:
        """Sets up the url for this request, if not given."""
        if self.url is not None:
            return

        assert self.base_urls is not None
        assert self.vendor_info is not None
        base_url = self.base_urls[Environment.PERF]
        self.url = f"{base_url}/security/auth/token"
        if self.vendor_info.implementation is Implementation.UBER:
            self.url = f"{base_url}/v1/vendor/authentication"

    def _setup_request_headers(self) -> None:
        if self.headers is not None:
            return

        assert self.vendor_info is not None
        content_type = "application/x-www-form-urlencoded"
        if self.vendor_info.implementation is Implementation.UBER:
            content_type = "application/json"

        self.headers = {
            "Content-Type": content_type,
            "mcd-clientid": self.vendor_info.client_id,
            "mcd-marketid": f"{self.vendor_info.market}",
            "Authorization": self.vendor_info.basic_token,
        }

    def _setup_request_body(self) -> None:
        if self.body is not None:
            return

        assert self.vendor_info is not None
        self.body = "grantType=client_credentials"
        if self.vendor_info.implementation is Implementation.UBER:
            self.body = '{"username":"************","password":"************"}'
