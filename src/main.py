import csv

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from hashlib import md5
from typing import Generator, Iterable


class MalformedInput(ValueError):
    pass


class NotTheSameAirport(ValueError):
    pass


def parse_dt(dt_string: str) -> dt.datetime:
    return dt.datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")


@dataclass(frozen=True)
class FlightDetails:
    flight_no: str
    origin: str
    destination: str
    departure: dt.datetime
    arrival: dt.datetime
    base_price: Decimal
    bag_price: Decimal
    bags_allowed: int

    @property
    def id(self) -> str:
        id_components = [
            self.flight_no,
            self.origin,
            self.destination,
            str(self.departure),
            str(self.arrival),
        ]
        return "-".join(id_components)
        # return md5("-".join(id_components).encode()).hexdigest()

    @classmethod
    def from_record(cls, record: dict) -> "FlightDetails":
        if record["origin"] == record["destination"]:
            raise MalformedInput()
        return cls(
            flight_no=record["flight_no"],
            origin=record["origin"],
            destination=record["destination"],
            departure=parse_dt(record["departure"]),
            arrival=parse_dt(record["arrival"]),
            base_price=Decimal(record["base_price"]),
            bag_price=Decimal(record["bag_price"]),
            bags_allowed=int(record["bags_allowed"]),
        )


class FlightCombination:
    """
    Container representing a combination of flights
    """

    def __init__(self, flights: list[FlightDetails] | None) -> None:
        self._flights: list[FlightDetails] = flights or []
        # TODO: Calculate visited airports if flights is passed
        self.visited_airports: set = set()

    @property
    def last(self) -> FlightDetails | None:
        return self._flights[-1] if self._flights else None

    def __len__(self) -> int:
        return len(self._flights)

    def __iter__(self) -> Iterable[FlightDetails]:
        yield from self._flights

    def add_leg(self, flight: FlightDetails) -> None:
        if not self._flights:
            # Add the origin airport to visited airports if
            # we're on the first leg
            self.visited_airports.add(flight.origin)
        elif self.last.destination != flight.origin:
            raise NotTheSameAirport()
        self._flights.append(flight)
        self.visited_airports.add(flight.destination)

    def pop_leg(self) -> None:
        flight: FlightDetails = self._flights.pop()
        self.visited_airports.remove(flight.destination)
        if not self._flights:
            self.visited_airports.remove(flight.origin)

    def __str__(self) -> str:
        return str([flight.id for flight in self._flights])


def is_layover_valid(arrival: dt.datetime, departure: dt.datetime) -> bool:
    return dt.timedelta(hours=1) <= departure - arrival <= dt.timedelta(hours=6)


def get_valid_connecting_flights(
    outbound_flights: dict[str, list[FlightDetails]], inbound: FlightDetails
) -> Generator[FlightDetails, None, None]:
    for outbound in outbound_flights.get(inbound.destination, []):
        if is_layover_valid(inbound.arrival, outbound.departure):
            yield outbound


def find_combinations(
    outbound_flights: dict[str, list[FlightDetails]], origin: str, dest: str
):
    combination: FlightCombination = FlightCombination()
    pending: list[list[FlightDetails]] = [outbound_flights.get(origin, [])]

    while pending:
        if not pending[-1]:
            if len(combination) > 0:
                combination.pop_leg()
            pending.pop()
        else:
            flight: FlightDetails = pending[-1].pop()
            combination.add_leg(flight)

            if flight.destination == dest:
                # Return a copy of the flight sequence to avoid mutability
                # shenanigans
                yield [leg for leg in combination]
                combination.pop_leg()
            else:
                pending.append(
                    [
                        connection
                        for connection in get_valid_connecting_flights(
                            outbound_flights, flight
                        )
                        if connection.destination not in combination.visited_airports
                    ]
                )


def read_flight_details(filename: str) -> Generator[FlightDetails, None, None]:
    with open(filename, "r") as istream:
        yield from map(FlightDetails.from_record, csv.DictReader(istream))


def main():
    # fligths_graph = {}
    ORIGIN = "GXV"
    DESTINATION = "IUT"
    outbound_flights: dict[str, list[FlightDetails]] = {}
    for flight in read_flight_details("example/example2.csv"):
        outbound_flights.setdefault(flight.origin, []).append(flight)

    for combination in find_combinations(outbound_flights, ORIGIN, DESTINATION):
        for flight in combination:
            print(flight.id)
        print()


if __name__ == "__main__":
    main()
