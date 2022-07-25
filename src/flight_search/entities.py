import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class FlightDetails:
    """Container for the information related to a specific flight"""

    flight_no: str
    origin: str
    destination: str
    departure: dt.datetime
    arrival: dt.datetime
    base_price: Decimal
    bag_price: Decimal
    bags_allowed: int


class FlightCombination:
    """
    Container representing a combination of flights
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
        return self._flights[-1]

    @property
    def first(self) -> FlightDetails:
        return self._flights[0]

    @property
    def destination(self) -> str:
        return self.last.destination

    @property
    def connections(self) -> int:
        return len(self._flights) - 1

    def __add__(self, flight: FlightDetails) -> "FlightCombination":
        return FlightCombination(*self._flights, flight)
    
    def __len__(self) -> int:
        return len(self._flights)

    @property
    def travel_time(self) -> dt.timedelta:
        return self.last.arrival - self.first.departure

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from self._flights


class NullFlightCombination:
    @property
    def travel_time(self) -> dt.timedelta:
        return dt.timedelta(0)

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from []

    def __bool__(self) -> bool:
        return False


@dataclass
class Trip:
    departing: FlightCombination
    returning: FlightCombination | NullFlightCombination
    required_bags: int

    @property
    def origin(self) -> str:
        return self.departing.first.origin

    @property
    def destination(self) -> str:
        return (self.returning or self.departing).destination

    @property
    def departure(self) -> dt.datetime:
        return self.departing.first.departure

    @property
    def travel_time(self) -> dt.timedelta:
        return self.departing.travel_time + self.returning.travel_time

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from self.departing
        yield from self.returning


def total_price(flights: Iterable[FlightDetails], bags: int) -> Decimal:
    return sum(flight.total_price(bags) for flight in flights)


def bags_allowed(flights: Iterable[FlightDetails]) -> int:
    return min(flight.bags_allowed for flight in flights)
