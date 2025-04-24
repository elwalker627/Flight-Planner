import streamlit as st
import pandas as pd
import pydeck as pdk
import mysql.connector
from datetime import datetime, timedelta

def update_plane_schedule(plane_id, date):
    if plane_id.isdigit():
        connection = mysql.connector.connect(
            host="cs3190.cjek8eem4rj2.us-east-1.rds.amazonaws.com",
            user="elwalker627",
            password="cybhaz-Gabbo5-gycqiz",
            database="CS3960",
            port=3306
        )
        cursor = connection.cursor()
        query = f"SELECT Flights.id, Flights.source, Flights.destination, Flights.departure_date_time, Flights.arrival_date_time, Flights.status, Flights.delay_time, Source.latitude, Source.longitude, Destination.latitude, Destination.longitude FROM Flights JOIN Airports Source ON Source.id=Flights.source JOIN Airports Destination ON Destination.id=Flights.destination WHERE plane={plane_id} AND DATE(departure_date_time)=DATE('{date}');"
        st.write("Query:", query)
        cursor.execute(query)
        returner = cursor.fetchall()
        cursor.close()
        connection.close()
        st.write("Returner:", returner)
        return returner
    else:
        return None
    

# Sample flight data (you'd use your real data here)
flight_data = None
keys = ["id", "source", "destination", "departure", "arrival", "status", "delay", "source_latitude", "source_longitude", "destination_latitude", "destination_longitude"]
rows_dicts = None

print("Starting app")
st.title("Flight Schedule Viewer")

plane_id = st.text_input("Enter Plane ID:", "3")
date = st.text_input("Enter Date:", "2025-04-25")
if st.button("Update Schedule"):
    st.write("Button clicked")
    new_data = update_plane_schedule(plane_id, date)
    st.write(new_data)
    if new_data != None:
        st.write("New data")
        flight_data = new_data
        rows_dicts = pd.DataFrame(flight_data, columns=keys)

flight_data = update_plane_schedule(plane_id, date)
rows_dicts = pd.DataFrame(flight_data, columns=keys)

# Add tooltip info
flight_data["tooltip"] = flight_data.apply(
    lambda row: f"Flight {row['id']}: {row['source']} → {row['destination']}<br>Dep: {row['departure']} | Arr: {row['arrival']}",
    axis=1
)

# ArcLayer for flight paths
arc_layer = pdk.Layer(
    "ArcLayer",
    data=flight_data,
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
    data=flight_data,
    get_source_position=["source_lon", "source_lat"],
    get_target_position=["dest_lon", "dest_lat"],
    get_width=8,
    get_tilt=10,
    get_source_color=RED_RGB,
    get_target_color=GREEN_RGB,
    pickable=True,
    auto_highlight=True,
)

# Number labels (optional)
text_layer = pdk.Layer(
    "TextLayer",
    data=flight_data,
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
        zoom=2.7,
        pitch=0,
    ),
    tooltip={"text": "{tooltip}"},
)

st.pydeck_chart(deck)
