import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from report_generator import generate_pdf_report
from traffic_api import search_location, fetch_traffic
from prediction import predict_congestion
from datetime import datetime
import plotly.graph_objects as go

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="🚦 Real-Time Traffic Congestion Prediction",
    layout="wide"
)

# --------------------------
# AUTO REFRESH (30 sec)
# --------------------------
count = st_autorefresh(interval=30000, limit=None, key="refresh")

# --------------------------
# SESSION STATE (History)
# --------------------------
if "speed_history" not in st.session_state:
    st.session_state.speed_history = []

# --------------------------
# CUSTOM CSS
# --------------------------
st.markdown("""
<style>

.big-title {
    text-align:center;
    font-size:42px;
    font-weight:bold;
    margin-bottom:20px;
}

.metric-card {
    background-color:#1e1e1e;
    padding:25px;
    border-radius:15px;
    text-align:center;
    box-shadow: 0px 0px 20px rgba(0,0,0,0.4);
}

.refresh-text {
    text-align:center;
    font-size:14px;
    color:gray;
    margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------
# TITLE
# --------------------------
st.markdown('<div class="big-title">🚦 Real-Time Traffic Congestion Prediction </div>', unsafe_allow_html=True)
st.markdown('<div class="refresh-text">🔄 Auto refreshing every 30 seconds</div>', unsafe_allow_html=True)
st.caption(f"🔄 Refresh count: {count}")

# --------------------------
# MODE SELECTOR (ADD-ON)
# --------------------------
mode = st.radio(
    "Select Mode",
    ["Single City Dashboard", "Multi City Comparison", "India Heatmap"]
)

# =========================================================
# ============= ORIGINAL SINGLE CITY ======================
# =========================================================
if mode == "Single City Dashboard":

    # --------------------------
    # SEARCH SECTION
    # --------------------------
    st.markdown("### 🔎 Search Location")
    search_query = st.text_input("", placeholder="Enter City / Road / Area")

    lat = None
    lon = None
    address = None

    if search_query:
        lat, lon, address = search_location(search_query)

        if lat:
            st.success("Location Found")
        else:
            st.error("Location not found")

    # --------------------------
    # MAP SECTION
    # --------------------------
    st.markdown("## 🗺 Live Location Map")

    if lat:
        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon]).add_to(m)
    else:
        m = folium.Map(location=[22.5, 78.9], zoom_start=5)

    st_folium(m, height=500, use_container_width=True)

    # --------------------------
    # TRAFFIC + ML SECTION
    # --------------------------
    if lat:

        st.markdown(f"### 📍 Location: {address}")

        current_speed, free_speed = fetch_traffic(lat, lon)

        if current_speed:

            # Store speed history
            st.session_state.speed_history.append(current_speed)
            if len(st.session_state.speed_history) > 10:
                st.session_state.speed_history.pop(0)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    🚗<br>
                    <b>Current Speed</b><br>
                    <h1>{current_speed} km/h</h1>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    🛣<br>
                    <b>Free Flow Speed</b><br>
                    <h1>{free_speed} km/h</h1>
                </div>
                """, unsafe_allow_html=True)


            # --------------------------
            # TRAFFIC TREND INDICATOR
            # --------------------------

            if len(st.session_state.speed_history) >= 2:
                previous_speed = st.session_state.speed_history[-2]
                latest_speed = st.session_state.speed_history[-1]

                st.markdown("## 📈 Traffic Trend")

                if latest_speed > previous_speed:
                    st.success("🟢 Traffic Improving (Speed Increasing)")
                elif latest_speed < previous_speed:
                    st.error("🔴 Traffic Increasing (Speed Decreasing)")
                else:
                    st.warning("🟡 Traffic Stable")


            # ML Prediction
            prediction, percent, color = predict_congestion(current_speed, free_speed)

            st.markdown("## 🧠 ML Congestion Prediction")

            st.markdown(f"""
            <div style="
                padding:30px;
                border-radius:15px;
                background-color:{color};
                text-align:center;
                color:white;
                font-size:26px;
                font-weight:bold;">
                🚦 Congestion Level: {prediction}
            </div>
            """, unsafe_allow_html=True)


            # Gauge meter
            st.markdown("## 🎯 Congestion Level Meter")

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=percent,
                title={'text': "Congestion %"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 40], 'color': "green"},
                        {'range': [40, 70], 'color': "orange"},
                        {'range': [70, 100], 'color': "red"},
                    ],
                }
            ))

            st.plotly_chart(fig, use_container_width=True)


            # Peak
            current_hour = datetime.now().hour
            st.markdown("## ⏰ Traffic Time Analysis")

            is_peak = (8 <= current_hour <= 11) or (17 <= current_hour <= 21)

            if 8 <= current_hour <= 11:
                st.error("🔴 Morning Peak Hour (Office Rush Time)")
            elif 17 <= current_hour <= 21:
                st.error("🔴 Evening Peak Hour (Return Rush Time)")
            elif 12 <= current_hour <= 16:
                st.warning("🟡 Moderate Traffic Hours")
            else:
                st.success("🟢 Non-Peak Hours (Low Traffic Expected)")


            # Advisory
            st.markdown("## 🚨 Smart Travel Advisory")

            if prediction == "High" and is_peak:
                st.error("❌ Avoid This Route Now (High Congestion + Peak Hour)")
            elif prediction == "High":
                st.warning("⚠ Heavy Traffic Detected – Travel with Extra Time")
            elif prediction == "Medium" and is_peak:
                st.warning("⚠ Moderate Congestion During Peak Hours")
            elif prediction == "Medium":
                st.info("🚗 Traffic Moderate – Plan Accordingly")
            else:
                st.success("✅ Safe to Travel – Traffic is Smooth")


            # Risk
            st.markdown("## 📊 Route Risk Score")

            risk_score = percent

            if is_peak:
                risk_score += 10

            speed_ratio = current_speed / free_speed
            if speed_ratio < 0.5:
                risk_score += 10

            risk_score = min(risk_score, 100)

            st.metric("🚨 Risk Score (0-100)", risk_score)

            if risk_score >= 80:
                st.error("🔴 Very High Route Risk")
            elif risk_score >= 50:
                st.warning("🟡 Moderate Route Risk")
            else:
                st.success("🟢 Low Route Risk")


            # History
            st.markdown("## 📊 Traffic Speed Trend (Last 10 Refreshes)")
            st.line_chart(st.session_state.speed_history)


            # --------------------------
            # DOWNLOAD REPORT BUTTON
            # --------------------------

            st.markdown("## 📥 Download Traffic Report (PDF)")

            pdf_data = generate_pdf_report(
                "Single City Dashboard",
                {
                    "location": address,
                    "current_speed": current_speed,
                    "free_speed": free_speed,
                    "prediction": prediction,
                    "risk_score": risk_score
                }
            )
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name="Traffic_Report.pdf",
                mime="application/pdf"
            )
        else:
            st.error("No traffic data found for this location.")


