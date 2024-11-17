import subprocess
import socket
import time
import numpy as np
import threading
import psutil


def start_clumsy(single_latency,single_drop_rate):
    # clumsy working directory
    CLUM_DIR = "clumsy"
    # Start Clumsy with 10% packet loss
    cmd = f"clumsy.exe --drop on --drop-inbound on --drop-outbound on --drop-chance {single_drop_rate} " \
          f"--lag on --lag-inbound on --lag-outbound on --lag-time {single_latency}"
    process = subprocess.Popen(cmd, cwd=CLUM_DIR,shell=True)
    print("clumsy started.")
    return process.pid


def kill_clumsy(pid):
    # Terminate the Clumsy process
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()
    print("clumsy stopped.")


def earth_sat_distance(earth_lat,earth_lon,sat_lat,sat_lon):
    # according to the starlink blog, https://blog.apnic.net/2024/05/17/a-transport-protocols-view-of-starlink/
    # the height of a satellite is about 550km
    SAT_H = 550.
    EARTH_R = 6378.
    # calculate cartesian coordinates for earth station:
    x_earth = EARTH_R * np.cos(np.radians(earth_lat)) * np.cos(np.radians(earth_lon))
    y_earth = EARTH_R * np.cos(np.radians(earth_lat)) * np.sin(np.radians(earth_lon))
    z_earth = EARTH_R * np.sin(np.radians(earth_lon))
    # calculate cartesian coordinates for the satellite:
    sat_r = EARTH_R + SAT_H
    x_sat = sat_r * np.cos(np.radians(sat_lat)) * np.cos(np.radians(sat_lon))
    y_sat = sat_r * np.cos(np.radians(sat_lat)) * np.sin(np.radians(sat_lon))
    z_sat = sat_r * np.sin(np.radians(sat_lon))
    # calculate distance between earth and satellite
    distance = np.sqrt((x_sat - x_earth) ** 2 + (y_sat - y_earth) ** 2 + (z_sat - z_earth) ** 2)
    return distance


def e2s_lantency(earth_lat,earth_lon,sat_lat,sat_lon):
    # light speed constant
    LIGHT_V = 300000. # km/s
    # calculate distance between earth and satellite
    distance = earth_sat_distance(earth_lat,earth_lon,sat_lat,sat_lon)
    # suppose radio wave is transmitted with light speed
    single_bound_lantency = distance/LIGHT_V
    return single_bound_lantency*1000 # return in miniseconds


def e2s_packet_loss(earth_lat,earth_lon,sat_lat,sat_lon):
    SAT_H = 550.
    # calculate distance between earth and satellite
    distance = earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon)
    # man-made function, this function is chosen as packet loss accelerates to increase when the distance increases
    single_bound_loss_rate = min(0.02*np.exp((distance-SAT_H)/1000.), 1.0)
    return single_bound_loss_rate*100


def clumsy_simulate(server_addr,buffer_size,timeout,self_ll,self_node_num):
    inquire_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inquire_socket.settimeout(timeout)
    self_lat,self_lon = self_ll
    clumsy_pid = None
    # simulate different latency and drag for every three seconds
    while True:
        # inquire server about satellites index and latitude,longitude information
        flag = 0
        pn,tp,cu = 0,0,0 # dummy parameters here, they are neglected in flag=0 case
        header = flag.to_bytes(4, 'big') + self_node_num.to_bytes(4, 'big')\
                 +pn.to_bytes(4, 'big') + tp.to_bytes(4, 'big')
        inquiry = header+cu.to_bytes(4, 'big')
        #print("start inquiry...")
        try:
            # send the inquiry
            inquire_socket.sendto(inquiry, server_addr)
            #print("inquiry sent...")
            # Wait for acknowledgement
            ack, _ = inquire_socket.recvfrom(buffer_size)
            #print("ack received..")
            # Decode the packet
            flag, node_number, lat_info, lon_info= ack[:4], ack[4:8], ack[8:12], ack[12:16]
            flag = int.from_bytes(flag, 'big')
            assert flag == 0, "Received wrong acknowledgement for latitude/longitude inquiry"
            node_number = int.from_bytes(node_number, 'big')
            sat_lat = int.from_bytes(lat_info, 'big',signed=True)
            sat_lon = int.from_bytes(lon_info, 'big',signed=True)
            # calculate latency and packet loss rate
            distance = earth_sat_distance(self_lat,self_lon,sat_lat,sat_lon)
            single_latency = e2s_lantency(self_lat,self_lon,sat_lat,sat_lon)
            single_drop_rate = e2s_packet_loss(self_lat,self_lon,sat_lat,sat_lon)
            print(f"earth lat {self_lat},earth lon {self_lon},sat lat {sat_lat}, sat lon {sat_lon}")
            print(f"E2S distance: {distance} km, single bound latency {single_latency} ms, single bound drop rate {single_drop_rate}")
            if clumsy_pid is not None:
                kill_clumsy(clumsy_pid)
            clumsy_pid = start_clumsy(single_latency,single_drop_rate)
        except socket.timeout:
            pass
        time.sleep(3)


