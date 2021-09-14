from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    """Represents a loadtest stage.

    Fields:
    `target_request_per_sec`(float): How many req/s there will be at the end of this stage.
    `minutes_to_reach_target`(float): How many mins it takes to reach `target_request_per_sec`
    starting from the previous's stage's `target_request_per_sec`.
    `curve`(float): The shape of the req/s graph (convex or concave). If 0 the loadtest will linearly
    reach `target_request_per_sec` with `config.DEFAULT_RAMPUP` user/sec. Less than 2 means the majority of users will
    be (de)spawned at the beginning of the stage, more than 2 means the majority of users will
    be (de)spawned at the end of the stage. Created a tool so you can kinda visualize how it works:
    https://editor.p5js.org/kobekojo/sketches/O574TAgnv
    """

    target_request_per_sec: float
    minutes_to_reach_target: float
    curve: float = 2

    def __post_init__(self):
        assert self.target_request_per_sec >= 0
        assert self.minutes_to_reach_target > 0
        assert self.curve >= 0
