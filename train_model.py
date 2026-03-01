import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib


# Load Dataset..!!
data = pd.read_csv("traffic_data.csv")


# Clean column names (extra spaces safety)
data.columns = data.columns.str.strip()

print(" Dataset loaded successfully")
print(data.head())
print("\nColumns:", data.columns)


# Data Preprocessing..!!
# Convert date_time to datetime..!!
data['date_time'] = pd.to_datetime(data['date_time'], errors='coerce')


# Drop rows with invalid datetime (if any)..!!
data = data.dropna(subset=['date_time'])


# Extract hour feature..!!
data['hour'] = data['date_time'].dt.hour
print("Hour feature extracted")


# Features & Target..!!
X = data[['hour', 'current_speed', 'free_flow_speed']]
y = data['congestion_level']
print(" Features & Target created")


# Train-Test Split..!!
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(" Data split completed")


# Model Training..!!
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)
model.fit(X_train, y_train)
print(" Model trained successfully")


# Model Evaluation..!!
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n Model Accuracy: {accuracy * 100:.2f}%")

print("\n Classification Report:")
print(classification_report(y_test, y_pred))


# Save Model..!!
joblib.dump(model, "traffic_model.pkl")
print("\n Model saved as traffic_model.pkl")