def client(server_addr, buffer_size, timeout,debug_interval, chunk_size, self_node_num):
    # Data to be sent
    message = "This is a test string that will be sent as binary data over UDP in smaller packets."
    binary_stream = message.encode('utf-8')
    chunks = [binary_stream[i:i + chunk_size] for i in range(0, len(binary_stream), chunk_size)]
    total_packets = len(chunks)
    total_send = 0
    rtts = []

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)  # set timeout
    print(f"\nSending udp://{server_addr[0]}:{server_addr[1]} with {total_packets} packets:\n")

    for packet_number, chunk in enumerate(chunks):
        # header = packet_number(32bit), total_packets(32bit)
        flag = 1
        header = flag.to_bytes(4, 'big') + self_node_num.to_bytes(4, 'big') \
                 + packet_number.to_bytes(4, 'big') + total_packets.to_bytes(4, 'big')
        packet = header + chunk
        print(f"Sent packet {packet_number}/{total_packets}")
        while True:
            try:
                # send the packet
                total_send += 1
                start_time = time.time()
                client_socket.sendto(packet, server_addr)
                # Wait for acknowledgement
                ack, _ = client_socket.recvfrom(buffer_size)
                end_time = time.time()
                # round trip time
                rtt = (end_time - start_time) * 1000  # convert to milliseconds
                rtts.append(rtt)
                ack_number = int.from_bytes(ack, 'big')
                print(
                    f"Received ACK from {server_addr[0]}:{server_addr[1]}: packet_num={ack_number}, time={rtt:.2f} ms")
                break
            except socket.timeout:
                print(f"Timeout: packet_num={packet_number}, resending...")
            except Exception:
                print(f"Request failed, packet_num={packet_number}")
            time.sleep(debug_interval)
        time.sleep(debug_interval)

    print(f"\n--- UDP://{server_addr[0]}:{server_addr[1]} statistics ---\n")
    packets_transmitted = total_send
    packets_received = len(rtts)
    packet_lost_count = packets_transmitted - packets_received
    packet_loss = ((packets_transmitted - packets_received) / packets_transmitted) * 100
    print(f"{packets_transmitted} packets transmitted, "
          f"{packets_received} received, "
          f"{packet_lost_count} lost.")
    if packet_loss == 0:
        print(f"({packet_loss:.1f}% loss)\n")
    elif packet_loss < 80:
        print(f"({packet_loss:.1f}% loss)\n")
    else:
        print(f"({packet_loss:.1f}% loss)\n")

    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        print(f"rtt min={min_rtt:.2f} ms, avg={avg_rtt:.2f} ms, max={max_rtt:.2f} ms\n")
    else:
        print("No RTT data available.\n")


if __name__ == "__main__":
    SERVER_ADDR = ('localhost', 8080)
    BUFFER_SIZE = 1024
    EARTH_LL =(0,-180) # latitude, longitude
    EARTH_NODE_NUM=10
    TIMEOUT=2 # 2s timeout for inquiry satellites latitude and longitude information
    DEBUG_INTER = 1 # 1s
    CHUNK_SIZE =10 #bit
    clumsy_thread = threading.Thread(target=clumsy_simulate,
                                     args=(SERVER_ADDR,BUFFER_SIZE,TIMEOUT,EARTH_LL,EARTH_NODE_NUM),
                                     daemon=True)
    client_thread = threading.Thread(target=client,
                                     args=(SERVER_ADDR, BUFFER_SIZE, TIMEOUT,DEBUG_INTER, CHUNK_SIZE, EARTH_NODE_NUM),
                                     daemon=True)
    # start the threads
    clumsy_thread.start()
    client_thread.start()

    # keep the main program alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")