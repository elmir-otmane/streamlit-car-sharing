import streamlit as st
import pandas as pd

st.set_page_config(page_title="Car Sharing Dashboard", layout="wide")
st.title("🚗 Car Sharing Dashboard")

# ─── 1. LOAD DATA ────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    trips  = pd.read_csv("trips.csv")
    cars   = pd.read_csv("cars.csv")
    cities = pd.read_csv("cities.csv")
    return trips, cars, cities

trips, cars, cities = load_data()

# ─── 2. MERGE DATAFRAMES ─────────────────────────────────────────────────────

# trips.car_id → cars.id
trips_merged = trips.merge(cars, left_on="car_id", right_on="id", how="left", suffixes=("", "_car"))

# cars.city_id → cities.city_id
trips_merged = trips_merged.merge(cities, on="city_id", how="left")

# ─── 3. DROP USELESS COLUMNS ─────────────────────────────────────────────────

trips_merged = trips_merged.drop(
    columns=[c for c in ["id", "car_id", "customer_id", "city_id"] if c in trips_merged.columns]
)

# ─── 4. FIX DATE FORMATS ─────────────────────────────────────────────────────

trips_merged["pickup_time"]  = pd.to_datetime(trips_merged["pickup_time"])
trips_merged["dropoff_time"] = pd.to_datetime(trips_merged["dropoff_time"])
trips_merged["pickup_date"]  = trips_merged["pickup_time"].dt.date
trips_merged["duration_min"] = (
    trips_merged["dropoff_time"] - trips_merged["pickup_time"]
).dt.total_seconds() / 60

# ─── 5. SIDEBAR FILTERS ──────────────────────────────────────────────────────

st.sidebar.header("Filters")
brands = st.sidebar.multiselect(
    "Select Car Brand",
    options=trips_merged["brand"].unique(),
    default=trips_merged["brand"].unique(),
)
trips_merged = trips_merged[trips_merged["brand"].isin(brands)]

# ─── 6. BUSINESS METRICS ─────────────────────────────────────────────────────

total_trips    = len(trips_merged)
total_distance = trips_merged["distance"].sum()
top_car        = trips_merged.groupby("model")["revenue"].sum().idxmax()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Trips", total_trips)
with col2:
    st.metric("Top Car Model by Revenue", top_car)
with col3:
    st.metric("Total Distance (km)", f"{total_distance:,.2f}")

# ─── 7. DATA PREVIEW ─────────────────────────────────────────────────────────

st.subheader("Data Preview")
st.write(trips_merged.head())

# ─── 8. VISUALIZATIONS ───────────────────────────────────────────────────────

st.subheader("📈 Trips Over Time")
st.line_chart(trips_merged.groupby("pickup_date").size().rename("trips"))

st.subheader("💰 Revenue per Car Model")
st.bar_chart(trips_merged.groupby("model")["revenue"].sum().sort_values(ascending=False))

st.subheader("📊 Cumulative Revenue Growth Over Time")
st.area_chart(trips_merged.groupby("pickup_date")["revenue"].sum().cumsum())

st.subheader("🚘 Number of Trips per Car Model")
st.bar_chart(trips_merged.groupby("model").size().sort_values(ascending=False).rename("trips"))

st.subheader("⏱️ Average Trip Duration by City (minutes)")
st.bar_chart(trips_merged.groupby("city_name")["duration_min"].mean().sort_values(ascending=False))

st.subheader("🏙️ Revenue by City")
st.bar_chart(trips_merged.groupby("city_name")["revenue"].sum().sort_values(ascending=False))

st.subheader("🔍 Bonus – Average Trip Distance by Brand (km)")
st.bar_chart(trips_merged.groupby("brand")["distance"].mean().sort_values(ascending=False))
