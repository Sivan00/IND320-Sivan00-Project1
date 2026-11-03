# IND320 Project

Parts 1 and 2 are on `main`. Part 3 is on the `project-part-3` branch while it is reviewed. The same Streamlit app is used throughout.

## Start here

- [Part 1 notebook](notebooks/IND320_assignment1.ipynb)
- [Part 2 notebook](notebooks/IND320_assignment2.ipynb)
- [Part 3 notebook](notebooks/IND320_assignment3.ipynb)
- [Part 3 PDF](pdfs/IND320_project_3_notebook.pdf)
- [Streamlit app](https://ind320-sivan00-project1.streamlit.app/)

## Folders

`notebooks/` has the Jupyter notebooks. `pdfs/` has notebook PDFs. `recordings/` has screencast links. `pages/` has the Streamlit screens. Shared app code stays in the root so its imports work.

## Run locally

```bash
.venv/bin/python -m pip install -r requirements-local.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

Part 2 also needs Cassandra and private settings in `.env` or `.streamlit/secrets.toml`. Those files are ignored by Git. Part 3 uses public NVE area data and Open-Meteo historical weather data.
