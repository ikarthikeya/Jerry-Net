import socket
import json
import time
from math import radians, sin, cos, sqrt, atan2
import heapq
import threading
import random  # For packet loss simulation
import sys
from time import perf_counter
sys.stdout.reconfigure(encoding='utf-8')


# Satellite configuration
satellite_id = "sat1"
satellite_positions = {
    "sat1": (34.05, -118.25),  # Los Angeles
    "sat2": (36.16, -115.15),  # Las Vegas
    "sat3": (40.71, -74.00),   # New York
    "sat4": (37.77, -122.42),  # San Francisco
    "sat5": (34.68, -117.83),  # Example Satellite
    "earth2": (32.77, -96.79)  # Stationary Earth object
}

# Ports configuration
receiver_ports = {
    "sat1": 5005,
    "sat2": 5006,
    "sat3": 5007,
    "sat4": 5008,
    "sat5": 5009,
    "earth2": 5010
}

communication_range = 5000
# PACKET_LOSS_PROBABILITY = 0.1
def reconstruct_path(previous_nodes, start_node, end_node):
    path = []
    current_node = end_node
    while current_node is not None:
        path.insert(0, current_node)
        current_node = previous_nodes[current_node]
    if path[0] == start_node:  # Ensure path is valid
        return path
    return []  # Return empty path if no connection

# Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Build the graph dynamically based on communication range
def build_graph(satellite_positions, communication_range):
    graph = {}
    for sat_id, (lat1, lon1, *_rest) in satellite_positions.items():
        neighbors = {}
        for neighbor_id, (lat2, lon2, *_rest) in satellite_positions.items():
            if sat_id != neighbor_id:
                distance = calculate_distance(lat1, lon1, lat2, lon2)
                if distance <= communication_range:
                    neighbors[neighbor_id] = distance
        graph[sat_id] = neighbors
    print(f"Graph: {graph}")
    return graph

# Dijkstra's algorithm
def dijkstra(graph, start_node):
    distances = {node: float('inf') for node in graph}
    distances[start_node] = 0
    previous_nodes = {node: None for node in graph}
    priority_queue = [(0, start_node)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances[current_node]:
            continue

        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))

    return distances, previous_nodes

# A* algorithm
def a_star(graph, start_node, goal_node, satellite_positions):
    def heuristic(node, goal):
        lat1, lon1 = satellite_positions[node]
        lat2, lon2 = satellite_positions[goal]
        return calculate_distance(lat1, lon1, lat2, lon2)

    distances = {node: float('inf') for node in graph}
    distances[start_node] = 0
    previous_nodes = {node: None for node in graph}
    priority_queue = [(0, start_node)]

    while priority_queue:
        current_priority, current_node = heapq.heappop(priority_queue)

        if current_node == goal_node:
            break

        for neighbor, weight in graph[current_node].items():
            distance = distances[current_node] + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                priority = distance + heuristic(neighbor, goal_node)
                heapq.heappush(priority_queue, (priority, neighbor))

    return distances, previous_nodes

# Simulate satellite movement
def simulate_satellite_movement(satellite_positions):
    for sat_id in satellite_positions:
        lat, lon, *_rest = satellite_positions[sat_id]
        satellite_positions[sat_id] = (lat + 0.01, lon + 0.01)  # Example movement
    return satellite_positions

# Send a packet with optional loss simulation
def send_packet(sender_id, receiver_id, receiver_port, packet):
    # if random.random() < PACKET_LOSS_PROBABILITY:
    #     print(f"Packet {packet['packet_num']} from {sender_id} to {receiver_id} lost in transmission.")
    #     return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.sendto(json.dumps(packet).encode(), ("localhost", receiver_port))
            print(f"Packet {packet['packet_num']} is sent from {sender_id} to {receiver_id} at {receiver_port}")
    except Exception as e:
        print(f"Error sending packet {packet['packet_num']} to {receiver_id}: {e}")

# Server to listen for packets
def start_server(host, port, satellite_id):
    """Start the server to listen for incoming packets."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"{satellite_id} server listening on {host}:{port}...")

    while True:
        data, addr = server_socket.recvfrom(1024)
        packet = json.loads(data.decode())
        print(f"{satellite_id} received packet {packet['packet_num']} from {packet['sender']} with message: {packet['data']}")

        # Check if there are more hops in the path
        if packet.get("path") and len(packet["path"]) > 0:
            next_hop = packet["path"].pop(0)  # Get the next hop from the path
            if next_hop in receiver_ports:
                send_packet(
                    satellite_id,  # Current satellite
                    next_hop,  # Next satellite in the path
                    receiver_ports[next_hop],  # Next satellite's receiving port
                    packet  # Packet to be sent
                )
        else:
            print(f"{satellite_id} has no more hops for packet {packet['packet_num']}. Packet delivered.")


if __name__ == "__main__":
    packet_count = 10
    destination = "earth2"

    for sat_id, port in receiver_ports.items():
        threading.Thread(target=start_server, args=("localhost", port, sat_id), daemon=True).start()

    for packet_num in range(packet_count):
        # Simulate satellite movement
        satellite_positions = simulate_satellite_movement(satellite_positions)

        # Build the graph dynamically
        graph = build_graph(satellite_positions, communication_range)

        # Ensure graph is valid
        if satellite_id not in graph or destination not in graph:
            print(f"Graph is invalid or missing required nodes ({satellite_id}, {destination}). Skipping...")
            continue

        # Measure Dijkstra execution time
        dijkstra_start = perf_counter()
        distances_dijkstra, previous_nodes_dijkstra = dijkstra(graph, satellite_id)
        dijkstra_end = perf_counter()

        # Measure A* execution time
        a_star_start = perf_counter()
        distances_a_star, previous_nodes_a_star = a_star(graph, satellite_id, destination, satellite_positions)
        a_star_end = perf_counter()

        # Reconstruct paths
        dijkstra_path = reconstruct_path(previous_nodes_dijkstra, satellite_id, destination)
        a_star_path = reconstruct_path(previous_nodes_a_star, satellite_id, destination)

        # Output the execution times in microseconds
        print(f"Dijkstra Time: {(dijkstra_end - dijkstra_start) * 1e6:.2f} µs")
        print(f"A* Time: {(a_star_end - a_star_start) * 1e6:.2f} µs")

        # Print paths
        if dijkstra_path:
            print(f"Dijkstra Path: {' -> '.join(dijkstra_path)}")
        else:
            print("No path found using Dijkstra's algorithm.")

        if a_star_path:
            print(f"A* Path: {' -> '.join(a_star_path)}")
        else:
            print("No path found using A* algorithm.")

        # Handle sending packets for A* (or use Dijkstra if desired)
        if a_star_path and len(a_star_path) > 1:
            next_hop = a_star_path[1]
            packet = {
                "sender": satellite_id,
                "packet_num": packet_num,
                "data": f"Hello from {satellite_id}! Packet {packet_num}",
                "path": a_star_path[1:]
            }
            print(f"Sending Packet via A*: {packet}")
            send_packet(satellite_id, next_hop, receiver_ports[next_hop], packet)
        else:
            print(f"No valid A* path to {destination} from {satellite_id}")

        # Pause before sending the next packet
        time.sleep(1)
