"""Module for storing all enums."""

from enum import Enum, auto


class ParentEnum(Enum):
    def __str__(self):
        return self.name.lower()

    def __repr__(self) -> str:
        return self.name


class Environment(ParentEnum):
    PERF = auto()
    ALB = auto()
    NLB = auto()


class Version(ParentEnum):
    V1 = auto()
    V2 = auto()


class Implementation(ParentEnum):
    STANDARD = auto()
    UBER = auto()
    DELIVERYHERO = auto()


class Market(ParentEnum):
    US = auto()
    CA = auto()


class Vendor(ParentEnum):
    DOORDASH = auto()
    UBEREATS = auto()
    GRUBHUB = auto()
    POSTMATES = auto()
    SKIPTHEDISHES = auto()
