# IND320 project work

This repository holds the four parts of my IND320 project. The notebooks document the analysis, and the Streamlit app uses the same project data and helper functions.

## Project part 3

Part 3 adds hourly weather data and two new ways to look for patterns. `notebooks/IND320_assignment3.ipynb` contains the analysis. I use Open-Meteo ERA5 precipitation and temperature, NVE area polygons, and the weekly reservoir series.

The `data/areas/` folder contains NVE boundary files and fixed random samples with 1,000 points per electricity area and per NVE region. In the 2024 NO3 weather example, I average five sampled locations. This keeps the hourly API request manageable. The Streamlit page lets me choose an electricity area, dates, and a small number of points. It splits requests by month and shows an error if the API refuses a request.

The app has two new pages. Reservoir patterns has STL and spectrogram tabs for weekly reservoir fill. Weather outliers has SPC checks for precipitation and LOF anomalies for temperature. The weather points come from the selected electricity-zone polygon. I use the separate NVE region polygons for the regional sample points.

Open-Meteo does not require an API key for this non-commercial use. To refresh the NVE polygons, run `python scripts/download_nve_regions.py` from the project root. The geospatial packages needed for the notebook are in `requirements-local.txt`.

I am developing Part 3 on the `project-part-3` branch. The assignment asks me to use a temporary branch until peer review and teacher feedback are complete, then merge the work into `main`.

## Earlier parts

Part 1 uses the reservoir CSV from the course repository and shows how I rename, inspect and plot the data. Part 2 reads reservoir data directly from NVE and prepares cross-border transfer data with Cassandra, Spark and MongoDB. The notebooks and PDFs are in their own folders, and the screencast pages are in `recordings/`.

## Repository folders

- `notebooks/` contains the Jupyter notebooks for Parts 1 to 3.
- `pdfs/` contains the notebook PDFs.
- `recordings/` contains the screencast pages and links.
- `pages/` contains the separate Streamlit screens.
- `data/areas/` contains the public area polygons and reproducible point samples.

The Streamlit entry point and its helper modules stay in the project root because the app imports them from there.

## Running the Streamlit app

The public app only needs the packages in `requirements.txt`:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

The MongoDB connection stays in `.streamlit/secrets.toml` locally and in Streamlit Community Cloud secrets when the app is published. The real file is ignored by Git; `.streamlit/secrets.toml.example` only lists the field names.

## Running the notebooks locally

Install the local packages from the repository root:

```bash
.venv/bin/python -m pip install -r requirements-local.txt
```

Open a notebook from `notebooks/` in VS Code or JupyterLab. The notebooks find the repository root so their data and helper imports still work when opened from that folder.

Part 2 also needs the local Cassandra container, an ENTSO-E API token and a MongoDB Atlas connection. Its first cell reads the ignored `.env` file without printing credentials. Existing environment variables take priority. The notebook can also read the MongoDB connection from `.streamlit/secrets.toml`.

PySpark 3.5 uses Java 17 on my Mac. Before running the database cells, I open Docker Desktop and start the container with `docker start my_cassandra`. The Cassandra service needs a short time to start before it accepts connections. I use the shared Python environment at `../.venv/bin/python`.

## Links

GitHub repository: https://github.com/Sivan00/IND320-Sivan00-Project1

Streamlit app: https://ind320-sivan00-project1.streamlit.app/

Part 1 screencast: [Open the screencast page](recordings/IND320_project_1_screencast.md)

Part 2 screencast: [Open the screencast page](recordings/IND320_project_2_screencast.md)
