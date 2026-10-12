# IND320 project work

This repository contains my IND320 project work. I am keeping the different parts in the same repository because they build on each other during the semester.

## Project part 1

The first notebook and Streamlit pages use the reservoir data from NVE. In part 1, the data was stored as a local CSV file. The notebook shows how I renamed the columns, checked the data and made separate and combined plots. The Streamlit app includes the table and interactive plot from the first hand-in.

## Project part 2

Part 2 continues from the first version of the app. The reservoir data is now requested directly from the NVE Magasinstatistikk API, so the app no longer depends on the CSV file. I have also added a page where the area type and time interval can be selected.

The table and plot pages both let me select EL, NO or VASS without mixing the different area systems. The table has one row and a small fill-level graph for every associated area number. The download interval slider selects the months retained for the table or plot. NVE's documented `HentOffentligData` endpoint does not accept date parameters, so it first returns the full public history and the chosen interval is then kept locally. The separate area guide explains the codes and shows that VASS 4 is defined but has no measurement series.

The second part introduces ENTSO-E transfer data, Cassandra, Spark and MongoDB. The notebook follows the data from the API into Cassandra, uses Spark to select the columns needed for the plots, and then stores the prepared rows in MongoDB. The Streamlit transfer page reads those prepared rows from MongoDB.

I use 2024 and 2025, the last two complete calendar years for this hand-in. ENTSO-E downloads are cached locally by year in `.cache/entsoe-yearly`, so rerunning the notebook does not repeat successful requests. That folder is ignored by Git and contains public measurements, not credentials. The notebook includes a coverage table before the yearly totals.

On the transfer page, the left column uses a radio button for the connection and a separate year selector. The right column follows the updated instruction from 12 October: month pills decide which months are included in the two direction lines for the same connection and year.

I am developing this part on the `project-part-2` branch while the work is being checked. The branch will be merged into `main` after the peer review and feedback stage.

## Running the Streamlit app

The public app only needs the packages listed in `requirements.txt`:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

The MongoDB connection is kept in `.streamlit/secrets.toml` locally and in Streamlit Community Cloud secrets when the app is published. The real file is ignored by Git, and `.streamlit/secrets.toml.example` only shows the required field names.

## Running the notebook locally

The database and notebook packages are kept in a separate list because Streamlit Community Cloud does not need Spark or Cassandra:

```bash
.venv/bin/python -m pip install -r requirements-local.txt
.venv/bin/python -m jupyter lab IND320_assignment2.ipynb
```

PySpark 3.5 uses Java 17 on my Mac. The notebook selects that version before it starts Spark, because the newer Java 24 installation does not work with this Spark version.

Before running the database cells, I open Docker Desktop and start the existing container with `docker start my_cassandra`. Cassandra needs a short time to start before it accepts connections. In VS Code, I select the Python kernel from `../.venv` so Spark and the notebook use the same Python installation.

Running the full notebook also requires the local Cassandra container, an ENTSO-E API token and a MongoDB Atlas connection. The first cell reads the ignored `.env` file automatically, including when I open the notebook in VS Code. Existing environment variables take priority. The notebook can also reuse the MongoDB settings in `.streamlit/secrets.toml`. I can start Jupyter with:

```bash
.venv/bin/python -m jupyter lab IND320_assignment2.ipynb
```

On my Mac, the shared Python environment is at `../.venv`, so I use `../.venv/bin/python` in these commands. The passwords and API token stay in the local ignored files.

## Finding my private connection settings

The hidden `.env` file holds `MONGODB_URI`, including the MongoDB database password, and `ENTSOE_API_KEY`. The Streamlit copy of the MongoDB connection is in `.streamlit/secrets.toml`. Both files are ignored by Git and have owner-only file permissions on my Mac. I never print their contents in the notebook.

In Finder, I can open the project folder and press Command + Shift + . to show the hidden files. These local files are not an encrypted backup. I still need to keep a recovery copy in my password manager. The website login passwords are separate from the database password and API token; they are not stored in this project.

## Links

Project 2 branch: https://github.com/Sivan00/IND320-Sivan00-Project1/tree/project-part-2

Streamlit app: https://ind320-sivan00-project1.streamlit.app/

Project 1 screencast: [Open the screencast page](IND320_project_1_screencast.md)
