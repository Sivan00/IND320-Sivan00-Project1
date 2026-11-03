"""Weather and time-series tools for project part 3."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL


if TYPE_CHECKING:
    import geopandas as gpd


OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
NVE_REGIONS_FILE = Path(__file__).resolve().parents[1] / "data" / "areas" / "nve_regions.zip"
ELECTRICITY_AREAS_FILE = Path(__file__).resolve().parents[1] / "data" / "areas" / "electricity_areas.zip"

def load_nve_regions(path: str | Path = NVE_REGIONS_FILE) -> gpd.GeoDataFrame:
    """Read the NVE region polygons bundled with this project."""
    import geopandas as gpd

    regions = gpd.read_file(path)
    if "reg_code" not in regions.columns or regions.empty:
        raise ValueError("The NVE region file must contain reg_code polygons.")
    return regions.to_crs("EPSG:4326")


def load_electricity_areas(path: str | Path = ELECTRICITY_AREAS_FILE) -> gpd.GeoDataFrame:
    """Read NVE's current electricity bidding-zone polygons."""
    import geopandas as gpd

    areas = gpd.read_file(path).to_crs("EPSG:4326")
    if "area_name" not in areas.columns or areas.empty:
        raise ValueError("The electricity area file must contain area_name polygons.")
    areas["area_code"] = areas["area_name"].str.replace(" ", "", regex=False)
    return areas


def sample_region_points(
    regions: gpd.GeoDataFrame,
    region_codes: Iterable[str],
    n: int = 1000,
    seed: int = 320,
    code_column: str = "reg_code",
) -> pd.DataFrame:
    """Draw reproducible, area-weighted random coordinates inside NVE regions."""
    import geopandas as gpd
    import shapely

    if n < 1:
        raise ValueError("n must be at least 1")
    region_codes = list(region_codes)
    selected = regions.loc[regions[code_column].isin(region_codes)].to_crs("EPSG:3035")
    if selected.empty:
        raise ValueError("No NVE polygons matched the selected region codes.")

    # Sampling in an equal-area projection avoids giving small geographic
    # regions too many points just because their longitude spans are narrower.
    geometry = selected.geometry.union_all()
    rng = np.random.default_rng(seed)
    min_x, min_y, max_x, max_y = geometry.bounds
    points = []
    attempts = 0
    while len(points) < n and attempts < n * 500:
        # Vectorized polygon checks are much faster than asking each detailed
        # boundary polygon about one point at a time.
        batch_size = max(500, min(20_000, (n - len(points)) * 12))
        x_values = rng.uniform(min_x, max_x, size=batch_size)
        y_values = rng.uniform(min_y, max_y, size=len(x_values))
        candidates = shapely.points(x_values, y_values)
        inside = candidates[shapely.covers(geometry, candidates)]
        points.extend(inside[: n - len(points)])
        attempts += len(x_values)
    if len(points) != n:
        raise RuntimeError("Could not sample enough points from the selected polygons.")

    sampled = gpd.GeoDataFrame(geometry=points, crs="EPSG:3035").to_crs("EPSG:4326")
    return pd.DataFrame(
        {
            "region_group": "+".join(region_codes),
            "sample_id": np.arange(1, n + 1),
            "latitude": sampled.geometry.y.to_numpy(),
            "longitude": sampled.geometry.x.to_numpy(),
        }
    )


def build_weather_sample(
    regions: gpd.GeoDataFrame,
    n_each: int = 1000,
    seed: int = 320,
) -> pd.DataFrame:
    """Sample 1,000 points in each of the five source weather regions."""
    # I save each source region separately. The East and North combinations are
    # built from these rows later, which keeps the 1,000-point requirement clear.
    codes = ["RS", "RØ", "RV", "RM", "RN"]
    pieces = [
        sample_region_points(regions, [code], n_each, seed + index)
        .assign(region_group=code)
        for index, code in enumerate(codes)
    ]
    return pd.concat(pieces, ignore_index=True)


def build_electricity_sample(
    areas: gpd.GeoDataFrame,
    n_each: int = 1000,
    seed: int = 640,
) -> pd.DataFrame:
    """Create the same-sized random sample for each NVE electricity area."""
    area_codes = sorted(areas["area_code"].dropna().unique())
    pieces = [
        sample_region_points(
            areas, [code], n=n_each, seed=seed + index, code_column="area_code"
        ).rename(columns={"region_group": "area_group"})
        for index, code in enumerate(area_codes)
    ]
    return pd.concat(pieces, ignore_index=True)


