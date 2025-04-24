import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import mysql.connector
from datetime import datetime, timedelta

def update_plane_schedule(plane_id, date):
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
                WHERE plane = {plane_id} AND DATE(departure_date_time) = DATE('{date}')
                ORDER BY Flights.departure_date_time ASC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            connection.close()
            df = pd.DataFrame([
                {
                    "id": row[0],
                    "source": row[1],
                    "destination": row[2],
                    "departure": row[3],
                    "arrival": row[4],
                    "source_latitude": float(row[7]),
                    "source_longitude": float(row[8]),
                    "destination_latitude": float(row[9]),
                    "destination_longitude": float(row[10])
                }
                for row in rows
            ])
            df["tooltip"] = df.apply(
                lambda row: f"Flight {row['id']}:\n{row['source']} → {row['destination']}\nDep: {row['departure']} | Arr: {row['arrival']}",
                axis=1
            )
            flight_data["label"] = ""
            flight_data.loc[flight_data.index[0], "label"] = "Start"
            flight_data.loc[flight_data.index[-1], "label"] = "End"
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
    flight_data = update_plane_schedule(plane_id, date)

    if flight_data is not None and not flight_data.empty:

        n = len(flight_data)
        colors = np.linspace(0, 255, n).astype(int)

        flight_data["arc_red"] = colors
        flight_data["arc_green"] = 255 - colors
        flight_data["arc_blue"] = 100  # keep blue fixed or vary too
        flight_data["arc_alpha"] = 80  # transparency

        arc_layer = pdk.Layer(
            "ArcLayer",
            data=flight_data,
            get_source_position=["source_longitude", "source_latitude"],
            get_target_position=["destination_longitude", "destination_latitude"],
            get_width=8,
            get_source_color="arc_color",
            get_target_color="arc_color",
            pickable=True,
            auto_highlight=True,
        )

        text_layer = pdk.Layer(
            "TextLayer",
            data=flight_data[flight_data["label"] != ""],  # Only label rows with text
            get_position=["mid_lon", "mid_lat"],  # or ["source_lon", "source_lat"]
            get_text="label",
            get_size=20,
            get_color=[255, 255, 255],
            background=True,
        )


        deck = pdk.Deck(
            layers=[arc_layer, text_layer],
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
