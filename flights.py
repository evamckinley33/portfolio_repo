import streamlit as st
import pandas as pd
import requests

SERP_API_KEY = os.getenv("SERP_API_KEY")

st.title("✈️ Optimal Flight Finder")

origins = ["MSN", "MKE", "ORD"]
destinations = ["LGA", "JFK", "HPN"]

ground_stats = {
    "MSN": {"cost": 0, "time": 130},
    "MKE": {"cost": 50, "time": 310},
    "ORD": {"cost": 69, "time": 480}
}

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

if st.button("Search Flights"):

    live_flights = {}
    flight_details = {}

    with st.spinner("Searching flights..."):

        for org in origins:
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

                        live_flights[(org, dest)] = [price, air_time]

                        flight_details[(org, dest)] = {
                            "code": f"{airline} {flight_num}",
                            "link": booking_url
                        }

                except Exception as e:
                    st.write(f"Error for {org} → {dest}")
                    st.write(e)

    if live_flights:

        rows = []

        for r in live_flights:

            total_cost = ground_stats[r[0]]["cost"] + live_flights[r][0]
            total_time = ground_stats[r[0]]["time"] + live_flights[r][1]

            score = 0.5 * total_cost + 0.5 * total_time

            rows.append({
                "Origin": r[0],
                "Destination": r[1],
                "Flight": flight_details[r]["code"],
                "Total Cost": total_cost,
                "Total Time": total_time,
                "Score": score,
                "Link": flight_details[r]["link"]
            })

        df = pd.DataFrame(rows)

        optimal = df.loc[df["Score"].idxmin()]

        st.subheader("🏆 Optimal Route")

        st.success(
            f"{optimal['Origin']} → {optimal['Destination']} | "
            f"{optimal['Flight']} | "
            f"${optimal['Total Cost']}"
        )

        st.markdown(f"[Book Flight]({optimal['Link']})")

        st.subheader("All Options")

        st.dataframe(df)
