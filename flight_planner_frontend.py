import streamlit as st
import pandas as pd
import pydeck as pdk
import mysql.connector
from datetime import datetime, timedelta

def update_plane_schedule(plane_id, date):
    keys = ["id", "source", "destination", "departure", "arrival", "status", "delay", "source_latitude", "source_longitude", "destination_latitude", "destination_longitude"]
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
        returner = pd.DataFrame(returner, columns=keys)
        st.write("Returner:", returner)
        return returner
    else:
        return None
    

# Sample flight data (you'd use your real data here)
flight_data = None

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

flight_data = update_plane_schedule(plane_id, date)

# Add tooltip info
flight_data["tooltip"] = flight_data.apply(
    lambda row: f"Flight {row['id']}: {row['source']} → {row['destination']}<br>Dep: {row['departure']} | Arr: {row['arrival']}",
    axis=1
)
st.write("Tooltip:", flight_data)

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

# Deck map setup
deck = pdk.Deck(
    layers=[arc_layer],
    initial_view_state=pdk.ViewState(
        latitude=39.5,
        longitude=-98.35,
        zoom=2.7,
        pitch=0,
    ),
    tooltip={"text": "{tooltip}"},
)

st.pydeck_chart(deck)
