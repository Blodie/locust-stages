import logging
from cmath import pi, sin
from datetime import datetime
from math import ceil
from typing import Any, Callable, Mapping, Optional

from locust import LoadTestShape, stats, events

import tasks
from config import DEFAULT_RAMPUP, STAGES, TASKS
from stage import Stage
from user import User

TEST_START_TIME: datetime = datetime.now()


@events.init.add_listener
def on_test_start(*args: Any, **kwargs: Any):
    """This runs once before testing begins."""
    original_print_method = stats.print_stats

    def custom_locust_print(stats: Mapping[str, Any], current: bool = True) -> None:
        """Extend locust's print stats method with extra timestamps."""
        logging.info(f"Started at: {TEST_START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"Test duration: {datetime.now() - TEST_START_TIME}")
        original_print_method(stats, current)

    stats.print_stats = custom_locust_print


class WebsiteTestUser(User):
    """Represents a user during a loadtest."""

    tasks: list[Callable[[User], None]] = [
        task
        for sublist in [
            [getattr(tasks, task_name)] * weight for task_name, weight in TASKS
        ]
        for task in sublist
    ]


class LoadtestStageHandler(LoadTestShape):
    """Makes it so the loadtest calls the tick() function around every second
    which determines how many users should be running at a given time.

    Fields:
        `_current_stage_index (int)`: Which stage from config.STAGES are we currently at.
        `_current_stage (Stage)`: Current stage.
        `_previous_stage (Stage)`: Previous stage.
    """

    current_stage_index: int = 0
    current_stage: Stage = STAGES[0]
    previous_stage: Stage = Stage(0, 1, 0)

    @property
    def progress(self) -> float:
        return self.get_run_time() / self.current_stage.minutes_to_reach_target / 60

    @property
    def avg_response_time(self) -> float:
        if self.runner.stats.total.avg_response_time > 0:
            return self.runner.stats.total.avg_response_time / 1000
        return 0.5

    @property
    def min_users(self) -> float:
        return self.avg_response_time * self.previous_stage.target_request_per_sec

    @property
    def max_users(self) -> float:
        return self.avg_response_time * (
            self.current_stage.target_request_per_sec
            - self.previous_stage.target_request_per_sec
        )

    def begin_next_stage(self) -> None:
        self.previous_stage = self.current_stage
        self.current_stage_index += 1
        self.current_stage = STAGES[self.current_stage_index]
        self.reset_time()

    def tick(self) -> Optional[tuple[int, float]]:
        """This method is called by locust every second or so, and it determines how many users
        should locust be running with at any given time.

        First we check if current stage finished, if so, we begin next stage.
        If there is no next stage we exit the loadtest. If there is a next stage
        then we commence it and keep calculating how many users should the loadtest be running with.

        Imagine a 2d coordinate system. X axis represents time, Y axis represents
        requests per second. Previous stage and current stage are 2 points in this
        system. Their `minutes_to_reach_target` and `target_requests_per_sec` are their
        X and Y coordinates. We return the user count so they correspond with a specific
        sinus function's points in the system. This makes it so the line between 2 points
        is not linear, rather it has a curve, and whether that curve is convex or concave,
        and to what extent, can be determined by the `current_stage`'s `curve` field.

        I made a tool that makes it easier to understand how this function works by visualizing it:
        https://editor.p5js.org/kobekojo/sketches/O574TAgnv
        """

        if self.progress >= 1:
            try:
                self.begin_next_stage()
            except IndexError:
                # No more stages, stop the test.
                return None

        user_count = ceil(
            self.max_users
            * sin(self.progress * pi / 2).real ** self.current_stage.curve
            + self.min_users
        )
        return (user_count, DEFAULT_RAMPUP)
