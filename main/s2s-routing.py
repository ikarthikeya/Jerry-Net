import threading
import time
import heapq
from math import radians, sin, cos, sqrt, atan2

# Initialize four dummy satellites with example latitude and longitude coordinates
satellite_positions = {
    "sat1": [34.05, -118.25],  # Example position for Satellite 1 (Los Angeles)
    "sat2": [36.16, -115.15],  # Example position for Satellite 2 (Las Vegas)
    "sat3": [40.71, -74.00],   # Example position for Satellite 3 (New York)
    "sat4": [37.77, -122.42]   # Example position for Satellite 4 (San Francisco)
}
communication_range = 500  # in kilometers

# Define the routing table for each satellite
routing_table = {}

# Haversine formula to calculate distance between two lat/lon points
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Update routing table with nearby satellites within range
def update_routing_table(routing_table, satellite_positions, current_position, communication_range):
    while True:
        for sat_id, position in satellite_positions.items():
            distance = calculate_distance(current_position[0], current_position[1], position[0], position[1])
            if distance <= communication_range:
                routing_table[sat_id] = {"position": position, "distance": distance, "status": "active"}
            else:
                if sat_id in routing_table:
                    routing_table[sat_id]["status"] = "inactive"
        time.sleep(10)  # Update every 10 seconds

# Dijkstra's algorithm for finding the shortest path
def dijkstra_routing(routing_table, destination_id):
    distances = {sat_id: float('inf') for sat_id in routing_table}
    previous_nodes = {sat_id: None for sat_id in routing_table}
    distances[destination_id] = 0
    priority_queue = [(0, destination_id)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances[current_node]:
            continue

        for neighbor, info in routing_table.items():
            if info["status"] == "active":
                distance = info["distance"]
                new_distance = current_distance + distance

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_distance, neighbor))

    return distances, previous_nodes

# Function to simulate satellite broadcasting its position to neighbors
def broadcast_position(satellite_id, position, satellites_in_range):
    while True:
        for neighbor_id in satellites_in_range:
            send_position_update(satellite_id, position, neighbor_id)
        time.sleep(15)  # Update every 15 seconds

# Simulated function to send position updates
def send_position_update(satellite_id, position, neighbor_id):
    print(f"Sending position update from {satellite_id} to {neighbor_id}")

# Function to simulate satellite movement by changing positions every second
def update_positions(satellite_positions):
    while True:
        for sat_id in satellite_positions:
            # Simulate slight movement by adjusting latitude and longitude
            satellite_positions[sat_id][0] += 0.0001 * (-1 if sat_id.endswith('1') else 1)
            satellite_positions[sat_id][1] += 0.0001 * (-1 if sat_id.endswith('2') else 1)
        time.sleep(1)  # Update positions every second

# Function to continuously display updated satellite positions and optimal distance
def continuous_display(satellite_positions, routing_table, destination_id="sat3"):
    while True:
        print("\nUpdated Satellite Positions:")
        for sat_id, pos in satellite_positions.items():
            print(f"{sat_id}: Latitude {pos[0]:.4f}, Longitude {pos[1]:.4f}")

        # Update the routing table based on the new positions
        for sat_id, position in satellite_positions.items():
            update_routing_table(routing_table, satellite_positions, position, communication_range)

        # Calculate shortest path to destination satellite
        distances, paths = dijkstra_routing(routing_table, destination_id)
        print(f"Optimal distances to {destination_id}: {distances}")

        time.sleep(1)  # Update every second

# Main execution for satellite router table maintenance
if __name__ == "__main__":
    # Start a thread to dynamically update satellite positions
    threading.Thread(target=update_positions, args=(satellite_positions,), daemon=True).start()

    # Start a routing table update thread for each satellite
    for sat_id, position in satellite_positions.items():
        threading.Thread(target=update_routing_table,
                         args=(routing_table, satellite_positions, position, communication_range),
                         daemon=True).start()

    # Example of starting broadcast for one satellite
    threading.Thread(target=broadcast_position, args=("sat1", satellite_positions["sat1"], satellite_positions.keys()), daemon=True).start()

    # Start continuous display of positions and optimal distances
    continuous_display_thread = threading.Thread(target=continuous_display, args=(satellite_positions, routing_table), daemon=True)
    continuous_display_thread.start()

    # Keep the main program alive
    continuous_display_thread.join()
