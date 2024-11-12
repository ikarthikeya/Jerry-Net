# created by Ting
# Sample Socket initialization with TCP protocol
# no dependency needed other than higher version of python
# Every satellite and earth-base opens a socket on a local port
# in this piece of code they are run in one main program with multiple thread,
# however, if you run each server's code in a seperate terminal window and open serveral terminals at once, I think it should also work

import json
import time
import socket
import logging
import os
import threading

# Create 'logs' directory if it doesn't exist
logs_dir = 'logs'
os.makedirs(logs_dir, exist_ok=True)

# Set up logging
log_file_path = os.path.join(logs_dir, 'satellite_communication.log')
logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)


# Define the types of connections
class ConnectionType:
    S2S = "Satellite-to-Satellite"
    S2E = "Satellite-to-Earth"
    E2S = "Earth-to-Satellite"
    BROADCAST = "Broadcast from Earth to Satellites"


def send_message(packet_type, des_host, des_port, des_id,
                 message, data_flag, src_id):
    #Handles sending messages over TCP.
    socket_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    try:
        port = int(des_port)
        socket_temp.connect((des_host, port))
        message = message.encode('utf-8')
        socket_temp.send(message)
        logger.info(f"{packet_type} message sent successfully from {src_id} to {des_id} with data_flag: {data_flag}.")
    except Exception as e:
        logger.error(f"{timestamp} - Error in {packet_type} from {src_id} to {des_id} with data_flag {data_flag}: {e}")
    finally:
        socket_temp.close()


def make_packet(data_flag, data, packet_type):
    #Creates a packet for communication.
    try:
        if not isinstance(data_flag, str) or not data_flag:
            raise ValueError("Invalid data_flag format.")

        packet = {
            "data_flag": f'{data_flag}/{time.time()}',
            "type": packet_type,
            "data": data
        }
        return json.dumps(packet)
    except Exception as e:
        logger.error(f"Error creating {packet_type} packet with data_flag {data_flag}: {e}")
        return None


def send_s2s_message(data_flag, data, des_host, des_port, des_id,src_id):
    """Sends Satellite-to-Satellite message."""
    message = make_packet(data_flag, data, ConnectionType.S2S)
    if message:
        send_message(ConnectionType.S2S, des_host, des_port, des_id,
                     message, data_flag, src_id)


def send_s2e_message(data_flag, data, des_host, des_port, des_id,src_id):
    """Sends Satellite-to-Earth message."""
    message = make_packet(data_flag, data, ConnectionType.S2E)
    if message:
        send_message(ConnectionType.S2E, des_host, des_port, des_id,
                     message, data_flag, src_id)


def send_e2s_message(data_flag, data, des_host, des_port, des_id,src_id):
    """Sends Earth-to-Satellite message."""
    message = make_packet(data_flag, data, ConnectionType.E2S)
    if message:
        send_message(ConnectionType.S2E, des_host, des_port, des_id,
                     message, data_flag, src_id)


def broadcast_from_earth(data_flag, data, satellite_list, src_id):
    """Broadcasts a message from Earth to multiple satellites."""
    message = make_packet(data_flag, data, "Broadcast")
    if message:
        for satellite in satellite_list:
            try:
                satellite_host, satellite_port, satellite_id = satellite
                send_message(ConnectionType.BROADCAST, satellite_host, satellite_port, satellite_id,
                             message, data_flag, src_id)
            except Exception as e:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                logger.error(
                    f"{timestamp} - Broadcast Error to Satellite with data_flag {data_flag}: {e}")


def server(host, port, node_id):
    #create local server to listen for incoming messages.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"{node_id} is listening on {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        with conn:
            print(f"{node_id} connected by {addr}")
            data = conn.recv(1024)
            if data:
                print(f"{node_id} received: {data.decode('utf-8')}")


# Example usage of the protocol functions
if __name__ == "__main__":
    # Define local server parameters
    satellite1_host, satellite1_port, satellite1_id = 'localhost', 8081, 'Satellite-1'
    satellite2_host, satellite2_port, satellite2_id = 'localhost', 8082, 'Satellite-2'
    earth_host, earth_port, earth_id = 'localhost', 8080, 'Earth-001'

    # Start satellite and Earth server threads
    threading.Thread(target=server, args=(satellite1_host, satellite1_port, satellite1_id),
                     daemon=True).start()
    threading.Thread(target=server, args=(satellite2_host, satellite2_port, satellite2_id),
                     daemon=True).start()
    threading.Thread(target=server, args=(earth_host, earth_port, earth_id), daemon=True).start()

    # Example calls
    print("\n--- Sending S2S message ---")
    send_s2s_message("s2s_data_flag", "Test S2S data", satellite2_host, satellite2_port, satellite2_id, satellite1_id)
    print("\n--- Sending S2E message ---")
    send_s2e_message("s2e_data_flag", "Test S2E data", earth_host, earth_port, earth_id, satellite1_id)
    print("\n--- Sending E2S message ---")
    send_e2s_message("e2s_data_flag", "Test E2S data", satellite1_host, satellite1_port, satellite1_id, earth_id)
    print("\n--- Broadcasting from Earth to all satellites ---")
    # Broadcasting from Earth to all satellites
    broadcast_from_earth("broadcast_data_flag", "Test broadcast data",
                         [(satellite1_host, satellite1_port, satellite1_id),
                         (satellite2_host, satellite2_port, satellite2_id)],
                         earth_id)

    # Keep the main thread running to let server threads handle connections
    while True:
        time.sleep(1)
