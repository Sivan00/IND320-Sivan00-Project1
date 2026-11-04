# Run Project 2 locally

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
