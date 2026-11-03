"""Small helpers for downloading Norwegian cross-border flows from ENTSO-E."""

import pandas as pd
from pathlib import Path
import logging
import time

from requests import RequestException
from entsoe.parsers import parse_crossborder_flows


# These are the nine external borders listed for the five Norwegian bidding zones.
# I keep the zone codes here so the notebook loop stays readable.
NORWEGIAN_CONNECTIONS = {
    "NO1-SE3": ("NO_1", "SE_3"),
    "NO2-DK1": ("NO_2", "DK_1"),
    "NO2-NL": ("NO_2", "NL"),
    "NO2-DE-LU": ("NO_2", "DE_LU"),
    "NO2-GB": ("NO_2", "GB"),
    "NO3-SE2": ("NO_3", "SE_2"),
    "NO4-SE1": ("NO_4", "SE_1"),
    "NO4-SE2": ("NO_4", "SE_2"),
    "NO4-FI": ("NO_4", "FI"),
}


def _tidy_flow(series, connection: str, direction: str) -> pd.DataFrame:
    # Some borders are reported every 15 minutes and others hourly. Taking the
    # hourly mean gives every connection the same unit and time interval.
    if isinstance(series, pd.DataFrame):
        # A missing reading is not the same as zero transfer.
        series = series.sum(axis=1, min_count=1)
    hourly = series.dropna().resample("1h").mean()

    tidy = hourly.rename("value_mw").reset_index()
    tidy.columns = ["timestamp", "value_mw"]
    tidy["timestamp"] = pd.to_datetime(tidy["timestamp"], utc=True)
    tidy["connection"] = connection
    tidy["direction"] = direction
    tidy["transfer_mwh"] = tidy["value_mw"]
    # I store timestamps in UTC, but group the results by the Norwegian calendar.
    # Otherwise the first hour of January would end up in December's totals.
    local_time = tidy["timestamp"].dt.tz_convert("Europe/Oslo")
    tidy["year"] = local_time.dt.year
    tidy["month"] = local_time.dt.month
    return tidy


def fetch_norwegian_transfers(client, start, end, cache_dir=".cache/entsoe-yearly", connections=None) -> pd.DataFrame:
    """Download both directions for every external Norwegian connection."""
    # Saving each year lets me resume a slow download without starting over.
    # Only public measurements go in this cache; the API key stays in .env.
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    logging.getLogger("entsoe").setLevel(logging.CRITICAL)
    boundaries = list(pd.date_range(start, end, freq="YS"))
    if not boundaries or boundaries[0] != start:
        boundaries.insert(0, start)
    if boundaries[-1] != end:
        boundaries.append(end)
    frames = []
    failures = []
    borders = NORWEGIAN_CONNECTIONS if connections is None else connections
    for connection, (norway_zone, neighbour_zone) in borders.items():
        # ENTSO-E treats direction as part of the query, so I request each border
        # twice instead of trying to infer imports from one series.
        for origin, destination, direction, short in [
            (norway_zone, neighbour_zone, "Out of Norway", "out"),
            (neighbour_zone, norway_zone, "Into Norway", "in"),
        ]:
            for first, last in zip(boundaries[:-1], boundaries[1:]):
                path = cache / f"{connection}-{short}-{first:%Y%m%d}-{last:%Y%m%d}.json"
                if path.exists():
                    frame = pd.read_json(path, orient="table")
                else:
                    try:
                        for attempt in range(3):
                            try:
                                xml = client.query_crossborder_flows(
                                    origin, destination, start=first, end=last
                                )
                                source = parse_crossborder_flows(xml)
                                break
                            except RequestException:
                                if attempt == 2:
                                    raise
                                time.sleep(2)
                        frame = _tidy_flow(source, connection, direction)
                        frame = frame.loc[
                            (frame["timestamp"] >= first) & (frame["timestamp"] < last)
                        ]
                        frame.to_json(path, orient="table", date_format="iso", index=False)
                    except Exception as error:
                        # Request URLs can contain the token, so I only show the error type.
                        failures.append(f"{connection} {short} {first:%Y-%m}: {type(error).__name__}")
                        print(f"Not downloaded: {failures[-1]}", flush=True)
                        continue
                frames.append(frame)
            print(f"Checked {connection}, {direction}.", flush=True)

    if failures:
        raise RuntimeError(
            "Some years could not be downloaded. Rerun to reuse the completed years: "
            + "; ".join(failures)
        ) from None

    transfers = pd.concat(frames, ignore_index=True)
    # Keep the end date exclusive, even if an API response includes its boundary.
    transfers = transfers.loc[
        (transfers["timestamp"] >= start) & (transfers["timestamp"] < end)
    ]
    return transfers.sort_values(
        ["timestamp", "connection", "direction"]
    ).drop_duplicates(["timestamp", "connection", "direction"])
