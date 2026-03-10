import joblib
import pandas as pd
from datetime import datetime

# Load trained ML model
model = joblib.load("traffic_model.pkl")

# store previous congestion value
previous_congestion = None


def predict_congestion(current_speed, free_speed):

    global previous_congestion

    # --------------------------
    # CURRENT TIME
    # --------------------------
    hour = datetime.now().hour

    # --------------------------
    # MACHINE LEARNING INPUT
    # --------------------------
    data = pd.DataFrame([{
        "hour": hour,
        "current_speed": current_speed,
        "free_flow_speed": free_speed
    }])

    prediction = model.predict(data)[0]

    # --------------------------
    # SPEED BASED CONGESTION
    # --------------------------

    speed_ratio = current_speed / free_speed
    speed_factor = (1 - speed_ratio) * 100

    # --------------------------
    # PEAK HOUR FACTOR
    # --------------------------

    peak_factor = 0
    if 8 <= hour <= 11 or 17 <= hour <= 21:
        peak_factor = 10

    # --------------------------
    # URBAN TRAFFIC FACTOR
    # --------------------------

    urban_factor = 5

    # --------------------------
    # ML SUPPORT FACTOR
    # --------------------------

    ml_factor = 0

    if prediction == "High":
        ml_factor = 8
    elif prediction == "Medium":
        ml_factor = 4

    # --------------------------
    # ROAD TYPE FACTOR (NEW)
    # --------------------------

    if free_speed > 70:
        road_factor = 5      # highway
    elif free_speed > 40:
        road_factor = 3      # city main road
    else:
        road_factor = 1      # small road

    # --------------------------
    # TRAFFIC DENSITY ESTIMATION (NEW)
    # --------------------------

    density_factor = (free_speed - current_speed) * 0.5

    # --------------------------
    # RAW CONGESTION
    # --------------------------

    congestion_percent = (
        speed_factor
        + peak_factor
        + urban_factor
        + ml_factor
        + road_factor
        + density_factor
    )

    # --------------------------
    # TRAFFIC TREND SMOOTHING
    # --------------------------

    if previous_congestion is not None:
        congestion_percent = (0.7 * congestion_percent) + (0.3 * previous_congestion)

    previous_congestion = congestion_percent

    congestion_percent = max(0, min(congestion_percent, 100))

    # --------------------------
    # CLASSIFICATION
    # --------------------------

    if congestion_percent < 35:
        level = "Low"
        color = "#00C853"
    elif congestion_percent < 70:
        level = "Medium"
        color = "#FF9800"
    else:
        level = "High"
        color = "#D50000"

    return level, round(congestion_percent, 2), color


