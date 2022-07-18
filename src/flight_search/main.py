import argparse
import csv
import datetime as dt
from dataclasses import asdict
from decimal import Decimal
from typing import Generator, Iterable, Optional
from .search import SearchConstraints, find_combinations
from .flights import FlightCombination, FlightDetails

TS_FORMAT = "%Y-%m-%dT%H:%M:%S"

class MalformedInput(ValueError):
    pass

def record_to_flight(record: dict) -> FlightDetails:
    if record["origin"] == record["destination"]:
        raise MalformedInput()
    return FlightDetails(
        flight_no=record["flight_no"],
        origin=record["origin"],
        destination=record["destination"],
        departure=dt.datetime.strptime(record["departure"], TS_FORMAT),
        arrival=dt.datetime.strptime(record["arrival"], TS_FORMAT),
        base_price=Decimal(record["base_price"]),
        bag_price=Decimal(record["bag_price"]),
        bags_allowed=int(record["bags_allowed"]),
    )

def flight_to_record(flight: FlightDetails) -> dict:
    return {
        "flight_no": flight.flight_no,
        "origin": flight.origin,
        "destination": flight.destination,
        "departure": flight.departure.strftime(TS_FORMAT),
        "arrival": flight.arrival.strftime(TS_FORMAT),
        "base_price": flight.base_price,
        "bag_price": flight.bag_price,
        "bags_allowed": flight.bags_allowed
    },

def load_flight_details(filename: str) -> Generator[FlightDetails, None, None]:
    with open(filename, "r") as istream:
        yield from map(record_to_flight, csv.DictReader(istream))



def serialize_combination(combination: FlightCombination) -> dict:
    return {
        "flights": [asdict(flight) for flight in combination],
        "bags_allowed": combination.bags_allowed,
        "destination": combination.destination,
        "origin": combination.origin,
        "total_price": combination.total_price(),
        "travel_time": combination.travel_time,
    }
    

def search_flights(flights, origin, destination, constraints) -> list:
    return [
        serialize_combination(combination)
        for combination in find_combinations(
            flights, origin, destination, constraints
        )
    ]


def main(args):
    flights: Iterable[FlightDetails] = load_flight_details(args.filename)
    constraints: SearchConstraints = SearchConstraints(
        required_bags=args.bags,
        min_layover=args.min_layover,
        max_layover=args.max_layover,
    )




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("origin")
    parser.add_argument("destination")
    parser.add_argument("-b", "--bags", type=int, default=0)
    parser.add_argument("-r", "--return", action="store_true", dest="roundtrip")
    parser.add_argument("--min-layover", type=int, default=1)
    parser.add_argument("--max-layover", type=int, default=6)
    main(parser.parse_args())