def robust_limits(values: pd.Series | np.ndarray, n_sd: float = 3.0) -> tuple[float, float, float, float]:
    """Return median, robust spread and symmetric limits using the MAD."""
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        raise ValueError("At least one finite value is required.")
    center = float(np.median(clean))
    mad = float(np.median(np.abs(clean - center)))
    spread = 1.4826 * mad
    if spread == 0:
        # Precipitation can be zero for most hours, which makes the ordinary
        # MAD collapse. I estimate the scale from non-median observations then.
        departures = np.abs(clean - center)
        nonzero_departures = departures[departures > 0]
        if nonzero_departures.size:
            spread = float(1.4826 * np.median(nonzero_departures))
        elif clean.size > 1:
            spread = float(np.std(clean, ddof=1))
    return center, spread, center - n_sd * spread, center + n_sd * spread


def spc_precipitation_plot(
    weather: pd.DataFrame,
    cutoff: float = 0.08,
    n_sd: float = 3.0,
) -> tuple[plt.Figure, dict[str, float | int]]:
    """Plot precipitation and robust SPC limits; use DCT residuals for flags."""
    if not 0 < cutoff < 1:
        raise ValueError("cutoff must be between 0 and 1")
    if n_sd <= 0:
        raise ValueError("n_sd must be positive")
    required = {"time", "precipitation"}
    if not required.issubset(weather.columns):
        raise ValueError("weather must contain time and precipitation columns")

    data = weather.dropna(subset=["precipitation"]).sort_values("time").copy()
    values = data["precipitation"].astype(float).to_numpy()
    if len(values) < 8:
        raise ValueError("At least eight observations are needed for DCT filtering")

    # I keep only low-frequency DCT coefficients as the local background; the
    # remaining high-pass signal is SATV and is used only to flag unusual hours.
    coefficients = dct(values, type=2, norm="ortho")
    keep = max(1, int(np.ceil(len(coefficients) * cutoff)))
    background = idct(
        np.r_[coefficients[:keep], np.zeros(len(coefficients) - keep)],
        type=2,
        norm="ortho",
    )
    satv = values - background
    satv_center, satv_spread, satv_low, satv_high = robust_limits(satv, n_sd)
    outlier = (satv < satv_low) | (satv > satv_high)

    # Translate the residual limits back to precipitation units at every hour.
    # These are exactly the boundaries used for the flags, not raw-data limits.
    center = background + satv_center
    low = background + satv_low
    high = background + satv_high
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(data["time"], values, color="#3D7476", linewidth=1.2, label="Mean precipitation")
    ax.plot(data["time"], center, color="#555555", linewidth=1, label="DCT background + residual median")
    ax.plot(data["time"], high, color="#B45B4E", linestyle="--", linewidth=1, label=f"SATV-based ±{n_sd:g} SD limits")
    ax.plot(data["time"], low, color="#B45B4E", linestyle="--", linewidth=1)
    ax.scatter(data.loc[outlier, "time"], values[outlier], color="#D06A2E", s=22, zorder=3, label="DCT flags")
    ax.set(title="Precipitation: SPC outlier check", ylabel="Precipitation (mm/hour)", xlabel="Date")
    ax.grid(axis="y", color="#E7E7E7", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncols=2)
    fig.tight_layout()
    summary = {
        "observations": int(len(data)),
        "outliers": int(outlier.sum()),
        "outlier_percent": float(outlier.mean() * 100),
        "residual_median_mm": satv_center,
        "residual_robust_sd_mm": satv_spread,
        "residual_lower_limit_mm": satv_low,
        "residual_upper_limit_mm": satv_high,
        "dct_cutoff_fraction": cutoff,
        "robust_sd_multiplier": n_sd,
    }
    return fig, summary


