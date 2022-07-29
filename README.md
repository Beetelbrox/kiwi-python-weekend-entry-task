## Description
This is a solution for Kiwi's Python Weekend entry task. In this task we must write a python script/module/package, that for a given flight data in a form of csv file, prints out a structured list of all flight combinations for a selected route between airports A -> B, sorted by the final price for the trip.

## Requirements
In order to leverage some of the new typing syntax this script only works with python >= 3.10

## Running the script
In order to run the script, from the root of the repostirory run the following comand:
```shell
python -m flight_search.main <csv_path> <origin> <destination>
```
This will output the list of valid trips in the specified format, ordered by price in ascending order, to the standardard output.

### Options
We have implemented the suggested options as well as several extra ones based on the available flight data. In order to see a list of the options available you can run the following command:
```shell
python -m flight_search.main --help
```

Here's a snippet of all the options available:
```shell
usage: main.py [-h] [-b BAGS] [-r] [--min-layover MIN_LAYOVER] [--max-layover MAX_LAYOVER] [-p MAX_PRICE] [-c MAX_CONNECTIONS] [--departure-date DEPARTURE_DATE] [--return-date RETURN_DATE]
               file origin destination

positional arguments:
  file                  Path of the flights csv file.
  origin                IATA 3-letter code of the origin airport.
  destination           IATA 3-letter code of the destination airport.

options:
  -h, --help            show this help message and exit
  -b BAGS, --bags BAGS  Number of required bags.
  -r, --return          Return flight.
  --min-layover MIN_LAYOVER
                        Minimum layover between flights in the same route, in hours.
  --max-layover MAX_LAYOVER
                        Maximum layover between flights in the same route, in hours.
  -p MAX_PRICE, --max-price MAX_PRICE
                        Maximum trip price allowed.
  -c MAX_CONNECTIONS, --max-connections MAX_CONNECTIONS
                        Maximum amount of connections allowed.
  --departure-date DEPARTURE_DATE
                        Desired departure date (YYYY-MM-DD).
  --return-date RETURN_DATE
                        Desired return date (YYYY-MM-DD).
```
You can mix and match them to narrow the search results.

### Assumptions made
We have made the following choices with regards to the options and the results displayed:
 * All options except for departure & return date are shared by both departing & returning trips. Eg there's no support for a different amount
 of bags on the return flight
 * If a trip is a roundtrip, The output will display as destination the origin airport, not the destination of the departing flight. Eg for the trip `AGP -> DCA -> AGP` the output will display origin & return `AGP`.

## Implementation
In our solution we've modelled the flights & airports as a directed multigraph where nodes are airports and edges are flights between two airports. The problem is then reduced to calculating all simple paths between the origin and destination nodes.

### Search
In order to find all simple paths we've used a DFS-based backtracking search. DFS was chosen over BFS because in our type of graph (few nodes with large out-degree) it requires holding less nodes in memory at the same time. In order to reduce the search space at each traversal step and when loading flights we apply the constraints specified by the user (pricing, number of bags, etc), discarding any flight that doesn't meet them or that would make the overall combination not meet them.

### Constraints
We've implemented a basic rule engine in `constraints.py` that we use to prune branches during the search. This allows us to add new search constraints without having to modify the search code itself by just adding a new predicates to `is_flight_elegible`, `is_combination_elegible` and `is_trip_elegible`. Further abstractions could be introduced here to avoid spamming functions but for our use case it does the trick.

### Input validation
All interactions with the external world are managed in the `main.py` module. We check for malformed records & wrong types, as well as inconsistencies in the data like flights with the same origin and destination and negative number of bags.

## Testing
We've added a reduced suite of unit tests for critical parts of the search. Examples have been evaluated via visual inspection.
