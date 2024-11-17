from collections import deque
import socket
import threading
import time
from movement_simulation import init_satellites, satellites_move


def keep_moving(global_dequeue,orbit_z_axis,num_sats,velocity,sat_index):
    sat_ll_list = init_satellites(orbit_z_axis, num_sats)
    # initial lat, lon of the satellite
    (lat,lon) = sat_ll_list[sat_index]
    start_time = time.time()
    while True:
        time.sleep(1)
        end_time = time.time()
        t = end_time-start_time
        start_time = end_time
        lat, lon = satellites_move((lat,lon), orbit_z_axis, velocity, t)
        print(f"Satellites keeps moving: time slaps {t}, latitude {lat}, longitude {lon}")
        # update data in global queue for multi-threading data share
        global_dequeue.append((lat,lon))


def server(global_dequeue,server_addr, buffer_size, sat_node_number):
    #create udp satellite server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_addr)

    print(f"Satellite with node number {sat_node_number} is listening on {server_addr[0]}:{server_addr[1]}...")
    received_packets = {}
    total_packets_dict = {}  # Total packets to expect

    while True:
        # Receive a packet
        data, client_address = server_socket.recvfrom(buffer_size)
        print("Packet received!")
        # Decode the packet
        flag, node_number, packet_number, total_packets, chunk = data[:4],data[4:8],data[8:12], data[12:16], data[16:]
        flag = int.from_bytes(flag,'big')
        node_number = int.from_bytes(node_number,'big') # for satellites, node_number= sat_index, for
        packet_number = int.from_bytes(packet_number, 'big')
        total_packets = int.from_bytes(total_packets, 'big')
        total_packets_dict[node_number] = total_packets
        if flag == 0:
            try:
                lat,lon = global_dequeue.pop()
            except global_dequeue.Empty:
                # give a out of range latitude(it should be from -90 to 90) to imply error
                lat, lon = -800, -800
            # send out latitude, longitude info to earth station
            lat_info = int(lat).to_bytes(4,'big',signed=True)
            lon_info = int(lon).to_bytes(4,'big',signed=True)
            ll_info = flag.to_bytes(4,'big')+sat_node_number.to_bytes(4,'big')+lat_info+lon_info
            server_socket.sendto(ll_info, client_address)
        else:
            # Store the packet content
            if node_number in received_packets.keys():
                received_packets[node_number][packet_number] = chunk
            else:
                received_packets[node_number] = {}
                received_packets[node_number][packet_number] = chunk
            print(f"Received packet {packet_number}/{total_packets} from {client_address}")

            # Send acknowledgment for the received packet
            ack = flag.to_bytes(4,'big')+sat_node_number.to_bytes(4,'big')+packet_number.to_bytes(4, 'big')
            server_socket.sendto(ack, client_address)

            # If all packets are received, reassemble the binary stream
            if len(received_packets[node_number]) == total_packets:
                print(f"All packets frome node {node_number} received!")
                # Reassemble and decode the original string
                binary_stream = b''.join(received_packets[node_number][i] for i in range(total_packets))
                original_string = binary_stream.decode()
                print("Reconstructed String:", original_string)


if __name__ == "__main__":
    global_dequeue = deque(maxlen=10)
    SERVER_ADDR = ('localhost', 8080)
    BUFFER_SIZE = 1024
    NUM_SATS = 5
    SAT_INDEX=0
    SAT_NODE_NUM=0
    ORBIT_Z_AXIS=(0,0)
    # from the starlink article, https://blog.apnic.net/2024/05/17/a-transport-protocols-view-of-starlink/
    # the satellite's speed is about 27000km/hour on with the height of 550km
    # on the equator of earth surface, 1 degree of longitude is about 111.3km
    VELOCITY = 27000/111.3/(60*60)
    print(f"velocity:{VELOCITY}")

    simulation_thread = threading.Thread(target=keep_moving, args=(global_dequeue,ORBIT_Z_AXIS,NUM_SATS,VELOCITY,SAT_INDEX),
                     daemon=True)
    server_thread = threading.Thread(target=server, args=(global_dequeue,SERVER_ADDR, BUFFER_SIZE, SAT_NODE_NUM),
                     daemon=True)

    # start the threads
    simulation_thread.start()
    server_thread.start()

    # keep the main program alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")
