"""Module used for the configuration of the loadtest."""

from locust import stats

from stage import Stage
from enums import Environment

ENVIRONMENT: Environment = Environment.PERF
"""Environment that will be used throughout the loadtesting."""

TASKS: list[tuple[str, int]] = [
    ("token_generation", 0),
    ("get_menu", 0),
    ("order", 1),
    ("release", 1),
]
"""Name(str) and weight(int) of the tasks to use during the loadtest. 0 weight means
the task will not be run. Task name can only be name of methods found in tasks.py.
"""

STAGES: list[Stage] = [
    Stage(target_request_per_sec=40, minutes_to_reach_target=5, curve=2),
    Stage(target_request_per_sec=40, minutes_to_reach_target=2, curve=0),
    Stage(target_request_per_sec=0, minutes_to_reach_target=5, curve=4),
]
"""Stages of the loadtest we want to run."""

DEFAULT_RAMPUP: int = 40
"""If a stage's `curve` is 0, this value will be used to linearly increase/decrease
the user count until the desired `target_request_per_sec` is reached.
"""

LOG_RESPONSE: bool = False
"""Set to `True` if we want to see the response bodies logged to the console."""

RELEASE_WAIT_TIME_SEC: int = 180
"""How much time needs to pass before an order can be released."""

USE_GLOBAL_AUTH_TOKENS: bool = False
"""If true, global bearer tokens will be used for every locust task,
and will only be generated again if expired and needed,
if false, global bearer tokens will not be used, a new bearer token 
will be generated for each locust task if needed (currently only needed on Environment.PERF)."""

stats.CONSOLE_STATS_INTERVAL_SEC = 10
"""How often locust reprints stats on the console while running."""
