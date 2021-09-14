"""Module for all the tasks. 

Disclaimer: Do not put decorators to these methods
because that fucks locust up for some reason, and you will not notice that
it is fucked up until its too late and you had lost your sanity.
"""

import logging
from queue import Empty
from datetime import datetime
from typing import Any

from config import LOG_RESPONSE, RELEASE_WAIT_TIME_SEC
from requests_tpo import GetMenu, Order, Release, TokenGeneration
from user import User


def token_generation(user: User) -> None:
    """Task for testing token generation api calls."""
    response = user.send_request(TokenGeneration(), True)

    if LOG_RESPONSE:
        logging.info(response)


def get_menu(user: User) -> None:
    """Task for testing get menu api calls."""
    response = user.send_request(GetMenu())

    if LOG_RESPONSE:
        logging.info(response)


def order(user: User) -> None:
    """Task for testing order api calls. Once completed
    generates a release request with the data from the order request
    and puts in in `release_queue` for later calls
    """
    order_request = Order()
    response = user.send_request(order_request)

    user.release_queue.put(
        (
            Release(
                vendor_info=order_request.vendor_info,
                store_id=order_request.store_id,
                order_id=order_request.order_id,
            ),
            datetime.now(),
        )
    )

    if LOG_RESPONSE:
        logging.info(response)


def release(user: User) -> None:
    """Task for testing release order api calls. If enough time passed
    since the order call, sends the release request.
    """
    response: dict[str, Any] = {"locust": "No Release request found."}
    try:
        order_time = user.release_queue.peek()
        duration = datetime.now() - order_time
        if duration.total_seconds() >= RELEASE_WAIT_TIME_SEC:
            release_request = user.release_queue.dequeue()
            response = user.send_request(release_request)
    except Empty:
        # If release queue empty go ahead with another task
        pass

    if LOG_RESPONSE:
        logging.info(response)
