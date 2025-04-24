import requests
import mysql.connector
from datetime import datetime, timedelta
import warnings
from math import radians, sin, cos, sqrt, atan2, exp
warnings.filterwarnings("ignore", category=UserWarning, module="pandas.io.sql")

def train_poisson_regression(x_data, y_data, lr=0.0001, epochs=10000):
    a = 0.0  # intercept
    b = 0.0  # slope

    for epoch in range(epochs):
        grad_a = 0.0
        grad_b = 0.0
        loss = 0.0

        for x, y in zip(x_data, y_data):
            x -= 2023
            pred = exp(a + b * x)
            error = pred - y
            loss += error ** 2

            grad_a += error * pred  # ∂L/∂a
            grad_b += error * pred * x  # ∂L/∂b

        # update parameters
        a -= lr * grad_a / len(x_data)
        b -= lr * grad_b / len(x_data)

    return a, b

def predict_poisson(x, a, b):
    x -= 2023
    return exp(a + b * x)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def valid_plane(airplanes, source, destination, is_business):
    pass

def update_seat_demand(source, destination, demand, average_seat_count):
    average_seat_count = float(average_seat_count)
    for row in demand:
        if row[0] == source and row[1] == destination:
            row[2] -= average_seat_count

def update_weather_and_flights():
    # UPDATE WEATHER *********************************************************************************************
    connection = mysql.connector.connect(
        host="cs3190.cjek8eem4rj2.us-east-1.rds.amazonaws.com",
        user="elwalker627",
        password="cybhaz-Gabbo5-gycqiz",
        database="CS3960",
        port=3306
    )

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Airports;")
    airports = cursor.fetchall()

    API_KEY = "4704c05879e73d36df3c173ed1598227"
    for airport in airports:
        lat, lon = airport[2], airport[3]
        airport_id = airport[0]

        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        weather_data = response.json()

        for three_hr_block in weather_data['list']:
            rain = 'rain' in three_hr_block
            snow = 'snow' in three_hr_block
            wind_speed = three_hr_block['wind']['speed']
            start_time = datetime.fromtimestamp(three_hr_block['dt'])
            temp = three_hr_block['main']['temp']
            end_time = start_time + timedelta(hours=3)

            if(rain and three_hr_block['rain']['3h'] > 10):
                print("Heavy Rain 60")
                cursor.execute("INSERT INTO Weather (affected_airport, start_date_time, end_date_time, weather_type) VALUES (%s, %s, %s, %s);", (airport_id, start_time, end_time, 1))
            if(snow and three_hr_block['snow']['3h'] > 10):
                print("Snow 63")
                cursor.execute("INSERT INTO Weather (affected_airport, start_date_time, end_date_time, weather_type) VALUES (%s, %s, %s, %s);", (airport_id, start_time, end_time, 2))
            if(three_hr_block['main'] == "Thunderstorm"):
                print("Thunderstorm 66")
                cursor.execute("INSERT INTO Weather (affected_airport, start_date_time, end_date_time, weather_type) VALUES (%s, %s, %s, %s);", (airport_id, start_time, end_time, 3))
            if((rain or snow) and temp < 0):
                print("Icing 69")
                cursor.execute("INSERT INTO Weather (affected_airport, start_date_time, end_date_time, weather_type) VALUES (%s, %s, %s, %s);", (airport_id, start_time, end_time, 4))
            if(three_hr_block['main'] == "Fog"):
                print("Fog 72")
                cursor.execute("INSERT INTO Weather (affected_airport, start_date_time, end_date_time, weather_type) VALUES (%s, %s, %s, %s);", (airport_id, start_time, end_time, 5))
            if wind_speed > 30:
                print("Strong Winds 75")
                cursor.execute("INSERT INTO Weather (affected_airport, start_date_time, end_date_time, weather_type) VALUES (%s, %s, %s, %s);", (airport_id, start_time, end_time, 6))

    connection.commit()

    # UPDATE FLIGHTS *********************************************************************************************

    # CONCLUDE ***************************************************************************************************
    cursor.close()
    connection.close()

