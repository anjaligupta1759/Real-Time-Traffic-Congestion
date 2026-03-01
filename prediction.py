import joblib
import pandas as pd
from datetime import datetime

model = joblib.load("traffic_model.pkl")

def predict_congestion(current_speed, free_speed):

    hour = datetime.now().hour

    data = pd.DataFrame([{
        "hour": hour,
        "current_speed": current_speed,
        "free_flow_speed": free_speed
    }])

    prediction = model.predict(data)[0]

    if prediction == "Low":
        percent = 25
        color = "#00C853"
    elif prediction == "Medium":
        percent = 60
        color = "#FF9800"
    else:
        percent = 90
        color = "#D50000"

    return prediction, percent, color
