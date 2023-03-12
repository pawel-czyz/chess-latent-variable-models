"""Parsing the data from PGN into
standardized format.

Note:
    It can be used either as a library
    (e.g., use ``HeadersData`` to parse the data)
    or as a script:

    .. code-block::

       $ python -m morfi.parsing --help

    will print out more information.
"""
import argparse
import gzip
from pathlib import Path
from typing import Optional

import chess.pgn
import pandas as pd
import pydantic


class HeadersData(pydantic.BaseModel):
    """Object storing parsed data."""
    # General event data
    event_name: str
    result: str
    termination: str
    time_control: str

    # Date and time of the event
    date: str
    time: str

    # Data about the white player
    white_name: str
    white_title: Optional[str]
    white_elo: int
    white_elo_diff: Optional[int]

    # Data about the black player
    black_name: str
    black_title: Optional[str]
    black_elo: int
    black_elo_diff: Optional[int]


def parse_game(game) -> HeadersData:
    headers = game.headers

    return HeadersData(
        event_name=headers.get("Event"),
        result=headers.get("Result"),
        termination=headers.get("Termination"),
        date=headers.get("UTCDate"),
        time=headers.get("UTCTime"),
        time_control=headers.get("TimeControl"),
        # White
        white_name=headers.get("White"),
        white_title=headers.get("WhiteTitle"),
        white_elo=headers.get("WhiteElo"),
        white_elo_diff=headers.get("WhiteRatingDiff"),
        # Black
        black_name=headers.get("Black"),
        black_title=headers.get("BlackTitle"),
        black_elo=headers.get("BlackElo"),
        black_elo_diff=headers.get("BlackRatingDiff"),
    )


def parse_pgn(
    filepath: Path, max_games: int = int(1e18), report_each: int = 10_000
) -> tuple[list[HeadersData], list, list]:
    """Parses a PGN file.

    Args:
        filepath: path to the PGN file
        max_games: specified the maximum number of games to be parsed from the file.
          Useful for debugging purposes.
        report_each: controls verbosity of the command

    Returns:
        list of parsed headers
        damaged headers (in the ``chess.pgn`` format,
          so that they can be manually investigated and the command can be debugged)
        exceptions: additional Python exception information (used for debugging),
          paired with damaged headers
    """
    games = []
    damaged_headers = []
    exceptions = []

    with open(filepath) as handle:
        for i in range(max_games):
            if i % report_each == 1:
                print(f"Loading the {i}st game...")

            game = chess.pgn.read_game(handle)
            if game is None:
                break
            else:
                try:
                    games.append(parse_game(game))
                except Exception as e:
                    damaged_headers.append(game.headers)
                    exceptions.append(e)

    return games, damaged_headers, exceptions


def _main() -> None:
    """Creates a simple parser and parses a given PGN file."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "INPUT_PGN",
        type=Path,
        help="Path to the PGN file to be loaded. "
        "Alternatively, it can be a compressed version of the PGN file.",
    )
    parser.add_argument(
        "OUTPUT_CSV", type=Path, help="Path to the output CSV (will be created)."
    )
    parser.add_argument(
        "--max-games",
        type=int,
        default=int(1e18),
        help="If set, maximally the specified number of games will be loaded.",
    )

    args = parser.parse_args()
    games, damaged_headers, exceptions = parse_pgn(
        filepath=args.INPUT_PGN,
        max_games=args.max_games,
    )

    print(f"Loaded {len(games)} games.")
    print(f"Found {len(exceptions)} exceptions:")
    for e, h in zip(exceptions, damaged_headers):
        print(f"   Exception: {e}\t Headers: {h}.")

    print(f"Saving the data to {args.OUTPUT_CSV}...")
    df = pd.DataFrame(map(lambda x: x.dict(), games))
    df.to_csv(args.OUTPUT_CSV, index=False)
    print("Saved. Script run finished.")


if __name__ == "__main__":
    _main()