def move_flights_to_historical(date):
    connection = mysql.connector.connect(
        host="cs3190.cjek8eem4rj2.us-east-1.rds.amazonaws.com",
        user="elwalker627",
        password="cybhaz-Gabbo5-gycqiz",
        database="CS3960",
        port=3306
    )
    cursor = connection.cursor(dictionary=True)  # Use dictionary cursor to access by column name

    # Step 1: Fetch the flights for the given date
    cursor.execute("""
        SELECT *
        FROM Flights
        JOIN Airplanes ON Flights.plane = Airplanes.id
        JOIN Airplane_Models ON Airplanes.model = Airplane_Models.id
        WHERE DATE(departure_date_time) = DATE(%s);
    """, (date,))
    flights_to_remove = cursor.fetchall()

    # Step 2: Disable SQL_SAFE_UPDATES and delete the rows (run these in separate .execute calls)
    cursor.execute("SET SQL_SAFE_UPDATES = 0;")
    delete_flights_in_batches(cursor, date)
    cursor.execute("SET SQL_SAFE_UPDATES = 1;")

    # Step 3: Insert into Historical_Flight_Data
    for flight in flights_to_remove:
        cursor.execute("""
            INSERT INTO Historical_Flight_Data (
                source, destination, departure_date_time,
                business_class_count, first_class_count,
                main_count, delta_comfort_plus_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (
            flight['source'],
            flight['destination'],
            flight['departure_date_time'],
            flight['business_class_seat_count'],
            flight['first_class_seat_count'],
            flight['main_seat_count'],
            flight['delta_comfort_plus_seat_count']
        ))

    # Step 4: Cleanup
    cursor.close()
    connection.commit()
    connection.close()

def delete_flights_in_batches(cursor, date, batch_size=500):
    total_deleted = 0
    while True:
        cursor.execute("""
            DELETE FROM Flights 
            WHERE DATE(departure_date_time) = DATE(%s) 
            LIMIT %s;
        """, (date, batch_size))
        rows_affected = cursor.rowcount
        total_deleted += rows_affected
        if rows_affected < batch_size:
            break
    print(f"Deleted {total_deleted} flights from {date}")

def plan_one_week_out():
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    move_flights_to_historical(yesterday)
    target_day = (now + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    plan_flights(target_day)

def plan_flights(start):
    # UPDATE WEATHER *********************************************************************************************
    connection = mysql.connector.connect(
        host="cs3190.cjek8eem4rj2.us-east-1.rds.amazonaws.com",
        user="elwalker627",
        password="cybhaz-Gabbo5-gycqiz",
        database="CS3960",
        port=3306
    )
    year = start.year
    year_day = start.timetuple().tm_yday

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Airports;")
    airports = cursor.fetchall()
    airport_size = len(airports)

    time_blocks = [(start + timedelta(hours=i)) for i in range(0, 24, 6)]

    flight_demands = [[[0 for _ in range(4)] for _ in range(airport_size)] for _ in range(airport_size)]
    flattened_flight_demands = []
    airplane_locations = [[] for _ in range(airport_size)]
    query = f"""
SELECT
    ROUND(SUM(am.business_class_seat_count) / COUNT(a.id), 2) AS avg_business_class,
    ROUND(SUM(am.first_class_seat_count) / COUNT(a.id), 2) AS avg_first_class,
    ROUND(SUM(am.delta_comfort_plus_seat_count) / COUNT(a.id), 2) AS avg_comfort_plus,
    ROUND(SUM(am.main_seat_count) / COUNT(a.id), 2) AS avg_main,
    SUM(a.id) AS airplane_count
FROM Airplanes a
JOIN Airplane_Models am ON a.model = am.id;
"""
    cursor.execute(query)
    airplane_seat_averages_pd = cursor.fetchall()
    airplane_seat_averages_arr = list(airplane_seat_averages_pd[0])
    airplane_seat_averages = [airplane_seat_averages_arr[0] + airplane_seat_averages_arr[1], airplane_seat_averages_arr[2], airplane_seat_averages_arr[3]]
    airplane_seat_averages_sum = airplane_seat_averages[0] + airplane_seat_averages[1] + airplane_seat_averages[2]
    airplane_count = airplane_seat_averages_arr[3]
    airplane_seat_averages.append(airplane_seat_averages_sum)

    query = f"""
SELECT 
    0 AS pattern_index,
    f.plane,
    f.destination AS current_airport,
    f.arrival_date_time,
    am.model_name, 
    am.business_class_seat_count, 
    am.first_class_seat_count, 
    am.delta_comfort_plus_seat_count, 
    am.main_seat_count, 
    am.business_class_seat_count+am.first_class_seat_count+am.delta_comfort_plus_seat_count+am.main_seat_count AS total_seat_count, 
    am.maintenance_between_flights_hrs, 
    am.maintenance_daily_hrs, 
    am.maintenance_weekly_hrs, 
    am.maintenance_monthly_hrs, 
    am.maintenance_annually_hrs, 
    am.speed_kmph, 
    am.kmpg, 
    am.fuel_capacity_gallons,
    Destination_Airports.latitude AS destination_latitude,
    Destination_Airports.longitude AS destination_longitude,
    Source_Airports.latitude AS source_latitude,
    Source_Airports.longitude AS source_longitude
FROM Flights f
JOIN (
    SELECT 
        plane,
        MAX(arrival_date_time) AS latest_arrival
    FROM Flights
    GROUP BY plane
) latest_flight ON f.plane = latest_flight.plane 
               AND f.arrival_date_time = latest_flight.latest_arrival
JOIN Airplanes a ON f.plane = a.id
JOIN Airports Destination_Airports ON Destination_Airports.id = f.destination
JOIN Airports Source_Airports ON Source_Airports.id = f.source
JOIN Airplane_Models am ON a.model = am.id;
"""
    cursor.execute(query)
    airplanes = cursor.fetchall()
    for airplane in airplanes:
        airplane_locations[airplane[2]-1].append(airplane)

    for start_time in time_blocks:
        demand_total = 0
        count = 0
        for airplanes in airplane_locations:
            for i in range(len(airplanes)):
                airplane = list(airplanes[i])
                airplane[0] = start_time
                airplanes[i] = airplane
        for source in airports:
            source_id = source[0]
            for destination in airports:
                destination_id = destination[0]
                query = f"""
SELECT 
    departure_date_time,
    YEAR(departure_date_time) AS year,
    SUM(business_class_count) + SUM(first_class_count) AS first_business_class_count,
    SUM(main_count) AS main_count, 
    SUM(delta_comfort_plus_count) AS delta_comfort_plus_count
FROM Historical_Flight_Data
WHERE MONTH(departure_date_time) = MONTH('{start_time}') AND DAY(departure_date_time) = DAY('{start_time}') AND HOUR(departure_date_time) >= HOUR('{start_time}') AND HOUR(departure_date_time) <= HOUR('{start_time+timedelta(hours=5, minutes=59)}') AND source={source_id} AND destination={destination_id}
GROUP BY year
"""
                rows = 0
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    cursor.execute(query)
                    rows = cursor.fetchall()
                if not rows:
                    continue
                if len(rows) == 1:
                    if rows[0][1] == 2023:
                        rows.append((rows[0][0].replace(hour=0, minute=0, second=0, microsecond=0), 2024, 0, 0, 0))
                        rows = tuple(rows)
                    else:
                        rows.append((rows[0][0].replace(hour=0, minute=0, second=0, microsecond=0), 2023, 0, 0, 0))
                        rows = tuple(rows)

                X = [float(row[1]) for row in rows]

                y = [float(row[2]) for row in rows]  
                a, b = train_poisson_regression(X, y)
                predicted = predict_poisson(year, a, b)
                flight_demands[source_id-1][destination_id-1][0] = predicted

                y = [float(row[3]) for row in rows]  
                a, b = train_poisson_regression(X, y)
                predicted = predict_poisson(year, a, b)
                flight_demands[source_id-1][destination_id-1][1] = predicted

                y = [float(row[4]) for row in rows]  
                a, b = train_poisson_regression(X, y)
                predicted = predict_poisson(year, a, b)
                flight_demands[source_id-1][destination_id-1][2] = predicted

                flight_demands[source_id-1][destination_id-1][3] = flight_demands[source_id-1][destination_id-1][0] + flight_demands[source_id-1][destination_id-1][1] + flight_demands[source_id-1][destination_id-1][2] + flight_demands[source_id-1][destination_id-1][3]
                flattened_flight_demands.append([source_id, destination_id, flight_demands[source_id-1][destination_id-1][3]])
                demand_total += flattened_flight_demands[count][2]
                count += 1

        print("Flattened Flight Demands 224:", flattened_flight_demands)
        n = len(flight_demands)
        clean_data = [
            [  # for each source
                [  # for each destination
                    float(x[0]) if hasattr(x, '__len__') and not isinstance(x, (str, bytes)) else float(x)
                    for x in flight_demands[i][j]
                ]
                for j in range(len(flight_demands[i]))
            ]
            for i in range(len(flight_demands))
        ]
        sorted_data = sorted(flattened_flight_demands, key=lambda row: row[2], reverse=True)

        # Optimize here
        create_schedule(airplane_locations, start_time, airports, flattened_flight_demands, airplane_seat_averages[3], cursor)


    # ADD FLIGHTS ************************************************************************************************
    connection.commit()
    cursor.close()
    connection.close()

def create_schedule(airplanes, start_time, airports, demands, airplane_seat_average, cursor):
    max_end_time = start_time + timedelta(hours=5, minutes=59)
    keep_scheduling = True
    filtered_sorted = sorted(demands, key=lambda row: row[2], reverse=True)
    while keep_scheduling:
        filtered_sorted = sorted(filtered_sorted, key=lambda row: row[2], reverse=True)
        if len(filtered_sorted) == 0:
            keep_scheduling = False
            break
        if(filtered_sorted[0][2] <= 0):
            print("Scheduling Finished 259")
            keep_scheduling = False
            break
        print("HERE 262")
        flight = filtered_sorted[0]
        source_airport = airports[flight[0]-1]
        destination_airport = airports[flight[1]-1]
        distance = haversine(source_airport[2], source_airport[3], destination_airport[2], destination_airport[3])
        print("Distance 267:", distance)
        history = set()
        history.add(source_airport[0])
        airplane = select_plane(airplanes, source_airport[0], distance, filtered_sorted, airplane_seat_average, max_end_time, history, cursor)
        if airplane == None:
            filtered_sorted = filtered_sorted[1:]
            continue
        next_start_time = airplane[0]
        end_time = next_start_time + timedelta(hours=distance/float(airplane[15]))
        airplane[0] = end_time + timedelta(hours=float(airplane[10]))
        airplanes[source_airport[0]-1].remove(airplane)
        airplanes[destination_airport[0]-1].append(airplane)
        cursor.execute("INSERT INTO Flights (source, destination, plane, departure_date_time, arrival_date_time) VALUES (%s, %s, %s, %s, %s);", (next_start_time, destination_airport[0], airplane[1], airplane[0], end_time))
        update_seat_demand(source_airport[0], destination_airport[0], filtered_sorted, airplane_seat_average)

def select_plane(airplanes, source, distance, demand, average_seats, max_end_time, history, cursor):
    if len(airplanes) == 0:
        return None
    airplane_options = airplanes[source-1]
    index = 0
    while index < len(airplane_options):
        airplane = airplane_options[index]
        index += 1
        airplane_on_time = airplane[0] + timedelta(hours=distance/float(airplane[15])) < max_end_time
        if plane_can_make_distance(distance, airplane) and airplane_on_time:
            return airplane
    
    return flight_to_here(source, demand, airplanes, average_seats, history, distance, max_end_time, len(airplane_options), cursor)

def plane_can_make_distance(distance, plane):
    plane_distance = plane[17]*plane[16]
    return plane_distance >= distance

def flight_to_here(here, demand, airplanes, average_seats, history, distance, max_end_time, airports_count, cursor):
    if len(airplanes) == 0 or len(history) >= airports_count:
        return None
    filtered = [row for row in demand if row[1] == here]
    index =  1
    if len(filtered) == 0:
        return None
    source = filtered[0][0]
    while source in history:
        if source >= len(filtered) or index >= len(filtered):
            return None
        source = filtered[index][0]
        index += 1
    history.add(source)
    plane = select_plane(airplanes, source, distance, demand, average_seats, max_end_time, history, cursor)
    if plane == None:
        return None
    for airplane_sets in airplanes:
        if plane in airplane_sets:
            print("REMOVAL SUCCESS 326")
            airplane_sets.remove(plane)
    airplanes[here-1].append(plane)
    start_time = plane[0]
    end_time = start_time + timedelta(hours=distance/float(plane[15]))
    cursor.execute("INSERT INTO Flights (source, destination, plane, departure_date_time, arrival_date_time) VALUES (%s, %s, %s, %s, %s);", (source, here, plane[1], start_time, end_time))
    update_seat_demand(source, here, demand, average_seats)
    return plane

def lambda_handler(event, context):
    print("Starting to update...")
    update_weather_and_flights()
    print("Starting to plan...")
    plan_one_week_out()
    print("Lambda ran successfully 336")
    return {"statusCode": 200, "body": "Done"}

# lambda_handler(None, None)
# current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
# end_date = current_date + timedelta(days=7)

# while current_date <= end_date:
#     print("Current Date:", current_date)
#     plan_flights(current_date)
#     current_date += timedelta(days=1)