"""
latency machine learning prediction: Daim
"""
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.preprocessing import OneHotEncoder
import pandas as pd

# # Generate synthetic data
# def generate_synthetic_data(n_samples=1000):
#     earth_lats = np.random.uniform(-90, 90, n_samples)
#     earth_lons = np.random.uniform(-180, 180, n_samples)
#     sat_lats = np.random.uniform(-90, 90, n_samples)
#     sat_lons = np.random.uniform(-180, 180, n_samples)

#     latencies = []
#     for earth_lat, earth_lon, sat_lat, sat_lon in zip(earth_lats, earth_lons, sat_lats, sat_lons):
#         distance = earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon)
#         latency = e2s_lantency(earth_lat, earth_lon, sat_lat, sat_lon)
#         latencies.append(latency)

#     X = np.column_stack([earth_lats, earth_lons, sat_lats, sat_lons])
#     y = np.array(latencies)
#     return X, y
import numpy as np
import pandas as pd

def generate_synthetic_data(num_samples=1000, seed=42):
    np.random.seed(seed)
    
    # Generate random Earth and Satellite coordinates
    earth_lats = np.random.uniform(-90, 90, num_samples)
    earth_lons = np.random.uniform(-180, 180, num_samples)
    sat_lats = np.random.uniform(-90, 90, num_samples)
    sat_lons = np.random.uniform(-180, 180, num_samples)

    # Calculate Distance (km)
    EARTH_RADIUS = 6378.0
    SAT_ALTITUDE = 550.0
    distances = []
    for elat, elon, slat, slon in zip(earth_lats, earth_lons, sat_lats, sat_lons):
        x_earth = EARTH_RADIUS * np.cos(np.radians(elat)) * np.cos(np.radians(elon))
        y_earth = EARTH_RADIUS * np.cos(np.radians(elat)) * np.sin(np.radians(elon))
        z_earth = EARTH_RADIUS * np.sin(np.radians(elat))
        sat_r = EARTH_RADIUS + SAT_ALTITUDE
        x_sat = sat_r * np.cos(np.radians(slat)) * np.cos(np.radians(slon))
        y_sat = sat_r * np.cos(np.radians(slat)) * np.sin(np.radians(slon))
        z_sat = sat_r * np.sin(np.radians(slat))
        distance = np.sqrt((x_sat - x_earth)**2 + (y_sat - y_earth)**2 + (z_sat - z_earth)**2)
        distances.append(distance)

    # Satellite Traffic Load (%)
    traffic_load = np.random.uniform(0, 100, num_samples)

    # Weather Conditions (0 = Clear, 1 = Cloudy, 2 = Rain, 3 = Storm)
    weather_conditions = np.random.choice([0, 1, 2, 3], num_samples, p=[0.55, 0.2, 0.17, 0.08])

    # Signal Strength (0 to 1, inversely proportional to distance and weather severity)
    signal_strength = np.clip(1 / (np.array(distances) / 1000 + weather_conditions + 1), 0, 1)

    # Calculate Latency (ms) using a sensible trend:
    # Latency increases with distance and traffic load, and decreases with signal strength.
    base_latency = np.array(distances) / 300000 * 1000  # Speed of light in km/ms
    traffic_penalty = traffic_load * 0.05  # Traffic load contributes up to 5 ms
    weather_penalty = weather_conditions * 2  # Weather adds penalty (max 6 ms for storms)
    latency = base_latency + traffic_penalty + weather_penalty
    latency = np.clip(latency, 0, None)  # Ensure latency is non-negative

    # Compile features into a DataFrame
    data = pd.DataFrame({
        "Earth_Lat": earth_lats,
        "Earth_Lon": earth_lons,
        "Sat_Lat": sat_lats,
        "Sat_Lon": sat_lons,
        "Distance_km": distances,
        "Traffic_Load_%": traffic_load,
        "Weather_Condition": weather_conditions,
        "Signal_Strength": signal_strength,
        "Latency_ms": latency
    })
    
    # Save to a CSV for later use
    data.to_csv("synthetic_satellite_latency_data.csv", index=False)
    print("Synthetic data saved as 'synthetic_satellite_latency_data.csv'.")

    return data.loc[:, data.columns != 'Latency_ms'],data.Latency_ms

# # Generate data
# synthetic_data = generate_synthetic_data(num_samples=1000)
# print(synthetic_data.head())

# Generate data
X, y = generate_synthetic_data(num_samples=1000)
# One-hot encode the categorical feature
encoder = OneHotEncoder(sparse_output=False)
encoded_weather = encoder.fit_transform(X[['Weather_Condition']])
encoded_weather_df = pd.DataFrame(encoded_weather, columns=encoder.get_feature_names_out(['Weather_Condition']))

# Replace the original Weather_Condition with encoded columns
X = pd.concat([X.drop(columns=['Weather_Condition']), encoded_weather_df], axis=1)

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# print(X_train.head())
# print(X_train.describe())


# Train a model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
score = model.score(X_test, y_test)
print(f"R^2 score on test data: {score:.3f}")

# Save the model to disk
joblib.dump(model, 'latency_predictor.pkl')

print("Model trained and saved as 'latency_predictor.pkl'.")

