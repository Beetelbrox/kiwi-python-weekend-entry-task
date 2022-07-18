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

    def __init__(self, flights: list[FlightDetails]) -> None:
        if not flights:
            raise ValueError("Flight combination must contain at least 1 flight")

        self._flights: list[FlightDetails] = flights
        self.visited_airports = set()
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
    def origin(self) -> str:
        return self.first.origin

    @property
    def destination(self) -> str:
        return self.last.destination

    @property
    def bags_allowed(self) -> str:
        return min(flight.bags_allowed for flight in self._flights)
    
    def total_price(self, num_bags) -> str:
        return sum(
            flight.bag_price * num_bags + flight.base_price
            for flight in self._flights
        )
    
    @property
    def travel_time(self) -> dt.timedelta:
        return self.last.arrival - self.first.departure
        

    def __len__(self) -> int:
        return len(self._flights)

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from self._flights

    def add_leg(self, flight: FlightDetails) -> "FlightCombination":
        return FlightCombination([*self._flights, flight])

    def join(self, other: "FlightCombination") -> "FlightCombination":
        return FlightCombination([*self._flights, *other._flights])
