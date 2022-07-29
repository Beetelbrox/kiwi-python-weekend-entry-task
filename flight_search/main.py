"""Entrypoint for the app, including all I/O & serde logic"""

import argparse
import csv
import datetime as dt
import json
from dataclasses import asdict
from decimal import Decimal
from typing import Any, Generator

from .constraints import SearchConstraints, TripConstraints
from .entities import FlightDetails, Trip, num_bags_allowed, total_price
from .search import search_trips

TS_FORMAT = "%Y-%m-%dT%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class MalformedInput(ValueError):
    """Exception thrown when malformed input is passed"""


def record_to_flight(record: dict) -> FlightDetails:
    """
    Converts a record into a FlightDetails object. All FlightDetails instances
    are constructed using this method so we validate input here so we don't need to
    keep checking values everywhere else. String fields are not validated as we don't
    really care if the origin & dest are valid IATA 3-letter codes for the purpose
    of this exercise.
    Normally this would be done with a runtime validation library like
    Pydantic which provides most of the boilerplate.
    """
    try:
        if record["origin"] == record["destination"]:
            raise MalformedInput(
                # pylint: disable=line-too-long
                f"Origin and destination airports are the same: {record['origin']}, {record['destination']}"
            )
        if (bags_allowed := int(record["bags_allowed"])) < 0:
            raise MalformedInput(
                f"Negative amount of allowed bags received: {bags_allowed}"
            )

        return FlightDetails(
            flight_no=record["flight_no"],
            origin=record["origin"],
            destination=record["destination"],
            departure=dt.datetime.strptime(record["departure"], TS_FORMAT),
            arrival=dt.datetime.strptime(record["arrival"], TS_FORMAT),
            base_price=Decimal(record["base_price"]),
            bag_price=Decimal(record["bag_price"]),
            bags_allowed=bags_allowed,
        )
    except KeyError as ex:
        raise MalformedInput from ex


def load_flight_details(filepath: str) -> Generator[FlightDetails, None, None]:
    """
    Loads available flight details from CSV,
    parsing the records into FlightDetails instances.
    """
    with open(filepath, "r", encoding="utf-8") as fhandle:
        yield from map(record_to_flight, csv.DictReader(fhandle))


def serialize_trip(trip: Trip) -> dict:
    """
    Serializes a trip object into a record dict
    with the required schema
    """
    return {
        "flights": [asdict(flight) for flight in trip],
        "bags_allowed": num_bags_allowed(trip),
        "bags_count": trip.required_bags,
        "destination": trip.destination,
        "origin": trip.origin,
        "total_price": total_price(trip, trip.required_bags),
        "travel_time": trip.travel_time,
    }


def _parse_date(date: str) -> dt.date | None:
    return dt.datetime.strptime(date, DATE_FORMAT).date() if date else None


def _build_constraints(
    args: argparse.Namespace, origin: str, destination: str, departure_date: str | None
) -> SearchConstraints:
    return SearchConstraints(
        origin=origin,
        destination=destination,
        required_bags=args.bags,
        min_layover=dt.timedelta(hours=args.min_layover),
        max_layover=dt.timedelta(hours=args.max_layover),
        max_price=args.max_price,
        max_connections=args.max_connections,
        departure_date=_parse_date(departure_date),
    )


def build_constraints(args: argparse.Namespace) -> TripConstraints:
    """
    Given an args object, construct a trip constraints object to be used in the search
    """

    if args.return_date is not None and not args.roundtrip:
        raise MalformedInput("Specified return date on a one-way only trip.")

    dep = _build_constraints(args, args.origin, args.destination, args.departure_date)
    ret = (
        _build_constraints(args, args.destination, args.origin, args.return_date)
        if args.roundtrip
        else None
    )
    return TripConstraints(dep, ret)


class TripEncoder(json.JSONEncoder):
    """Custom encoder for serializing the Trip record into JSON"""

    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, dt.timedelta):
            return str(o)
        if isinstance(o, dt.datetime):
            return o.strftime(TS_FORMAT)
        return json.JSONEncoder.default(self, o)


def sorting_key_fn(trip: Trip) -> tuple[Decimal, Any]:
    """Function to be used when sorting the list of trips"""
    return (total_price(trip, trip.required_bags), trip.departure)


def main(args: argparse.Namespace) -> None:
    """
    Main function of the app. Takes care of loading data & configuration from file & args,
    running the search algorithm, formatting the resulting trips and printing them to the
    console
    """
    unsorted_trips = search_trips(
        load_flight_details(args.file), build_constraints(args)
    )
    # Pretty dump the JSON and print it
    print(
        json.dumps(
            [
                serialize_trip(trip)
                for trip in sorted(unsorted_trips, key=sorting_key_fn)
            ],
            cls=TripEncoder,
            indent=4,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path of the flights csv file.")
    parser.add_argument("origin", help="IATA 3-letter code of the origin airport.")
    parser.add_argument(
        "destination", help="IATA 3-letter code of the destination airport."
    )
    parser.add_argument(
        "-b", "--bags", type=int, default=0, help="Number of required bags."
    )
    parser.add_argument(
        "-r", "--return", action="store_true", dest="roundtrip", help="Return flight."
    )
    parser.add_argument(
        "--min-layover",
        type=int,
        default=1,
        help="Minimum layover between flights in the same route, in hours.",
    )
    parser.add_argument(
        "--max-layover",
        type=int,
        default=6,
        help="Maximum layover between flights in the same route, in hours.",
    )
    parser.add_argument(
        "-p", "--max-price", type=Decimal, help="Maximum trip price allowed."
    )
    parser.add_argument(
        "-c",
        "--max-connections",
        type=int,
        help="Maximum amount of connections allowed.",
    )
    parser.add_argument("--departure-date", help="Desired departure date (YYYY-MM-DD).")
    parser.add_argument("--return-date", help="Desired return date (YYYY-MM-DD).")
    main(parser.parse_args())
