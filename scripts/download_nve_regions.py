"""Download the public NVE region and electricity area shapefiles."""

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

import geopandas as gpd
import requests


ROOT = Path(__file__).resolve().parents[1]
AREA_DIR = ROOT / "data" / "areas"
NVE_REGION_LAYER = (
    "https://gis4.nve.no/map/rest/services/Mapservices/Administrasjon/"
    "MapServer/0/query"
)
ELECTRICITY_AREA_LAYER = (
    "https://kart.nve.no/enterprise/rest/services/Nettomraader/"
    "MapServer/0/query"
)


def download_layer(url: str, fields: str, output_name: str, rename: dict[str, str]) -> None:
    output = AREA_DIR / output_name
    response = requests.get(
        url,
        params={
            "where": "1=1",
            "outFields": fields,
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "geojson",
        },
        timeout=60,
    )
    response.raise_for_status()
    temporary_geojson = AREA_DIR / f"{output.stem}.geojson"
    temporary_geojson.write_bytes(response.content)
    regions = gpd.read_file(temporary_geojson).to_crs("EPSG:4326")
    temporary_geojson.unlink()
    regions = regions.rename(columns=rename)

    # A zip keeps the shapefile's related files together when the project moves.
    with TemporaryDirectory(dir=AREA_DIR) as temporary_directory:
        shape_path = Path(temporary_directory) / f"{output.stem}.shp"
        shape_columns = [column for column in rename.values() if column in regions.columns]
        regions[[*shape_columns, "geometry"]].to_file(shape_path)
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for component in Path(temporary_directory).iterdir():
                archive.write(component, arcname=component.name)
    print(f"Saved {len(regions)} area polygons to {output}")


def main() -> None:
    AREA_DIR.mkdir(parents=True, exist_ok=True)
    download_layer(
        NVE_REGION_LAYER,
        "REGION,REGIONNAVN",
        "nve_regions.zip",
        {"REGION": "reg_code", "REGIONNAVN": "reg_name"},
    )
    download_layer(
        ELECTRICITY_AREA_LAYER,
        "budomr",
        "electricity_areas.zip",
        {"budomr": "area_name"},
    )


if __name__ == "__main__":
    main()
