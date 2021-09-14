"""All the logic behind tpo requests."""

from datetime import datetime
from json.decoder import JSONDecodeError
from queue import Empty, Queue
from typing import Any

from locust.clients import ResponseContextManager
from locust import HttpUser

from db import BEARER_PLACE_HOLDER
from config import (
    ENVIRONMENT,
    USE_GLOBAL_AUTH_TOKENS,
)
from enums import Environment, Implementation
from requests_tpo import (
    Request,
    TokenGeneration,
)


class RequestQueue(Queue[tuple[Request, datetime]]):
    """A queue of [Request, datetime] tuples.

    Extended the built in Queue class to have threadsafe peek functionality.
    """

    def peek(self) -> datetime:
        """Returns the queue's first element's datetime part."""
        with self.mutex:
            try:
                return list(self.queue)[0][1]
            except IndexError:
                raise Empty

    def dequeue(self) -> Request:
        """Returns the queue's first element's Request part."""
        return self.get_nowait()[0]


class User(HttpUser):
    """Abstract class containing the necessary methods for api calls.

    Fields:
        `abstract (bool)`: `True` - Indicates to locust that this is an abstract class
        and it shouldn't try to create users from it.
        `host (str)`: "" - Used by locust to generate urls in self.client.request() method,
        but since our baseurls contain variable data it is easier if we generate the whole url ourselves,
        but it is still mandatory to not be null for locust to work, so we give it a default value of empty string.
        `release_queue (RequestQueue)`: Contains the release requests
        that need to be called after some time has passed.
    """

    abstract: bool = True
    host: str = ""
    release_queue: RequestQueue = RequestQueue()

    def send_request(self, request: Request, recursed: bool = False) -> dict[str, Any]:
        """Sends a request with data found in given `request`.

        First checks if a valid token is necessary for the request to be sent, if so,
        generates one. Then sends the request. From the response
        we check if the bearer token is invalid. If so, generate a new one and
        send the original request again. Then we check if we got back valid json data.
        Finally we check if the request was a failure.

        Args:
            `request (Request)`: `Request` that contains the request data.
            `recursed (bool, optional)`: Used for when the bearer token expired, and we need
            to resend the original request. Stops the method from recursing forever. Defaults to False.

        Returns:
            `dict[str, Any]`: The response body if it was a valid json, otherwise the response text wrapped in a dict.
        """
        if self._is_valid_bearer_token_necessary(request):
            self._generate_token_for_request(request)

        assert request.vendor_info is not None
        assert request.success_status_codes is not None
        with self.client.request(
            url=request.url,
            method=request.method,
            headers=request.headers,
            data=request.body,
            name=request.locust_display_name,
            catch_response=True,
        ) as response:
            assert type(response) is ResponseContextManager
            response.success()

            if not recursed and self._is_token_invalid(response, request):
                self._generate_token_for_request(request)
                return self.send_request(request, True)

            body = self._parse_response_body(response)
            if self._was_request_a_failure(request, response.status_code, body):
                response.failure(body)

            return body

    def _is_valid_bearer_token_necessary(self, request: Request) -> bool:
        """Checks if valid bearer token is necessary for `request`.

        `TokenGeneration` doesn't use bearer tokens. A valid one is only
        necessary on `Environment.PERF` if the request only has the
        default placeholder as its bearer token.
        """
        return (
            type(request) is not TokenGeneration
            and ENVIRONMENT is Environment.PERF
            and request.bearer_token is BEARER_PLACE_HOLDER
        )

    def _generate_token_for_request(self, request: Request) -> None:
        """Generates a valid bearer token for the given request.

        Args:
            `request (Request)`: Request for which to generate a token for.
        """
        assert request.vendor_info is not None
        token_generation_request = TokenGeneration(vendor_info=request.vendor_info)

        result = self.send_request(token_generation_request, True)
        token = f'Bearer {result.get("token")}'
        request.bearer_token = token
        if USE_GLOBAL_AUTH_TOKENS:
            request.vendor_info.bearer_token = token

    def _parse_response_body(self, response: ResponseContextManager) -> dict[str, Any]:
        """Tries to parse `response.text` to json and return it.

        If it fails, marks the `reponse` as a failure,
        then returns the `response.text` wrapped in a dict like so:
        {"code": `response.status_code`, "text": `response.text`}

        Args:
            `response (ResponseContextManager)`: Response object whose body we try to parse.

        Returns:
            `dict[str, Any]`: Response's body parsed as json, or `response.text` wrapped in a dict.
        """
        try:
            return response.json()
        except JSONDecodeError:
            result = {"code": response.status_code, "text": response.text}
            response.failure(result)
            return result

    def _was_request_a_failure(
        self,
        request: Request,
        status_code: int,
        result: dict[str, Any],
    ) -> bool:
        """Checks if `request` was a failure.

        In the case of `TokenGeneration` if the response body
        doesn't have a `token` attribute, the `request` was a failure.
        In any other case, if the response's status code is not among
        the request's success_status_codes list, the request was a failure.

        Args:
            `request (Request)`: The `Request` that was sent.
            `status_code (int)`: Response's status code.
            `result (dict[str, Any])`: Response's body.

        Returns:
            `bool`: Whether the request was a failure or not.
        """
        assert request.success_status_codes is not None
        return (
            type(request) is TokenGeneration
            and result.get("token") is None
            or status_code not in request.success_status_codes
        )

    def _is_token_invalid(
        self, response: ResponseContextManager, request: Request
    ) -> bool:
        """Checks if the bearer token used in the request is expired.

        `Tokengeneration` doesn't use bearer token so it can't be expired in that case.
        On `Standard` the response body will contain text like token is expired or
        invalid and that means expired token.
        On uber the response body will be null and the status code will be 500 if
        it's expired.

        Args:
            `response (ResponseContextManager)`: The response from which we can deduce if the token expired or not.
            `request (Request)`: The request for which we sent the request.

        Returns:
            `bool`: Whether the token expired or not.
        """
        assert request.vendor_info is not None
        is_token_expired = response.text is not None and (
            "Token is expired" in response.text
            or "Invalid authorization token" in response.text
        )
        is_uber_token_expired = (
            request.vendor_info.implementation is Implementation.UBER
            and response.status_code == 500
            and response.text is None
        )
        return type(request) is not TokenGeneration and (
            is_token_expired or is_uber_token_expired
        )
