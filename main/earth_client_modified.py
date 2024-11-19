import subprocess
import socket
import time
import numpy as np
import threading
import psutil
import joblib
from routing_table_manager_modified import RoutingTableManager
import zlib
from movement_simulation import earth_sat_distance
from protocol import send_packets


# Load the trained model
latency_model = joblib.load('latency_predictor.pkl')

def predict_latency(routing_table):
    """
    Predict latency for each satellite and select the one with the lowest latency.

    :param earth_lat: Latitude of Earth station
    :param earth_lon: Longitude of Earth station
    :param satellites: List of tuples [(sat_lat, sat_lon, node_id), ...]
    :return: Best satellite (node_id, predicted_latency)
    """
        # Create an array of 4 zeros
    weather = np.zeros(4)
    traffic_load = np.random.uniform(0, 100)

    # Randomly choose one index to set to 1
    weather[np.random.randint(4)] = 1
    features = []
    for _,sat_info in routing_table.items():
        distance=earth_sat_distance(EARTH_LL[0], EARTH_LL[1], sat_info['latitude'], sat_info['longitude'])
        signal_strength = np.clip(1 / (np.array(distance) / 1000 + np.argmax(weather) + 1), 0, 1)
        features.append([EARTH_LL[0], EARTH_LL[1], sat_info['latitude'], sat_info['longitude'],distance,traffic_load,signal_strength\
            ,weather[0],weather[1],weather[2],weather[3]])

    # Predict latencies
    predictions = latency_model.predict(np.array(features))
    best_idx = np.argmin(predictions)
    return weather,list(routing_table.keys())[best_idx], predictions[best_idx]

# Example usage in clumsy_simulate or client function
# satellites = [(15, 45, 'Satellite-1'), (30, 60, 'Satellite-2')]  # Satellite lat/lon with IDs
# earth_lat, earth_lon = 10, 20  # Example Earth location


# best_satellite, best_latency = predict_latency(earth_lat, earth_lon, satellites)

# print(f"Best satellite to use: {best_satellite}, Predicted latency: {best_latency:.2f} ms")

def calculate_checksum(data):
    """
    Calculate a checksum for the given data using MD5.
    :param data: Data to calculate the checksum for (in bytes).
    :return: Hexadecimal checksum string.
    """
    return zlib.crc32(data)


def verify_checksum(data, checksum):
    """
    Verify if the checksum of the data matches the provided checksum.
    :param data: The original data (in bytes).
    :param checksum: The checksum to verify against.
    :return: True if valid, False otherwise.
    """
    return calculate_checksum(data) == checksum


def start_clumsy(single_latency, single_drop_rate):
    # clumsy working directory
    CLUM_DIR = "clumsy"
    # Start Clumsy with 10% packet loss
    cmd = f"clumsy.exe --drop on --drop-inbound on --drop-outbound on --drop-chance {single_drop_rate} " \
          f"--lag on --lag-inbound on --lag-outbound on --lag-time {single_latency}"
    process = subprocess.Popen(cmd, cwd=CLUM_DIR, shell=True)
    print("clumsy started.")
    return process.pid


def kill_clumsy(pid):
    # Terminate the Clumsy process
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()
    print("clumsy stopped.")


def e2s_lantency(earth_lat, earth_lon, sat_lat, sat_lon):
    # light speed constant
    LIGHT_V = 300000.  # km/s
    # calculate distance between earth and satellite
    distance = earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon)
    # suppose radio wave is transmitted with light speed
    single_bound_lantency = distance / LIGHT_V
    return single_bound_lantency * 1000  # return in miniseconds


def e2s_packet_loss(earth_lat, earth_lon, sat_lat, sat_lon):
    SAT_H = 550.
    # calculate distance between earth and satellite
    distance = earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon)
    # man-made function, this function is chosen as packet loss accelerates to increase when the distance increases
    single_bound_loss_rate = min(0.02 * np.exp((distance - SAT_H) / 1000.), 1.0)
    return single_bound_loss_rate * 100


