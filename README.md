# IND320 project 1

This repository contains my first compulsory project in IND320. I use the
`reservoirs.csv` dataset from the [course repository](https://github.com/khliland/IND320/tree/main/D2Dbook/data).
Both the Jupyter Notebook and the Streamlit app read the same local CSV file.

I kept the original CSV unchanged. Instead, I rename the columns in Python, sort
the rows by date and use the national `NO` series with area number `0` for the
time plots. The dataset contains nine area rows for each week, so using the
national series avoids plotting the same week several times.

## Running the Streamlit app locally

The project uses Python 3.12. After cloning the repository, the app can be
started with:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

## Opening the notebook

The notebook can be opened in VS Code or JupyterLab. If Jupyter is not already
installed in the environment, I use:

```bash
.venv/bin/python -m pip install ipykernel jupyterlab
.venv/bin/python -m jupyter lab IND320_assignment1.ipynb
```

On my Mac, I can also use the Python environment already created in the main
IND320 folder. The packages needed by the published app are listed in
`requirements.txt`.

The fourth page is still a simple placeholder because this is only the first
part of the project. The app currently reads data from the local CSV file.
MongoDB belongs to project part 2 and is not used in this submission.

## Screencast

My project 1 screencast is available on the [GitHub release page](https://github.com/Sivan00/IND320-Sivan00-Project1/releases/tag/project-1).
