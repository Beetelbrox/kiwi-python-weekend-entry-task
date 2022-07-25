"""
Module containing a crude rule engine for pruning the search space
while generating the list of elegible flights.
"""

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from flight_search.entities import FlightCombination, FlightDetails, Trip, total_price


@dataclass
class SearchConstraints:
    """
    Constraints for a flight combination search
    """

    # pylint: disable=too-many-instance-attributes
    origin: str
    destination: str
    required_bags: int = 0
    min_layover: dt.timedelta = dt.timedelta(hours=1)
    max_layover: dt.timedelta = dt.timedelta(hours=6)
    max_price: Decimal | None = None
    max_connections: int | None = None
    departure_date: dt.date | None = None


@dataclass
class TripConstraints:
    """
    Constraints for a trip search.
    May be one-way or roundtrip
    """

    departing: SearchConstraints
    returning: SearchConstraints | None

    @property
    def required_bags(self) -> int:
        """
        Number of required bags for the entire trip.
        Assumes it's the same for both legs
        """
        return self.departing.required_bags

    @property
    def roundtrip(self) -> bool:
        """The trip needs to be a roundtrip"""
        return self.returning is not None

    @property
    def max_price(self) -> Decimal | None:
        """Maximum price for the trip, if any"""
        return self.departing.max_price


def is_flight_within_price_range(
    flight: FlightDetails, constraints: SearchConstraints
) -> bool:
    """Evaluates if the flight is cheaper than the max price constraint, if set."""
    return (
        True
        if constraints.max_price is None  # Explicit check because it can be 0
        else flight.total_price(constraints.required_bags) <= constraints.max_price
    )


def has_a_valid_number_of_connections(
    combination: FlightCombination, constraints: SearchConstraints
) -> bool:
    """Evaluates if a combination has less than the maximum number of connections, if set."""
    return (
        True
        if constraints.max_connections is None  # Explicit check because it can be 0
        else combination.connections <= constraints.max_connections
    )


def is_within_price_range(
    item: FlightCombination | Trip, constraints: SearchConstraints
) -> bool:
    """Evaluate if a flight combination or trip is within price range, if set"""
    return (
        True
        if constraints.max_price is None  # Explicit check because it can be 0
        else total_price(item, constraints.required_bags) <= constraints.max_price
    )


def is_valid_layover(
    inbound: FlightDetails, outbound: FlightDetails, constraints: SearchConstraints
) -> bool:
    """
    Evaluates if the layover between an inbound an outbound flight is within constraints.
    Assumes they both land in the same airport
    """
    layover = outbound.departure - inbound.arrival
    return constraints.min_layover <= layover <= constraints.max_layover


def is_flight_elegible(flight: FlightDetails, constraints: TripConstraints) -> bool:
    """Indicates if a flight satisfies the constraints"""
    return (
        flight.bags_allowed >= constraints.required_bags
        and is_flight_within_price_range(flight, constraints.departing)
    )


def departs_on_requested_date(
    flight: FlightDetails, constraints: SearchConstraints
) -> bool:
    """Evaluates if a flight departs on a specific date"""
    return (
        True
        if not constraints.departure_date
        else flight.departure.date() == constraints.departure_date
    )


def is_combination_elegible(
    combination: FlightCombination, constraints: SearchConstraints
) -> bool:
    """Indicates if a combination satisfies the constraints"""
    return has_a_valid_number_of_connections(
        combination, constraints
    ) and is_within_price_range(combination, constraints)


def is_trip_elegible(trip: Trip, constraints: SearchConstraints) -> bool:
    """Indicates if a trip satisfies the constraints"""
    return is_within_price_range(trip, constraints)
