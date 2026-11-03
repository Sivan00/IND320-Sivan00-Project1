# IND320 Project

Parts 1 and 2 are on `main`. Part 3 is being reviewed on `project-part-3`. The same Streamlit app is used throughout.

## Files

- `notebooks/` - project notebooks
- `pdfs/` - notebook PDFs
- `recordings/` - screencast links
- `pages/` - Streamlit pages

## Open

- [Part 1 notebook](notebooks/IND320_assignment1.ipynb)
- [Part 2 notebook](notebooks/IND320_assignment2.ipynb)
- [Part 3 branch](https://github.com/Sivan00/IND320-Sivan00-Project1/tree/project-part-3)
- [Streamlit app](https://ind320-sivan00-project1.streamlit.app/)

## Run locally

```bash
.venv/bin/python -m pip install -r requirements-local.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

Part 2 also needs the local Cassandra container and private settings in `.env` or `.streamlit/secrets.toml`. These files are ignored by Git.
