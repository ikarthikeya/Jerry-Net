from collections import deque
import json
import socket
import threading
import time
from movement_simulation import init_satellites, satellites_move
import zlib
from protocol import decode_packet,send_packets,send_ack,send_path,answer_inquiry, CONTROL_FLAGS, create_udp_packet
from queue import Queue


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
    lat_lon = sat_ll_list
    start_time = time.time()
    while True:
        for i in range(num_sats):
            time.sleep(1)
            end_time = time.time()
            t = end_time - start_time
            start_time = end_time
            lat_lon[i][0], lat_lon[i][1] = satellites_move((lat_lon[i][0], lat_lon[i][1]), orbit_z_axis, velocity, t)
            print(f"Satellite {i+1} keeps moving: time slaps {t}, latitude {lat_lon[i][0]}, longitude {lat_lon[i][1]}")
            # update data in global queue for multi-threading data share
            global_dequeue[i].append((lat_lon[i][0], lat_lon[i][1]))


def server(global_dequeue, server_addr, receiver_ports, buffer_size, satellite_id,sat_node_number):
    # create udp satellite server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', server_addr))

    print(f"{satellite_id} is listening on {server_addr} for recieving...")
    received_packets = {}
    message_queue = Queue()
    while True:
        # Receive a packet
        data, client_address = server_socket.recvfrom(buffer_size)
        print(f"Packet received on {satellite_id}")
        # Decode the packet
        decode_res = decode_packet(data)
        if(decode_res['control_flag'] == CONTROL_FLAGS['path']) and verify_checksum(decode_res['payload'],decode_res['checksum']):
            packet_json = decode_res['payload']
            path_info = json.loads(packet_json)
            print(f"{satellite_id} received path from {path_info['sender']}")

            # Check if there are more hops in the path
            if path_info.get("path") and len(path_info["path"]) > 0:
                # print(f"----path:{path_info['path']}-----")
                next_hop = path_info["path"].pop(0)  # Get the next hop from the path
                payload_json = json.dumps(path_info)
                payload = payload_json.encode('utf-8')
                dumpy_src_addr, dumpy_src_port = decode_res['src_addr'][0],decode_res['src_addr'][1]
                dumpy_des_addr, dumpy_des_port = decode_res['des_addr'][0],decode_res['des_addr'][1]
                print(dumpy_src_addr)
                print(dumpy_src_port)
                packet = create_udp_packet(dumpy_src_addr, dumpy_src_port, dumpy_des_addr, dumpy_des_port, payload,
                                           flag='path')

                if next_hop in receiver_ports:
                    # send out message ot the top of the queue
                    # this server address should be decided by the rounting manager
                    router_addr = ['127.0.0.1', receiver_ports[next_hop]]  # current receiver satellite(router) address
                    message = message_queue.get()
                    send_packets(decode_res['src_addr'], decode_res['des_addr'], router_addr, message, suppress_log=True)

                    time.sleep(1)
                    send_path(
                        satellite_id,  # Current satellite
                        next_hop,  # Next satellite in the path
                        receiver_ports[next_hop],  # Next satellite's receiving port
                        packet  # Packet to be sent
                    )

            else:
                print("-----------------------------------------------------------")
                print(f"{satellite_id} has no more hops. Packet delivered.")
                message = message_queue.get()
                print("Reconstructed String:", message)
                print("------------------------P2P NET SUCCESS!--------------------")

        elif (decode_res['control_flag'] == CONTROL_FLAGS['data']) and verify_checksum(decode_res['payload'], decode_res['checksum']):
            message = send_ack(('127.0.0.1', server_addr),client_address,server_socket,decode_res,received_packets,suppress_log=True)
            if message is not None:
                message_queue.put(message)

        elif (decode_res['control_flag'] == CONTROL_FLAGS['inquiry']) and verify_checksum(decode_res['payload'],decode_res['checksum']):
            try:
                lat, lon = global_dequeue[sat_node_number-1].pop()
            except IndexError:
                # give a out of range latitude(it should be from -90 to 90) to imply error
                lat, lon = -800, -800
            print(f"server_addr:{server_addr}")
            answer_inquiry(('127.0.0.1', server_addr),client_address,server_socket,lat,lon)
        else:
            print(f"Checksum mismatch for packet {decode_res['packet_num']}. Packet discarded.")


if __name__ == "__main__":
    # SERVER_ADDR = ('localhost', 8080)
    SAT_ADDR = {
        1: { 'send': 50010, 'receive': 50011 },
        2: { 'send': 50012, 'receive': 50013 },
        3: { 'send': 50014, 'receive': 50015 },
        4: { 'send': 50016, 'receive': 50017 },
        5: { 'send': 50018, 'receive': 50019 }
    }
    # seperate dictonary for receiver ports
    receiver_ports = {
        "sat1": 50011,
        "sat2": 50013,
        "sat3": 50015,
        "sat4": 50017,
        "sat5": 50019,
        "earth2": 50021
    }
    EARTH2_LL = (0, -40)
    BUFFER_SIZE = 1024
    NUM_SATS = 5
    SAT_INDEX = 5 #0 to 4= 5 sats
    # SAT_NODE_NUM=0
    ORBIT_Z_AXIS = (0, 0)
    server_threads = []
    # from the starlink article, https://blog.apnic.net/2024/05/17/a-transport-protocols-view-of-starlink/
    # the satellite's speed is about 27000km/hour on with the height of 550km
    # on the equator of earth surface, 1 degree of longitude is about 111.3km
    VELOCITY = 27000 / 111.3 / (60 * 60)
    print(f"velocity:{VELOCITY}")
    global_dequeue = []#deque(maxlen=10)
    for i in range(NUM_SATS):
        global_dequeue.append(deque(maxlen=10))

    simulation_thread = threading.Thread(target=keep_moving,
                                         args=(global_dequeue, ORBIT_Z_AXIS, NUM_SATS, VELOCITY, SAT_INDEX),
                                         daemon=True)
    for node_id, (node_name, port) in enumerate(receiver_ports.items()):

        server_threads.append(threading.Thread(target=server, args=(global_dequeue, port, receiver_ports,BUFFER_SIZE,
                                                                    node_name,node_id),daemon=True))
        # server_threads[-1].start()

    # start the threads
    simulation_thread.start()
    for i in range(0, len(receiver_ports.keys())):
        server_threads[i].start()

    # keep the main program alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")
