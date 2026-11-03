# IND320 Project

Three project parts in one repository, with one Streamlit app throughout.

## Start here

- [Part 1 notebook](notebooks/IND320_assignment1.ipynb)
- [Part 2 notebook](notebooks/IND320_assignment2.ipynb)
- [Part 3 notebook](notebooks/IND320_assignment3.ipynb)
- [Part 3 PDF](pdfs/IND320_project_3_notebook.pdf)
- [Streamlit app](https://ind320-sivan00-project1.streamlit.app/)

Part 3 is on the `project-part-3` branch while it is reviewed. The same app URL is used for every part.

## Folders

`notebooks/` has the Jupyter notebooks. `pdfs/` has the notebook PDFs. `recordings/` has the screencast links. `pages/` has the Streamlit screens. Shared app code stays in the root so its imports work.

## Run locally

```bash
.venv/bin/python -m pip install -r requirements-local.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

For Part 2, use the local `.env`, MongoDB secrets and Cassandra container described in the notebook. They are not committed to GitHub. Part 3 uses NVE public area data and Open-Meteo historical weather data.

## Links

[GitHub repository](https://github.com/Sivan00/IND320-Sivan00-Project1) · [Streamlit app](https://ind320-sivan00-project1.streamlit.app/)