# =========================================================
# ================= MULTI CITY ============================
# =========================================================
elif mode == "Multi City Comparison":

    st.markdown("## 🌆 Multi City Comparison")

    city_input = st.text_input("Enter Cities (comma separated)")

    if city_input:

        city_list = [city.strip() for city in city_input.split(",")]

        if len(city_list) < 2:
            st.warning("⚠ Please enter at least 2 cities separated by comma.")
        else:

            results = []

            for city in city_list:

                lat_c, lon_c, address_c = search_location(city)

                if lat_c:

                    current_speed_c, free_speed_c = fetch_traffic(lat_c, lon_c)

                    if current_speed_c:

                        prediction_c, percent_c, _ = predict_congestion(current_speed_c, free_speed_c)

                        current_hour = datetime.now().hour
                        is_peak = (8 <= current_hour <= 11) or (17 <= current_hour <= 21)

                        risk_c = percent_c

                        if is_peak:
                            risk_c += 10

                        speed_ratio_c = current_speed_c / free_speed_c
                        if speed_ratio_c < 0.5:
                            risk_c += 10

                        risk_c = min(risk_c, 100)

                        results.append({
                            "City": city.title(),
                            "Speed (km/h)": current_speed_c,
                            "Congestion": prediction_c,
                            "Risk Score": risk_c
                        })

            if results:


                # Convert to DataFrame
                import pandas as pd
                import plotly.express as px

                df = pd.DataFrame(results)

                # Sort highest risk first
                df = df.sort_values(by="Risk Score", ascending=False).reset_index(drop=True)

                # ----------------------------------
                # 🏆 Highest Risk Highlight
                # ----------------------------------
                st.markdown("## 🏆 Highest Risk City")

                highest_city = df.iloc[0]["City"]
                highest_risk = df.iloc[0]["Risk Score"]

                st.error(f"🚨 Highest Risk: {highest_city} ({highest_risk})")

                # ----------------------------------
                # 🥇 Ranking Badges
                # ----------------------------------
                st.markdown("## 🥇 Risk Ranking")

                medals = ["🥇", "🥈", "🥉"]

                for i in range(min(3, len(df))):
                    st.write(f"{medals[i]} {df.loc[i,'City']} — Risk: {df.loc[i,'Risk Score']}")

                # ----------------------------------
                # 📊 Risk Summary
                # ----------------------------------
                st.markdown("## 📊 Risk Summary")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Total Cities", len(df))
                col2.metric("High Risk", len(df[df["Risk Score"] >= 80]))
                col3.metric("Medium Risk", len(df[(df["Risk Score"] >= 50) & (df["Risk Score"] < 80)]))
                col4.metric("Low Risk", len(df[df["Risk Score"] < 50]))

                # ----------------------------------
                # 🤖 Smart Recommendation
                # ----------------------------------
                st.markdown("## 🤖 Smart Recommendation")

                lowest_city = df.iloc[-1]["City"]

                if highest_risk >= 80:
                    st.error(f"❌ Avoid {highest_city} Today")
                else:
                    st.warning(f"⚠ {highest_city} has highest traffic")

                st.success(f"✅ Safest City: {lowest_city}")

                # ----------------------------------
                # 📊 Bar Chart
                # ----------------------------------
                st.markdown("## 📊 Risk Comparison Chart")

                fig = px.bar(
                    df,
                    x="City",
                    y="Risk Score",
                    color="Risk Score",
                    color_continuous_scale=["green", "orange", "red"]
                )

                st.plotly_chart(fig, use_container_width=True)

                # ----------------------------------
                # 📋 Final Table
                # ----------------------------------
                st.markdown("## 📋 Detailed Table")
                st.dataframe(df, use_container_width=True)

            else:
                st.error("❌ No valid traffic data found.")


            # --------------------------
            # DOWNLOAD REPORT BUTTON
            # --------------------------    

            st.markdown("## 📥 Download Traffic Report (PDF)")

            pdf_data = generate_pdf_report("Multi City Comparison", results)

            st.download_button(
                label="📄 Download Comparison Report",
                data=pdf_data,
                file_name="Multi_City_Report.pdf",
                mime="application/pdf"
            )

