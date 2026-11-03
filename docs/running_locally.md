# Running locally

Use Python 3.12 and run these commands from the project folder:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-local.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

On my Mac, the existing environment is one folder up, so I use `../.venv/bin/python`.

The notebooks are in `notebooks/`. Open them in VS Code or JupyterLab with the same Python environment. Part 1 is the saved CSV-based work; the current app uses NVE directly. To rerun Part 1, download the original `reservoirs.csv` from the course repository and place it in `data/`.

Part 2 needs the local Cassandra container, Spark and the private settings described in `.env.example` and `.streamlit/secrets.toml.example`. Streamlit Cloud reads the MongoDB settings from its Secrets page. Real settings stay outside Git.

Part 3 uses public NVE and Open-Meteo data. The saved area polygons and coordinate samples are in `data/areas/`. Shared Python functions are in `utils/`, and the Streamlit screens are in `pages/`.
