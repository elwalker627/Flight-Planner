import streamlit as st
import pandas as pd
import pydeck as pdk

# Sample flight data (you'd use your real data here)
flight_data = pd.DataFrame([
    {"flight_num": 1, "source": "SLC", "dest": "JFK", "source_lat": 40.7899, "source_lon": -111.9791,
     "dest_lat": 40.6413, "dest_lon": -73.7781, "departure": "08:00", "arrival": "14:00"},
    {"flight_num": 2, "source": "JFK", "dest": "ATL", "source_lat": 40.6413, "source_lon": -73.7781,
     "dest_lat": 33.6407, "dest_lon": -84.4277, "departure": "16:00", "arrival": "19:00"},
])

st.title("Flight Schedule Viewer")

plane_id = st.text_input("Enter Plane ID:", "N12345")

# Filter your real dataset here
plane_flights = flight_data  # simulate with full data for now

# Add tooltip info
plane_flights["tooltip"] = plane_flights.apply(
    lambda row: f"Flight {row.flight_num}: {row['source']} → {row['dest']}<br>Dep: {row['departure']} | Arr: {row['arrival']}",
    axis=1
)

data = [
    {'start': [40.7899, -111.9791], 'end': [40.6413, -73.7781]},
    {'start': [40.6413, -73.7781], 'end': [33.6407, -84.4277]}
]

# Define the LineLayer
line_layer = pdk.Layer(
    "LineLayer",
    data,
    get_source_position="start",  # Connects start coordinates
    get_target_position="end",    # Connects end coordinates
    get_color=[0, 255, 0, 100],  # Line color (RGBA)
    get_width=2,                  # Line width
)

# ArcLayer for flight paths
arc_layer = pdk.Layer(
    "ArcLayer",
    data=plane_flights,
    get_source_position=["source_lat", "source_lon"],
    get_target_position=["dest_lat", "dest_lon"],
    get_source_color=[0, 128, 255],
    get_target_color=[255, 0, 128],
    auto_highlight=True,
    width_scale=0.0001,
    get_width=5,
    pickable=True,
)

GREEN_RGB = [0, 255, 0, 40]
RED_RGB = [240, 100, 0, 40]

arc_layer = pdk.Layer(
    "ArcLayer",
    data=plane_flights,
    get_source_position=["source_lat", "source_lon"],
    get_target_position=["dest_lat", "dest_lon"],
    get_width="S000 * 2",
    get_tilt=15,
    get_source_color=RED_RGB,
    get_target_color=GREEN_RGB,
    pickable=True,
    auto_highlight=True,
)

# Number labels (optional)
text_layer = pdk.Layer(
    "TextLayer",
    data=plane_flights,
    get_position=["source_lon", "source_lat"],
    get_text="flight_num",
    get_size=20,
    get_color=[0, 0, 0],
    get_angle=0,
    background=True,
)

# Deck map setup
deck = pdk.Deck(
    layers=[arc_layer, text_layer],
    initial_view_state=pdk.ViewState(
        latitude=39.5,
        longitude=-98.35,
        zoom=3.5,
        pitch=0,
    ),
    tooltip={"text": "{tooltip}"},
)

st.pydeck_chart(deck)