def clumsy_simulate(server_addr, buffer_size, timeout, self_ll, self_node_num):
    inquire_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inquire_socket.settimeout(timeout)
    self_lat, self_lon = self_ll
    clumsy_pid = None
    # simulate different latency and drag for every three seconds
    while True:
        # inquire server about satellites index and latitude,longitude information
        flag = 0
        pn, tp, cu = 0, 0, 0  # dummy parameters here, they are neglected in flag=0 case
        header = flag.to_bytes(4, 'big') + self_node_num.to_bytes(4, 'big') \
                 + pn.to_bytes(4, 'big') + tp.to_bytes(4, 'big')
        inquiry = header + cu.to_bytes(4, 'big')
        # print("start inquiry...")
        try:
            # send the inquiry
            inquire_socket.sendto(inquiry, server_addr)
            # print("inquiry sent...")
            # Wait for acknowledgement
            ack, _ = inquire_socket.recvfrom(buffer_size)
            # print("ack received..")
            # Decode the packet
            flag, node_number, lat_info, lon_info = ack[:4], ack[4:8], ack[8:12], ack[12:16]
            flag = int.from_bytes(flag, 'big')
            assert flag == 0, "Received wrong acknowledgement for latitude/longitude inquiry"
            node_number = int.from_bytes(node_number, 'big')
            sat_lat = int.from_bytes(lat_info, 'big', signed=True)
            sat_lon = int.from_bytes(lon_info, 'big', signed=True)
            # calculate latency and packet loss rate
            distance = earth_sat_distance(self_lat, self_lon, sat_lat, sat_lon)
            single_latency = e2s_lantency(self_lat, self_lon, sat_lat, sat_lon)
            single_drop_rate = e2s_packet_loss(self_lat, self_lon, sat_lat, sat_lon)
            print(f"earth lat {self_lat},earth lon {self_lon},sat lat {sat_lat}, sat lon {sat_lon}")
            print(
                f"E2S distance: {distance} km, single bound latency {single_latency} ms, single bound drop rate {single_drop_rate}")
            if clumsy_pid is not None:
                kill_clumsy(clumsy_pid)
            clumsy_pid = start_clumsy(single_latency, single_drop_rate)
        except socket.timeout:
            pass
        time.sleep(3)


def client(routing_manager, sat_addresses, buffer_size, timeout, debug_inter, chunk_size, message):
    # clean router table
    routing_manager.cleanup_routing_table()
    # get active sats
    active_satellites = routing_manager.get_active_satellites()
    # print(active_satellites)
    weather,best_satellite, best_latency = predict_latency(active_satellites)
    print(f"Best satellite to use: {best_satellite}, Predicted latency: {best_latency:.2f} ms, Current weather: {WEATHER_CONDITIONS[np.argmax(weather)]}")
    # predeict best

    # Data to be sent
    earth1_addr = ['127.0.0.1', 8080]  # the ultimate src address
    earth2_addr = ['127.0.0.1', 8081]  # the ultimate destination address
    # this server address should be decided by the rounting manager
    server_addr = ['127.0.0.1', active_satellites[best_satellite]['address']]  # current receiver satellite(router) address

    send_packets(earth1_addr, earth2_addr, server_addr, message,
                 timeout=timeout,chunk_size=chunk_size,buffer_size=buffer_size,
                 debug_interval=debug_inter)


if __name__ == "__main__":
    SAT_ADDR = {
        1: { 'send': 50010, 'receive': 50011 },
        2: { 'send': 50012, 'receive': 50013 },
        3: { 'send': 50014, 'receive': 50015 },
        4: { 'send': 50016, 'receive': 50017 },
        5: { 'send': 50018, 'receive': 50019 }
    }
    # SERVER_ADDR = ('localhost', 8080),('localhost', 8081),
    BUFFER_SIZE = 1024
    EARTH_LL = (20, 70)  # latitude, longitude
    TIMEOUT = 2  # 2s timeout for inquiry satellites latitude and longitude information
    DEBUG_INTER = 1  # 1s
    CHUNK_SIZE = 10  # bit
    EARTH_NODE_NUM=7
    WEATHER_CONDITIONS= {0 : 'Clear', 1 : 'Cloudy', 2 : 'Rain', 3 : 'Storm'}
    # clumsy_thread = threading.Thread(target=clumsy_simulate,
    #                                  args=(SERVER_ADDR,BUFFER_SIZE,TIMEOUT,EARTH_LL,EARTH_NODE_NUM),
    #                                  daemon=True)

    routing_manager = RoutingTableManager(SAT_ADDR, BUFFER_SIZE, TIMEOUT)
    # Start the routing table update thread
    update_thread = threading.Thread(
        target=routing_manager.update_routing_table, args=(EARTH_NODE_NUM,), daemon=True
    )
    update_thread.start()

    # client_thread = threading.Thread(target=client,
    #                                  args=(routing_manager,SAT_ADDR, BUFFER_SIZE, TIMEOUT,DEBUG_INTER, CHUNK_SIZE, EARTH_NODE_NUM,message),
    #                                  daemon=True)
    # # start the threads
    # # clumsy_thread.start()
    # client_thread.start()

    # keep the main program alive
    try:

        message = "This is a test string that will be sent as binary data over UDP in smaller packets."
        time.sleep(5)
        client(routing_manager, SAT_ADDR, BUFFER_SIZE, TIMEOUT, DEBUG_INTER, CHUNK_SIZE, message)
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        print("Exiting...")