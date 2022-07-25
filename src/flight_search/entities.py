"""Entities & value classes"""

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class FlightDetails:
    """Container for the information related to a specific flight"""

    # pylint: disable=too-many-instance-attributes
    flight_no: str
    origin: str
    destination: str
    departure: dt.datetime
    arrival: dt.datetime
    base_price: Decimal
    bag_price: Decimal
    bags_allowed: int

    def total_price(self, bags: int) -> Decimal:
        """Calcualtes the total price of the flight given a number of bags"""
        return self.base_price + bags * self.bag_price


class FlightCombination:
    """
    A combination of flights between an origin an a destination.
    Contains the list of flights, a set of visited airports for fast
    checks and several utility methods to calculate values from the list of flights.
    This class is not meant to be mutated, adding a flight returns a new instance which
    simplifies & makes the search safer at the expense of some memory.
    """

    def __init__(self, *flights: FlightDetails) -> None:
        if not flights:
            raise ValueError("Flight combination must contain at least 1 flight")
        self._flights: list[FlightDetails] = flights
        self.visited_airports: set = set()
        for flight in flights:
            self.visited_airports.add(flight.origin)
            self.visited_airports.add(flight.destination)

    @property
    def last(self) -> FlightDetails:
        """Last flight in the combination"""
        return self._flights[-1]

    @property
    def first(self) -> FlightDetails:
        """First flight in the combination"""
        return self._flights[0]

    @property
    def destination(self) -> str:
        """Destination of the combination"""
        return self.last.destination

    @property
    def connections(self) -> int:
        """Number of connections between flights in the combination"""
        return len(self._flights) - 1

    def __add__(self, flight: FlightDetails) -> "FlightCombination":
        """
        Produces a new combination with the passed flight
        appended to the current ones
        """
        return FlightCombination(*self._flights, flight)

    def __len__(self) -> int:
        return len(self._flights)

    @property
    def travel_time(self) -> dt.timedelta:
        """Travel time for the combination, including layovers."""
        return self.last.arrival - self.first.departure

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from self._flights


class NullFlightCombination:
    """
    Utility class representing a null combination to avoid
    having to write if statements checking for null return
    trips everywhere
    """

    @property
    def travel_time(self) -> dt.timedelta:
        """Placeholder for travel_time"""
        return dt.timedelta(0)

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from []

    def __bool__(self) -> bool:
        return False


@dataclass
class Trip:
    """
    A trip, consisting of a departing combination of flights
    and potentially a returning one.
    Includes utility methods to calculate aggregates & extract
    specific values directly from the trip.
    """

    departing: FlightCombination
    returning: FlightCombination | NullFlightCombination
    required_bags: int

    @property
    def origin(self) -> str:
        """Origin of the trip"""
        return self.departing.first.origin

    @property
    def destination(self) -> str:
        """Destination of the trip"""
        return (self.returning or self.departing).destination

    @property
    def travel_time(self) -> dt.timedelta:
        """
        Travel time of the trip. Includes layovers, does NOT include
        time between departing & returning combinations.
        """
        return self.departing.travel_time + self.returning.travel_time

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from self.departing
        yield from self.returning


def total_price(flights: Iterable[FlightDetails], bags: int) -> Decimal:
    """
    Given an iterable collection of flights and a number of bags,
    calculates the total associated cost
    """
    return sum(flight.total_price(bags) for flight in flights)


def num_bags_allowed(flights: Iterable[FlightDetails]) -> int:
    """
    Given an iterable collection of flights, returns the overall
    number of bags allowed by grabbing the most restrictive bag allowance.
    """
    return min(flight.bags_allowed for flight in flights)
