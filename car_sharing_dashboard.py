import streamlit as st
import pandas as pd

st.set_page_config(page_title="Car Sharing Dashboard", layout="wide")
st.title("🚗 Car Sharing Dashboard")

# ─── 1. LOAD DATA ────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    trips  = pd.read_csv("datasets/trips.csv")
    cars   = pd.read_csv("datasets/cars.csv")
    cities = pd.read_csv("datasets/cities.csv")
    return trips, cars, cities

trips, cars, cities = load_data()

# ─── 2. MERGE DATAFRAMES ─────────────────────────────────────────────────────

# Merge trips with cars on car_id
trips_merged = trips.merge(cars, left_on="car_id", right_on="id", how="left")

# Merge with cities on city_id
trips_merged = trips_merged.merge(cities, left_on="city_id", right_on="id", how="left")

# ─── 3. DROP USELESS ID COLUMNS ──────────────────────────────────────────────

trips_merged = trips_merged.drop(
    columns=[c for c in ["id_car", "city_id", "id_customer", "id", "car_id"] if c in trips_merged.columns]
)

# ─── 4. FIX DATE FORMATS ─────────────────────────────────────────────────────

trips_merged["pickup_time"]  = pd.to_datetime(trips_merged["pickup_time"])
trips_merged["dropoff_time"] = pd.to_datetime(trips_merged["dropoff_time"])
trips_merged["pickup_date"]  = trips_merged["pickup_time"].dt.date

# Derive trip duration in minutes
trips_merged["duration_min"] = (
    trips_merged["dropoff_time"] - trips_merged["pickup_time"]
).dt.total_seconds() / 60

# ─── 5. SIDEBAR FILTERS ──────────────────────────────────────────────────────

st.sidebar.header("Filters")

cars_brand = st.sidebar.multiselect(
    "Select Car Brand",
    options=trips_merged["brand"].unique(),
    default=trips_merged["brand"].unique(),
)

trips_merged = trips_merged[trips_merged["brand"].isin(cars_brand)]

# ─── 6. BUSINESS METRICS ─────────────────────────────────────────────────────

total_trips    = len(trips_merged)
total_distance = trips_merged["distance"].sum()
top_car        = trips_merged.groupby("model")["revenue"].sum().idxmax()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Trips", value=total_trips)
with col2:
    st.metric(label="Top Car Model by Revenue", value=top_car)
with col3:
    st.metric(label="Total Distance (km)", value=f"{total_distance:,.2f}")

# ─── 7. DATA PREVIEW ─────────────────────────────────────────────────────────

st.subheader("Data Preview")
st.write(trips_merged.head())

# ─── 8. VISUALIZATIONS ───────────────────────────────────────────────────────

st.subheader("📈 Trips Over Time")
trips_over_time = (
    trips_merged.groupby("pickup_date")
    .size()
    .reset_index(name="trips")
    .set_index("pickup_date")
)
st.line_chart(trips_over_time)

# ── Revenue per Car Model ─────────────────────────────────────────────────────
st.subheader("💰 Revenue per Car Model")
revenue_by_model = (
    trips_merged.groupby("model")["revenue"]
    .sum()
    .sort_values(ascending=False)
)
st.bar_chart(revenue_by_model)

# ── Cumulative Revenue Growth Over Time ──────────────────────────────────────
st.subheader("📊 Cumulative Revenue Growth Over Time")
cumulative_revenue = (
    trips_merged.groupby("pickup_date")["revenue"]
    .sum()
    .cumsum()
    .reset_index()
    .set_index("pickup_date")
)
st.area_chart(cumulative_revenue)

# ── Number of Trips per Car Model ─────────────────────────────────────────────
st.subheader("🚘 Number of Trips per Car Model")
trips_by_model = (
    trips_merged.groupby("model")
    .size()
    .sort_values(ascending=False)
)
st.bar_chart(trips_by_model)

# ── Average Trip Duration by City ────────────────────────────────────────────
st.subheader("⏱️ Average Trip Duration by City (minutes)")
avg_duration_city = (
    trips_merged.groupby("city")["duration_min"]
    .mean()
    .sort_values(ascending=False)
)
st.bar_chart(avg_duration_city)

# ── Revenue by City ───────────────────────────────────────────────────────────
st.subheader("🏙️ Revenue by City")
revenue_by_city = (
    trips_merged.groupby("city")["revenue"]
    .sum()
    .sort_values(ascending=False)
)
st.bar_chart(revenue_by_city)

# ── Bonus: Average Distance by Brand ─────────────────────────────────────────
st.subheader("🔍 Bonus – Average Trip Distance by Brand (km)")
avg_dist_brand = (
    trips_merged.groupby("brand")["distance"]
    .mean()
    .sort_values(ascending=False)
)
st.bar_chart(avg_dist_brand)
