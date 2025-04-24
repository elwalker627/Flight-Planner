import streamlit as st
import pandas as pd
import pydeck as pdk
import mysql.connector
from datetime import datetime, timedelta

def update_plane_schedule(plane_id, date):
    keys = ["id", "source", "destination", "departure", "arrival", "status", "delay", "source_latitude", "source_longitude", "destination_latitude", "destination_longitude"]
    if plane_id.isdigit():
        try:
            connection = mysql.connector.connect(
                host="cs3190.cjek8eem4rj2.us-east-1.rds.amazonaws.com",
                user="elwalker627",
                password="cybhaz-Gabbo5-gycqiz",
                database="CS3960",
                port=3306
            )
            cursor = connection.cursor()
            query = f"""
                SELECT Flights.id, Source.name, Destination.name, Flights.departure_date_time, Flights.arrival_date_time, 
                       Flights.status, Flights.delay_time, Source.latitude, Source.longitude, 
                       Destination.latitude, Destination.longitude 
                FROM Flights 
                JOIN Airports Source ON Source.id = Flights.source 
                JOIN Airports Destination ON Destination.id = Flights.destination 
                WHERE plane = {plane_id} AND DATE(departure_date_time) = DATE('{date}');
            """
            st.write("Query:", query)
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            connection.close()
            df = pd.DataFrame(rows, columns=keys)
            float_cols = ["source_latitude", "source_longitude", "destination_latitude", "destination_longitude"]
            df[float_cols] = df[float_cols].astype(float)
            df["tooltip"] = df.apply(
                lambda row: f"Flight {row['id']}: {row['source']} → {row['destination']}<br>Dep: {row['departure']} | Arr: {row['arrival']}",
                axis=1
            )
            return df
        except Exception as e:
            st.error(f"Database error: {e}")
            return None
    else:
        st.warning("Plane ID must be an integer.")
        return None

# Streamlit UI
st.title("Flight Schedule Viewer")
plane_id = st.text_input("Enter Plane ID:", "3")
date = st.text_input("Enter Date (YYYY-MM-DD):", "2025-04-25")

flight_data = None

if st.button("Update Schedule"):
    st.write("Loading data...")
    flight_data = update_plane_schedule(plane_id, date)

    if flight_data is not None and not flight_data.empty:
        st.write("Type of flight_data:", type(flight_data))
        st.write(flight_data.head())

        GREEN_RGB = [0, 255, 0, 40]
        RED_RGB = [240, 100, 0, 40]

        arc_layer = pdk.Layer(
            "ArcLayer",
            data=flight_data,
            get_source_position=["source_longitude", "source_latitude"],
            get_target_position=["destination_longitude", "destination_latitude"],
            get_width=8,
            get_source_color=RED_RGB,
            get_target_color=GREEN_RGB,
            pickable=True,
            auto_highlight=True,
        )

        deck = pdk.Deck(
            layers=[arc_layer],
            initial_view_state=pdk.ViewState(
                latitude=39.5,
                longitude=-98.35,
                zoom=3,
                pitch=0,
            ),
            tooltip={"text": "{tooltip}"}
        )

        st.pydeck_chart(deck)
    else:
        st.warning("No flight data found for that plane and date.")
