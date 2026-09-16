# IND320 project 1

This folder holds my first compulsory IND320 project. The Jupyter notebook and
Streamlit app both read `data/reservoirs.csv`, copied from the [course repository](https://github.com/khliland/IND320/tree/main/D2Dbook/data).

I keep the source file as it is. The Python code gives the columns English names,
sorts dates, and uses the national `NO` / `0` area series for time plots. This
matters because the CSV has nine area rows for each week.

For a fresh clone, use Python 3.12 and install the small app dependency list:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

To run the notebook in a fresh environment, add its kernel and open the file in
VS Code or JupyterLab:

```bash
.venv/bin/python -m pip install ipykernel jupyterlab
.venv/bin/python -m jupyter lab IND320_assignment1.ipynb
```

On my Mac, I can use the existing `../.venv/bin/python` interpreter instead.
The published app will use the three packages in `requirements.txt`. The fourth
page is a placeholder for now, and this first part does not connect to a database.
