"""Read the curated power transfer rows from MongoDB."""

import pandas as pd
import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def get_transfer_collection():
    # The connection string lives in Streamlit secrets, never in the repository.
    # Caching the client also means the app can reuse one database connection.
    mongo = st.secrets["mongo"]
    client = MongoClient(mongo["uri"], serverSelectionTimeoutMS=10000)
    database = client[mongo.get("database", "ind320")]
    return database[mongo.get("collection", "power_transfers")]


@st.cache_data(ttl=600)
def load_power_transfers() -> pd.DataFrame:
    # I leave MongoDB's internal _id out because it is not useful in the plots.
    rows = list(get_transfer_collection().find({}, {"_id": 0}))
    data = pd.DataFrame(rows)
    if data.empty:
        return data

    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data["year"] = data["year"].astype(int)
    data["month"] = data["month"].astype(int)
    return data.sort_values(["timestamp", "connection", "direction"])