def lof_temperature_plot(
    weather: pd.DataFrame,
    contamination: float = 0.01,
) -> tuple[plt.Figure, dict[str, float | int]]:
    """Find unusual hourly mean temperatures with Local Outlier Factor."""
    if not 0 < contamination <= 0.5:
        raise ValueError("contamination must be greater than 0 and at most 0.5")
    if not {"time", "temperature_2m"}.issubset(weather.columns):
        raise ValueError("weather must contain time and temperature_2m columns")
    data = weather.dropna(subset=["temperature_2m"]).sort_values("time").copy()
    if len(data) < 20:
        raise ValueError("At least 20 temperature observations are needed for LOF")

    temperature = data["temperature_2m"].astype(float)
    # LOF sees both the temperature and its recent departure from a rolling
    # baseline, so ordinary winter/summer levels are less likely to look odd.
    baseline = temperature.rolling(24, center=True, min_periods=6).median()
    departure = temperature - baseline.bfill().ffill()
    features = np.column_stack([temperature.to_numpy(), departure.to_numpy()])
    model = LocalOutlierFactor(n_neighbors=min(20, len(data) - 1), contamination=contamination)
    flags = model.fit_predict(features) == -1

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(data["time"], temperature, color="#3D7476", linewidth=1.1, label="Mean temperature")
    ax.scatter(data.loc[flags, "time"], temperature[flags], color="#D06A2E", s=22, zorder=3, label="LOF anomaly")
    ax.set(title="Temperature: Local Outlier Factor", ylabel="Temperature (°C)", xlabel="Date")
    ax.grid(axis="y", color="#E7E7E7", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    summary = {
        "observations": int(len(data)),
        "anomalies": int(flags.sum()),
        "anomaly_percent": float(flags.mean() * 100),
        "contamination": contamination,
        "median_temperature_c": float(temperature.median()),
    }
    return fig, summary


def stl_decomposition(
    series: pd.Series,
    period: int = 52,
    seasonal_smoother: int = 13,
    trend_smoother: int | None = None,
    robust: bool = True,
) -> tuple[plt.Figure, pd.DataFrame]:
    """Decompose weekly reservoir fill into trend, seasonal and residual parts."""
    clean = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    if len(clean) < 2 * period:
        raise ValueError(f"At least {2 * period} values are needed for period={period}")
    if period < 2 or seasonal_smoother < 7 or seasonal_smoother % 2 == 0:
        raise ValueError("period must be >= 2 and seasonal_smoother must be odd and >= 7")
    kwargs = {"period": period, "seasonal": seasonal_smoother, "robust": robust}
    if trend_smoother is not None:
        if trend_smoother % 2 == 0 or trend_smoother <= period:
            raise ValueError("trend_smoother must be odd and greater than period")
        kwargs["trend"] = trend_smoother
    result = STL(clean, **kwargs).fit()
    components = pd.DataFrame(
        {"observed": clean, "trend": result.trend, "seasonal": result.seasonal, "residual": result.resid}
    )
    fig, axes = plt.subplots(4, 1, figsize=(10, 7), sharex=True)
    for ax, column in zip(axes, components.columns):
        ax.plot(components.index, components[column], color="#3D7476", linewidth=1.1)
        ax.set_ylabel(column.capitalize())
        ax.grid(axis="y", color="#E7E7E7", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_title("STL decomposition of weekly reservoir fill", loc="left", fontweight="bold")
    axes[-1].set_xlabel("Date")
    fig.tight_layout()
    return fig, components


def fill_spectrogram(
    series: pd.Series,
    window_weeks: int = 104,
    overlap_weeks: int = 78,
) -> tuple[plt.Figure, dict[str, float | int]]:
    """Show the dominant frequencies in a weekly reservoir-fill series."""
    clean = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    if len(clean) < 8:
        raise ValueError("At least eight weekly observations are needed")
    if not 2 <= window_weeks <= len(clean):
        raise ValueError("window_weeks must be between 2 and the series length")
    if not 0 <= overlap_weeks < window_weeks:
        raise ValueError("overlap_weeks must be smaller than window_weeks")

    frequency, times, power = spectrogram(
        clean.to_numpy(), fs=52, window="hann", nperseg=window_weeks,
        noverlap=overlap_weeks, detrend="linear", scaling="spectrum",
    )
    fig, ax = plt.subplots(figsize=(10, 4.8))
    # fs=52 expresses frequency per year, so segment times are years.
    mesh = ax.pcolormesh(times * 52, frequency, 10 * np.log10(power + 1e-12), shading="auto", cmap="viridis")
    fig.colorbar(mesh, ax=ax, label="Power (dB)")
    ax.set(title="Spectrogram of weekly reservoir fill", xlabel="Weeks from start", ylabel="Frequency (cycles/year)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    summary = {
        "observations": int(len(clean)),
        "window_weeks": int(window_weeks),
        "overlap_weeks": int(overlap_weeks),
        "time_windows": int(len(times)),
    }
    return fig, summary


@st.cache_data(ttl=86400, show_spinner=False)
def load_open_meteo_region(
    area_code: str,
    start_date: str,
    end_date: str,
    point_count: int = 1,
    sample_file: str = "data/areas/electricity_sample_points.csv",
) -> pd.DataFrame:
    """Download ERA5 hourly weather and average the stored sample points."""
    # Resolving the sample from the project folder also works inside notebooks/.
    sample_path = Path(sample_file)
    if not sample_path.is_absolute():
        sample_path = Path(__file__).resolve().parents[1] / sample_path
    samples = pd.read_csv(sample_path)
    selected = samples.loc[samples["area_group"] == area_code]
    if point_count < 1:
        raise ValueError("point_count must be at least 1")
    if point_count > len(selected):
        raise ValueError("point_count exceeds the number of saved locations for this area")
    # A fixed sample per area keeps the app responsive and makes reruns comparable.
    chosen = selected.head(point_count)
    if chosen.empty:
        raise ValueError(f"No saved sample points were found for {area_code}.")

    # Smaller monthly requests are more reliable than one very large yearly URL.
    first_day = pd.Timestamp(start_date).normalize()
    last_day = pd.Timestamp(end_date).normalize()
    if first_day > last_day:
        raise ValueError("start_date must not be after end_date")
    months = pd.period_range(first_day.to_period("M"), last_day.to_period("M"), freq="M")
    batch_summaries = []
    for month in months:
        month_start = max(first_day, month.start_time)
        month_end = min(last_day, month.end_time.normalize())
        for start in range(0, len(chosen), 50):
            batch = chosen.iloc[start : start + 50]
            params = {
                "latitude": ",".join(f"{value:.5f}" for value in batch["latitude"]),
                "longitude": ",".join(f"{value:.5f}" for value in batch["longitude"]),
                "start_date": month_start.date().isoformat(),
                "end_date": month_end.date().isoformat(),
                "hourly": "precipitation,temperature_2m",
                "models": "era5",
                "timezone": "Europe/Oslo",
                "temperature_unit": "celsius",
                "precipitation_unit": "mm",
            }
            # Smaller requests keep the response size manageable for this endpoint.
            response = requests.get(OPEN_METEO_ARCHIVE, params=params, timeout=(10, 60))
            if response.status_code == 429:
                try:
                    reason = response.json().get("reason", "Open-Meteo rate limit reached.")
                except ValueError:
                    reason = "Open-Meteo rate limit reached."
                raise ValueError(f"Open-Meteo could not serve this request: {reason}")
            response.raise_for_status()
            payload = response.json()
            locations = payload if isinstance(payload, list) else [payload]
            frames = []
            for location in locations:
                hourly = location.get("hourly", {})
                if not hourly.get("time"):
                    continue
                frames.append(
                    pd.DataFrame(
                        {
                            "time": pd.to_datetime(hourly["time"]),
                            "precipitation": hourly.get("precipitation"),
                            "temperature_2m": hourly.get("temperature_2m"),
                        }
                    )
                )
            if not frames:
                continue
            batch_weather = pd.concat(frames, ignore_index=True)
            sums = batch_weather.groupby("time")[["precipitation", "temperature_2m"]].sum(min_count=1)
            counts = batch_weather.groupby("time")[["precipitation", "temperature_2m"]].count()
            batch_summary = sums.add_suffix("_sum").join(counts.add_suffix("_count"))
            batch_summaries.append(batch_summary)

    if not batch_summaries:
        raise ValueError("Open-Meteo returned no hourly observations for this interval.")
    totals = pd.concat(batch_summaries).groupby(level=0).sum()
    return pd.DataFrame(
        {
            "time": totals.index,
            "precipitation": totals["precipitation_sum"] / totals["precipitation_count"],
            "temperature_2m": totals["temperature_2m_sum"] / totals["temperature_2m_count"],
        }
    ).reset_index(drop=True)
