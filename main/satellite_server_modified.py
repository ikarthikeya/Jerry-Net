from collections import deque
import socket
import threading
import time
from movement_simulation import init_satellites, satellites_move
import zlib
from protocol import decode_packet,send_ack,answer_inquiry, CONTROL_FLAGS


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


def keep_moving(global_dequeue, orbit_z_axis, num_sats, velocity, sat_index):
    sat_ll_list = init_satellites(orbit_z_axis, num_sats)
    # initial lat, lon of the satellite
    (lat, lon) = sat_ll_list[sat_index]
    start_time = time.time()
    while True:
        time.sleep(1)
        end_time = time.time()
        t = end_time - start_time
        start_time = end_time
        lat, lon = satellites_move((lat, lon), orbit_z_axis, velocity, t)
        print(f"Satellites keeps moving: time slaps {t}, latitude {lat}, longitude {lon}")
        # update data in global queue for multi-threading data share
        global_dequeue.append((lat, lon))


def server(global_dequeue, server_addr, buffer_size, sat_node_number):
    # create udp satellite server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', server_addr))

    print(f"Satellite with node number {sat_node_number} is listening on {server_addr} for recieving...")
    received_packets = {}

    while True:
        # Receive a packet
        data, client_address = server_socket.recvfrom(buffer_size)
        print(f"Packet received on satellite {sat_node_number}")
        # Decode the packet
        decode_res = decode_packet(data)
        if (decode_res['control_flag'] == CONTROL_FLAGS['data']) and verify_checksum(decode_res['payload'], decode_res['checksum']):
            send_ack(server_addr,client_address,server_socket,decode_res,received_packets)
        elif (decode_res['control_flag'] == CONTROL_FLAGS['inquiry']) and verify_checksum(decode_res['payload'],decode_res['checksum']):
            try:
                lat, lon = global_dequeue.pop()
            except IndexError:
                # give a out of range latitude(it should be from -90 to 90) to imply error
                lat, lon = -800, -800

            answer_inquiry(server_addr,client_address,server_socket,lat,lon)
        else:
            print(f"Checksum mismatch for packet {decode_res['packet_num']}. Packet discarded.")


if __name__ == "__main__":
    global_dequeue = deque(maxlen=10)
    # SERVER_ADDR = ('localhost', 8080)
    SAT_ADDR = {
        1: { 'send': 50010, 'receive': 50011 },
        2: { 'send': 50012, 'receive': 50013 },
        3: { 'send': 50014, 'receive': 50015 },
        4: { 'send': 50016, 'receive': 50017 },
        5: { 'send': 50018, 'receive': 50019 }
    }
    BUFFER_SIZE = 1024
    NUM_SATS = 5
    SAT_INDEX = 0
    # SAT_NODE_NUM=0
    ORBIT_Z_AXIS = (0, 0)
    server_threads = []
    # from the starlink article, https://blog.apnic.net/2024/05/17/a-transport-protocols-view-of-starlink/
    # the satellite's speed is about 27000km/hour on with the height of 550km
    # on the equator of earth surface, 1 degree of longitude is about 111.3km
    VELOCITY = 27000 / 111.3 / (60 * 60)
    print(f"velocity:{VELOCITY}")

    simulation_thread = threading.Thread(target=keep_moving,
                                         args=(global_dequeue, ORBIT_Z_AXIS, NUM_SATS, VELOCITY, SAT_INDEX),
                                         daemon=True)
    for id, ports in SAT_ADDR.items():
        server_threads.append(threading.Thread(target=server, args=(global_dequeue, ports['receive'], BUFFER_SIZE, id),
                                               daemon=True))
        # server_threads[-1].start()

    # start the threads
    simulation_thread.start()
    for i in range(0, len(SAT_ADDR)):
        server_threads[i].start()

    # keep the main program alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")
