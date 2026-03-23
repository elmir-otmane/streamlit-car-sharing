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

# ─── DEBUG: show columns (remove after fixing) ───────────────────────────────
with st.expander("🔍 Debug: Column Names (click to expand)"):
    st.write("**trips columns:**", list(trips.columns))
    st.write("**cars columns:**", list(cars.columns))
    st.write("**cities columns:**", list(cities.columns))

# ─── 2. MERGE DATAFRAMES ─────────────────────────────────────────────────────

# Find the car join key in trips
car_key_trips  = next((c for c in trips.columns if "car" in c.lower()), None)
car_key_cars   = next((c for c in cars.columns  if c.lower() == "id"), "id")

if car_key_trips:
    trips_merged = trips.merge(cars, left_on=car_key_trips, right_on=car_key_cars, how="left", suffixes=("", "_car"))
else:
    trips_merged = trips.copy()

# Find the city join key in trips_merged
city_key_trips  = next((c for c in trips_merged.columns if "city" in c.lower() and "id" in c.lower()), None)
city_key_cities = next((c for c in cities.columns       if c.lower() == "id"), "id")

if city_key_trips:
    trips_merged = trips_merged.merge(cities, left_on=city_key_trips, right_on=city_key_cities, how="left", suffixes=("", "_city"))

# ─── 3. DROP USELESS ID COLUMNS ──────────────────────────────────────────────

drop_cols = [c for c in trips_merged.columns if c.lower() in ["id_car","city_id","id_customer","id","car_id"]]
trips_merged = trips_merged.drop(columns=drop_cols, errors="ignore")

# ─── 4. FIX DATE FORMATS ─────────────────────────────────────────────────────

# Detect pickup / dropoff columns
pickup_col  = next((c for c in trips_merged.columns if "pickup"  in c.lower() and "time" in c.lower()), None)
dropoff_col = next((c for c in trips_merged.columns if "dropoff" in c.lower() and "time" in c.lower()), None)

if pickup_col:
    trips_merged[pickup_col]  = pd.to_datetime(trips_merged[pickup_col])
    trips_merged["pickup_date"] = trips_merged[pickup_col].dt.date
if dropoff_col:
    trips_merged[dropoff_col] = pd.to_datetime(trips_merged[dropoff_col])

if pickup_col and dropoff_col:
    trips_merged["duration_min"] = (
        trips_merged[dropoff_col] - trips_merged[pickup_col]
    ).dt.total_seconds() / 60

# ─── 5. DETECT KEY COLUMNS ───────────────────────────────────────────────────

brand_col    = next((c for c in trips_merged.columns if c.lower() in ["brand","make","manufacturer"]), None)
model_col    = next((c for c in trips_merged.columns if c.lower() == "model"), None)
revenue_col  = next((c for c in trips_merged.columns if "revenue" in c.lower() or "price" in c.lower() or "amount" in c.lower()), None)
distance_col = next((c for c in trips_merged.columns if "distance" in c.lower() or "km" in c.lower()), None)
city_col     = next((c for c in trips_merged.columns if c.lower() in ["city","name_city","city_name"]), None)

# ─── 6. SIDEBAR FILTERS ──────────────────────────────────────────────────────

st.sidebar.header("Filters")

if brand_col:
    cars_brand = st.sidebar.multiselect(
        "Select Car Brand",
        options=trips_merged[brand_col].unique(),
        default=trips_merged[brand_col].unique(),
    )
    trips_merged = trips_merged[trips_merged[brand_col].isin(cars_brand)]

# ─── 7. BUSINESS METRICS ─────────────────────────────────────────────────────

total_trips = len(trips_merged)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Trips", value=total_trips)

with col2:
    if model_col and revenue_col:
        top_car = trips_merged.groupby(model_col)[revenue_col].sum().idxmax()
        st.metric(label="Top Car Model by Revenue", value=top_car)
    else:
        st.metric(label="Top Car Model by Revenue", value="N/A")

with col3:
    if distance_col:
        total_distance = trips_merged[distance_col].sum()
        st.metric(label="Total Distance (km)", value=f"{total_distance:,.2f}")
    else:
        st.metric(label="Total Distance (km)", value="N/A")

# ─── 8. DATA PREVIEW ─────────────────────────────────────────────────────────

st.subheader("Data Preview")
st.write(trips_merged.head())

# ─── 9. VISUALIZATIONS ───────────────────────────────────────────────────────

if "pickup_date" in trips_merged.columns:
    st.subheader("📈 Trips Over Time")
    trips_over_time = trips_merged.groupby("pickup_date").size().reset_index(name="trips").set_index("pickup_date")
    st.line_chart(trips_over_time)

if model_col and revenue_col:
    st.subheader("💰 Revenue per Car Model")
    st.bar_chart(trips_merged.groupby(model_col)[revenue_col].sum().sort_values(ascending=False))

    st.subheader("📊 Cumulative Revenue Growth Over Time")
    if "pickup_date" in trips_merged.columns:
        cum_rev = trips_merged.groupby("pickup_date")[revenue_col].sum().cumsum().reset_index().set_index("pickup_date")
        st.area_chart(cum_rev)

if model_col:
    st.subheader("🚘 Number of Trips per Car Model")
    st.bar_chart(trips_merged.groupby(model_col).size().sort_values(ascending=False))

if city_col:
    if "duration_min" in trips_merged.columns:
        st.subheader("⏱️ Average Trip Duration by City (minutes)")
        st.bar_chart(trips_merged.groupby(city_col)["duration_min"].mean().sort_values(ascending=False))

    if revenue_col:
        st.subheader("🏙️ Revenue by City")
        st.bar_chart(trips_merged.groupby(city_col)[revenue_col].sum().sort_values(ascending=False))

if brand_col and distance_col:
    st.subheader("🔍 Bonus – Average Trip Distance by Brand (km)")
    st.bar_chart(trips_merged.groupby(brand_col)[distance_col].mean().sort_values(ascending=False))
