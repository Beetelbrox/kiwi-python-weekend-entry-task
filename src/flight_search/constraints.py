import datetime as dt
from dataclasses import dataclass

from flight_search.entities import FlightCombination, FlightDetails, Trip


@dataclass
class SearchConstraints:
    origin: str
    destination: str
    required_bags: int
    min_layover: dt.timedelta
    max_layover: dt.timedelta


@dataclass
class TripConstraints:
    departing: SearchConstraints
    returning: SearchConstraints | None

    @property
    def required_bags(self) -> int:
        # Assume that the bag requirement is the same for both legs.
        return self.departing.required_bags



def is_valid_layover(
    inbound: FlightDetails, outbound: FlightDetails, constraints: SearchConstraints
) -> bool:
    layover = outbound.departure - inbound.arrival
    return constraints.min_layover <= layover <= constraints.max_layover


def is_flight_elegible(flight: FlightDetails, constraints: TripConstraints) -> bool:
    return flight.bags_allowed >= constraints.required_bags

def is_combination_elegible(
    combination: FlightCombination, constraints: SearchConstraints
) -> bool:
    return True


def is_trip_elegible(
    combination: FlightCombination, constraints: SearchConstraints
) -> bool:
    return True
