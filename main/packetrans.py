import json
import random
import time
from datetime import datetime
import uuid

def generate_sensor_data(sensor, timestamp):
    # Define realistic value ranges for each sensor type
    value_ranges = {
        "moisture": (10, 80, "%"),
        "temperature": (10, 35, "°C"),
        "soil_ph": (5.5, 7.5, "pH"),
        "humidity": (20, 90, "%"),
        "light_intensity": (200, 800, "lx")
    }
    # Get range and unit based on sensor type
    value_range = value_ranges.get(sensor["sensor_type"], (0, 100, "units"))
    
    # Generate a single data packet for the sensor
    return {
        "packet_id": str(uuid.uuid4()),
        "sensor_id": sensor["sensor_id"],
        "sensor_type": sensor["sensor_type"],
        "location": {
            "lat": round(sensor["location_lat"], 4),
            "lon": round(sensor["location_lon"], 4)
        },
        "timestamp": timestamp,
        "value": round(random.uniform(value_range[0], value_range[1]), 2),
        "unit": value_range[2],
        "status": "active" if random.random() > 0.05 else "faulty"  # 5% chance of being faulty
    }

def generate_batch_data(sensors, timestamp):
    # Generate data for each sensor in a batch
    batch = [generate_sensor_data(sensor, timestamp) for sensor in sensors]
    return json.dumps(batch)

def continuous_data_stream(sensor_count=5, transmission_interval=5):
    # Initialize sensors with specific details
    sensors = [
        {
            "sensor_id": i + 1,
            "sensor_type": random.choice(["moisture", "temperature", "soil_ph", "humidity", "light_intensity"]),
            "location_lat": random.uniform(-90, 90),
            "location_lon": random.uniform(-180, 180)
        }
        for i in range(sensor_count)
    ]
    
    print("Starting optimized data transmission...\n")
    
    try:
        # Loop for continuous data generation and transmission
        while True:
            timestamp = datetime.now().isoformat()  # Generate a single timestamp for the batch
            json_batch = generate_batch_data(sensors, timestamp)
            print("Transmitting batch:", json_batch)
            # Add network transmission logic here (e.g., HTTP POST, MQTT publish)
            time.sleep(transmission_interval)
    
    except KeyboardInterrupt:
        print("\nData transmission stopped.")

# Example usage
continuous_data_stream(sensor_count=10, transmission_interval=10)
