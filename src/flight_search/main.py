import argparse
import csv
import datetime as dt
import json
from dataclasses import asdict
from decimal import Decimal
from typing import Any, Generator

from flight_search.constraints import SearchConstraints, TripConstraints
from flight_search.entities import FlightDetails, Trip, bags_allowed, total_price
from flight_search.search import search_trips

TS_FORMAT = "%Y-%m-%dT%H:%M:%S"


class MalformedInput(ValueError):
    pass


def record_to_flight(record: dict) -> FlightDetails:
    # Input control happens here
    try:
        if record["origin"] == record["destination"]:
            raise MalformedInput(
                f"Origin and destination airports are the same: {record['origin']}, {record['destination']}"
            )
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
    except KeyError as ex:
        raise MalformedInput from ex


def flight_to_record(data: list[tuple[str, Any]]) -> dict:
    return {
        key: val.strftime(TS_FORMAT) if isinstance(val, dt.datetime) else val
        for key, val in data
    }


def serialize_trip(trip: Trip) -> dict:
    return {
        "flights": [asdict(flight, dict_factory=flight_to_record) for flight in trip],
        "bags_allowed": bags_allowed(trip),
        "bags_count": trip.required_bags,
        "origin": trip.origin,
        "destination": trip.destination,
        "total_price": total_price(trip, trip.required_bags),
        "travel_time": trip.travel_time,
    }


def load_flight_details(filename: str) -> Generator[FlightDetails, None, None]:
    with open(filename, "r") as fh:
        yield from map(record_to_flight, csv.DictReader(fh))


def _build_constraints(
    args: argparse.Namespace, origin: str, destination: str
) -> SearchConstraints:
    return SearchConstraints(
        origin=origin,
        destination=destination,
        required_bags=args.bags,
        min_layover=dt.timedelta(hours=args.min_layover),
        max_layover=dt.timedelta(hours=args.max_layover),
    )


def build_constraints(args: argparse.Namespace) -> TripConstraints:

    dep = _build_constraints(args, args.origin, args.destination)
    ret = (
        _build_constraints(args, args.destination, args.origin)
        if args.roundtrip
        else None
    )
    return TripConstraints(dep, ret)


class TripEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dt.timedelta):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def main(args: argparse.Namespace) -> None:
    """
    Main function of the app. Takes care of loading data & configuration from file & args,
    running the search algorithm, formatting the resulting trips and printing them to the
    console
    """
    unsorted_trips = search_trips(
        load_flight_details(args.filename), build_constraints(args)
    )
    # sort by total price as per requirement and by departure time for convenience
    sorting_key_fn = lambda trip: (
        total_price(trip, trip.required_bags),
        trip.departure,
    )
    output = json.dumps(
        [serialize_trip(trip) for trip in sorted(unsorted_trips, key=sorting_key_fn)],
        cls=TripEncoder,
        indent=4,
    )
    print(output)


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
