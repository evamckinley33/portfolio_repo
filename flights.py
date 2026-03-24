import os
import streamlit as st
import pandas as pd
import requests

SERP_API_KEY = os.getenv("SERP_API_KEY")

st.title("Flight Finder✈️")

# -------------------------
# USER INPUTS
# -------------------------

st.sidebar.header("Travel Inputs")

departure_location = st.sidebar.text_input("Your Starting Location (City or ZIP)")

origins = st.sidebar.text_input(
    "Origin Airport(s) Code (comma separated)",
    "MSN,MKE,ORD"
).upper().split(",")

destinations = st.sidebar.text_input(
    "Destination Airport(s) Code (comma separated)",
    "LGA,JFK,HPN"
).upper().split(",")

transport_modes = st.sidebar.multiselect(
    "Available Transport to Airport",
    ["Drive", "Uber", "Public Transit"],
    default=["Drive"]
)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

# -------------------------
# HELPER: DISTANCE FUNCTION
# -------------------------

def get_distance_time(origin, airport_code):
    try:
        url = "https://serpapi.com/search"

        params = {
            "engine": "google_maps",
            "q": f"{origin} to {airport_code} airport",
            "api_key": SERP_API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        routes = data.get("directions", [{}])[0]

        distance_text = routes.get("distance", "0 mi")
        duration_text = routes.get("duration", "0 mins")

        distance = float(distance_text.split()[0])
        duration = int(duration_text.split()[0])

        return distance, duration

    except:
        return 50, 60  # fallback

# -------------------------
# HELPER: COST MODEL
# -------------------------

def estimate_ground(distance, duration, modes):
    costs = []
    times = []

    for mode in modes:

        if mode == "Drive":
            cost = distance * 0.5  # gas estimate
            time = duration

        elif mode == "Uber":
            cost = 2.5 * distance
            time = duration * 1.2

        elif mode == "Public Transit":
            cost = 5
            time = duration * 1.8

        costs.append(cost)
        times.append(time)

    return min(costs), min(times)

# -------------------------
# SEARCH BUTTON
# -------------------------

if st.button("Search Flights"):

    live_flights = {}
    flight_details = {}

    with st.spinner("Searching flights..."):

        for org in origins:

            # GET DISTANCE TO AIRPORT
            distance, duration = get_distance_time(departure_location, org)

            ground_cost, ground_time = estimate_ground(
                distance, duration, transport_modes
            )

            for dest in destinations:

                url = "https://serpapi.com/search"

                params = {
                    "engine": "google_flights",
                    "departure_id": org,
                    "arrival_id": dest,
                    "outbound_date": str(departure_date),
                    "return_date": str(return_date),
                    "currency": "USD",
                    "api_key": SERP_API_KEY
                }

                try:
                    response = requests.get(url, params=params)
                    results = response.json()

                    flight_list = results.get("best_flights") or results.get("other_flights")

                    if flight_list:

                        best = flight_list[0]

                        price = best.get("price", 9999)
                        air_time = best.get("total_duration", 150) * 2

                        segments = best.get("flights", [])

                        flight_num = segments[0].get("flight_number", "N/A") if segments else "N/A"
                        airline = segments[0].get("airline", "Unknown") if segments else "Unknown"

                        booking_url = results.get("search_metadata", {}).get("google_flights_url", "")

                        total_cost = ground_cost + price
                        total_time = ground_time + air_time

                        score = 0.5 * total_cost + 0.5 * total_time

                        live_flights[(org, dest)] = {
                            "cost": total_cost,
                            "time": total_time,
                            "score": score,
                            "flight": f"{airline} {flight_num}",
                            "link": booking_url
                        }

                except Exception as e:
                    st.write(f"Error for {org} → {dest}")
                    st.write(e)

    # -------------------------
    # RESULTS
    # -------------------------

    if live_flights:

        df = pd.DataFrame([
            {
                "Origin": k[0],
                "Destination": k[1],
                "Flight": v["flight"],
                "Total Cost": v["cost"],
                "Total Time": v["time"],
                "Score": v["score"],
                "Link": v["link"]
            }
            for k, v in live_flights.items()
        ])

        optimal = df.loc[df["Score"].idxmin()]

        st.subheader("🏆 Optimal Route")

        st.success(
            f"{optimal['Origin']} → {optimal['Destination']} | "
            f"{optimal['Flight']} | "
            f"${round(optimal['Total Cost'], 2)}"
        )

        st.markdown(f"[Book Flight]({optimal['Link']})")

        st.subheader("All Options")
        st.dataframe(df)