# =========================================================
# ================= INDIA HEATMAP =========================
# =========================================================

elif mode == "India Heatmap":

    st.markdown("## 🗺 India Traffic Heatmap")

    city_input = st.text_input("Enter Cities for Heatmap (comma separated)")

    heatmap_data = []
    table_data = []

    if city_input:

        from folium.plugins import HeatMap

        # Clean city names
        city_list = [city.strip().title() for city in city_input.split(",")]

        for city in city_list:

            lat_c, lon_c, address_c = search_location(city)

            # If city not found
            if lat_c is None or lon_c is None:
                st.warning(f"⚠ City not found: {city}")
                continue

            current_speed_c, free_speed_c = fetch_traffic(lat_c, lon_c)

            # If traffic API failed
            if current_speed_c is None or free_speed_c is None:
                st.warning(f"⚠ Traffic data unavailable for {city}")
                continue

            prediction_c, percent_c, _ = predict_congestion(
                current_speed_c, free_speed_c
            )

            # Heatmap data
            heatmap_data.append([lat_c, lon_c, percent_c])

            # Table data with lat/lon stored
            table_data.append({
                "City": city,
                "Risk %": percent_c,
                "Congestion Level": prediction_c,
                "Lat": lat_c,
                "Lon": lon_c
            })


    # -----------------------------------------------------
    # Show Heatmap if Data Found
    # -----------------------------------------------------

    if len(heatmap_data) > 0:

        import folium
        from streamlit_folium import st_folium
        import pandas as pd
        import plotly.express as px

        # India Map
        m = folium.Map(location=[22.5, 78.9], zoom_start=5)

        # Heatmap Layer
        HeatMap(
            heatmap_data,
            radius=40,
            blur=30,
            min_opacity=0.5,
            max_zoom=8
        ).add_to(m)

        # -----------------------------
        # Circle Markers
        # -----------------------------

        for row in table_data:

            lat_c = row["Lat"]
            lon_c = row["Lon"]

            if row["Risk %"] >= 70:
                marker_color = "red"
            elif row["Risk %"] >= 40:
                marker_color = "orange"
            else:
                marker_color = "green"

            popup_html = f"""
            <b>City:</b> {row['City']} <br>
            <b>Congestion:</b> {row['Congestion Level']} <br>
            <b>Risk %:</b> {row['Risk %']}%
            """

            folium.CircleMarker(
                location=[lat_c, lon_c],
                radius=10,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.7,
                popup=popup_html
            ).add_to(m)

        st_folium(m, height=600, use_container_width=True)

        # -------------------------------------------------
        # ANALYTICS
        # -------------------------------------------------

        df_heat = pd.DataFrame(table_data)

        df_heat = df_heat.sort_values(
            by="Risk %", ascending=False
        ).reset_index(drop=True)

        st.markdown("## 🏆 Heatmap Risk Ranking")

        highest_city = df_heat.iloc[0]["City"]
        highest_risk = df_heat.iloc[0]["Risk %"]

        safest_city = df_heat.iloc[-1]["City"]
        safest_risk = df_heat.iloc[-1]["Risk %"]

        st.error(f"🚨 Highest Risk City: {highest_city} ({highest_risk}%)")
        st.success(f"✅ Safest City: {safest_city} ({safest_risk}%)")

        # Top 3 Cities
        st.markdown("### 🥇 Top 3 High Risk Cities")

        medals = ["🥇", "🥈", "🥉"]

        for i in range(min(3, len(df_heat))):

            st.write(
                f"{medals[i]} {df_heat.loc[i,'City']} — {df_heat.loc[i,'Risk %']}%"
            )

        # -----------------------------
        # Risk Metrics
        # -----------------------------

        st.markdown("### 📊 Risk Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "High Risk",
            len(df_heat[df_heat["Risk %"] >= 70])
        )

        col2.metric(
            "Medium Risk",
            len(df_heat[(df_heat["Risk %"] >= 40) & (df_heat["Risk %"] < 70)])
        )

        col3.metric(
            "Low Risk",
            len(df_heat[df_heat["Risk %"] < 40])
        )

        # -----------------------------
        # Chart
        # -----------------------------

        st.markdown("## 📊 Heatmap Risk Comparison Chart")

        fig = px.bar(
            df_heat,
            x="City",
            y="Risk %",
            color="Risk %",
            color_continuous_scale=["green", "orange", "red"],
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

        # -----------------------------
        # Table
        # -----------------------------

        st.markdown("## 📊 City Risk Table")

        st.dataframe(
            df_heat[["City", "Risk %", "Congestion Level"]],
            use_container_width=True
        )

        # -----------------------------
        # PDF Download
        # -----------------------------

        st.markdown("## 📥 Download Traffic Report (PDF)")

        pdf_data = generate_pdf_report("India Heatmap", table_data)

        st.download_button(
            label="📄 Download Heatmap Report",
            data=pdf_data,
            file_name="Heatmap_Report.pdf",
            mime="application/pdf"
        )

    elif city_input:

        st.error("❌ No valid traffic data found for the entered cities.")

