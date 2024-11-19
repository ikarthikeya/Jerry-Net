import time
import json
import socket
import zlib
from queue import Queue
import threading

# our protocol details are as below
# source_ip + port: 6byte
# destination_ip + port: 6byte
# control flag: 1byte
# time-to-live: 1byte
# packet number: 4byte
# total packet number: 4byte
# checksum: 4byte
# total data length: 4byte
# payload

# global dictionary for control flag
CONTROL_FLAGS = {
    "data": 0,
    "ack": 1,
    "inquiry": 2,
}


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


def create_ll_inquiry(src_addr,des_addr):
    (src_ip, src_port) = src_addr
    (des_ip, des_port) = des_addr
    # latitude/longitude inquiry
    dumpy_payload="xxx"
    dumpy_payload = dumpy_payload.encode('utf-8')
    return create_udp_packet(src_ip,src_port,des_ip,des_port,dumpy_payload,
                             flag='inquiry')


def create_udp_packet(src_ip,src_port,des_ip,des_port,payload,
                      packet_number=0,total_packets=0,
                      flag='data',ttl=64):
    packet_len = len(payload) + 30
    checksum = calculate_checksum(payload)
    src_bytes = socket.inet_aton(socket.gethostbyname(src_ip)) + src_port.to_bytes(2, 'big')  # 6bytes
    des_bytes = socket.inet_aton(socket.gethostbyname(des_ip)) + des_port.to_bytes(2, 'big')  # 6bytes
    flag_bytes = CONTROL_FLAGS[flag].to_bytes(1, 'big')  # 1 byte
    ttl_bytes = ttl.to_bytes(1, 'big')
    packet_num_bytes = packet_number.to_bytes(4, 'big')
    total_packet_bytes = total_packets.to_bytes(4, 'big')
    crc_bytes = checksum.to_bytes(4, 'big')
    length_bytes = packet_len.to_bytes(4, 'big')
    header = src_bytes + des_bytes + flag_bytes + ttl_bytes \
             + packet_num_bytes + total_packet_bytes + crc_bytes + length_bytes
    packet = header + payload
    return packet


def batch_udp_packets(src_ip,src_port,des_ip,des_port,message,chunk_size=32,ttl=64):
    # encode the json message into binary data
    binary_stream = message.encode('utf-8')
    chunks = [binary_stream[i:i+chunk_size] for i in range(0,len(binary_stream),chunk_size)]
    total_packets = len(chunks)
    for packet_number, chunk in enumerate(chunks):
        packet = create_udp_packet(src_ip, src_port, des_ip, des_port, chunk,
                                    packet_number, total_packets,flag='data')
        yield packet, packet_number,total_packets


def decode_packet(packet):
    # Decode the packet
    src_ip = int.from_bytes(packet[:4],'big')
    src_port = int.from_bytes(packet[4:6],'big')
    des_ip = int.from_bytes(packet[6:10],'big')
    des_port = int.from_bytes(packet[10:12],'big')
    control_flag = int.from_bytes(packet[12:13],'big')
    ttl = int.from_bytes(packet[13:14], 'big')
    packet_num = int.from_bytes(packet[14:18], 'big')
    total_packet = int.from_bytes(packet[18:22], 'big')
    checksum = int.from_bytes(packet[22:26], 'big')
    length = int.from_bytes(packet[26:30], 'big')
    payload = packet[30:]
    res = {
        "src_addr": (src_ip,src_port),
        "des_addr": (des_ip,des_port),
        "control_flag":control_flag,
        "ttl":ttl,
        "packet_num":packet_num,
        "total_packet": total_packet,
        "checksum":checksum,
        "packet_length":length,
        "payload":payload,
    }
    return res


def send_packets(src_addr,des_addr,router_addr,message,timeout=1,chunk_size=32,buffer_size=1024,debug_interval=1):
    src_ip, src_port = src_addr
    des_ip, des_port = des_addr
    router_ip, router_port = router_addr
    udp_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sender.settimeout(timeout)

    print(f"\nSending packet from {src_ip}:{src_port} to {des_ip}:{des_port}\n")
    print(f"\nRouting to {router_ip}:{router_port}\n")

    # maintain a queue for retransmitting
    total_packets = None
    sending_queue = Queue()
    total_send = 0
    rtts = []
    for packet,packet_number,total_packets in \
            batch_udp_packets(src_ip,src_port,des_ip,des_port,message,
                                         chunk_size=chunk_size):
        # put packet into queue
        total_packets = total_packets
        sending_queue.put((packet_number, packet))

    # send package from sending queue
    while not sending_queue.empty():
        packet_number, packet = sending_queue.get()
        print(f"Sent packet {packet_number}/{total_packets}")
        try:
            # send the packet
            total_send += 1
            start_time = time.time()
            udp_sender.sendto(packet, router_addr)
            # Wait for acknowledgement
            ack, _ = udp_sender.recvfrom(buffer_size)
            end_time = time.time()
            # round trip time
            rtt = (end_time - start_time) * 1000  # convert to milliseconds
            rtts.append(rtt)
            # decode ack_message
            decode_res = decode_packet(ack)
            assert decode_res['control_flag'] == CONTROL_FLAGS['ack'], "ack flag error, resending..."
            assert decode_res['packet_num'] == packet_number, "ack packet_number mismatch, resending..."
            assert verify_checksum(decode_res['payload'], decode_res['checksum']), "ack checksum error, resending..."
            print(f"Received ACK from {router_addr[0]}:{router_addr[1]}: packet_num={packet_number}, time={rtt:.2f} ms")
        except socket.timeout:
            print(f"Timeout: packet_num={packet_number}, resending...")
            sending_queue.put((packet_number, packet))
        except Exception:
            sending_queue.put((packet_number, packet))
        time.sleep(debug_interval)
    print(f"---UDP packets all sent: statistics below---\n")
    packets_transmitted = total_send
    packets_received = len(rtts)
    packet_lost_count = packets_transmitted - packets_received
    packet_loss = ((packets_transmitted - packets_received) / packets_transmitted) * 100
    print(f"{packets_transmitted} packets transmitted, "
          f"{packets_received} received, "
          f"{packet_lost_count} lost.")
    print(f"({packet_loss:.1f}% loss)\n")
    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        print(f"rtt min={min_rtt:.2f} ms, avg={avg_rtt:.2f} ms, max={max_rtt:.2f} ms\n")
    else:
        print("No RTT data available.\n")


def send_ack(server_addr,sending_address,server_socket,decode_res,received_packets):
    """
    pure sending data acknowledgement function,
    since server thread might have other functions,
    it is possible server has multiple functions including this one.
    """
    control_flag = decode_res['control_flag']
    packet_number = decode_res['packet_num']
    total_packet = decode_res['total_packet']
    checksum = decode_res['checksum']
    payload = decode_res['payload']
    # verify if it's a valid packet
    if (control_flag==CONTROL_FLAGS['data']) and verify_checksum(payload,checksum):
        # Store the packet content
        if sending_address in received_packets.keys():
            received_packets[sending_address][packet_number] = payload
        else:
            received_packets[sending_address] = {}
            received_packets[sending_address][packet_number] = payload
        print(f"Received packet {packet_number}/{total_packet} from {sending_address}")

        # Send acknowledgment for the received packet
        ack_message = create_udp_packet(server_addr[0], server_addr[1],
                                        sending_address[0], sending_address[1], payload,
                                        packet_number=packet_number,total_packets=0,flag='ack')
        server_socket.sendto(ack_message, sending_address)

        # If all packets are received, reassemble the binary stream
        if len(received_packets[sending_address]) == total_packet:
            print(f"All packets frome address {sending_address} received!")
            # Reassemble and decode the original string
            binary_stream = b''.join(received_packets[sending_address][i] for i in range(total_packet))
            original_string = binary_stream.decode()
            print("Reconstructed String:", original_string)


def answer_inquiry(server_addr,sending_address,server_socket,lat,lon):
    """
    answer latitude/longitude inquiry
    """
    ll_data = json.dumps({'lat':lat,'lon':lon})
    payload = ll_data.encode('utf-8')
    ack = create_udp_packet(server_addr[0],server_addr[1],sending_address[0],sending_address[1],
                      payload,flag='ack')
    server_socket.sendto(ack, sending_address)


def test_server(host, port):
    # create local server to listen for incoming messages.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"Server is listening on {host}:{port}")
    received_packets = {}
    while True:
        # Receive a packet
        packet, sending_address = server_socket.recvfrom(1024)
        # Decode the packet
        decode_res = decode_packet(packet)
        send_ack((host,port),sending_address,server_socket,decode_res,received_packets)


if __name__ == "__main__":
    server_host, server_port = 'localhost', 8080
    threading.Thread(target=test_server, args=(server_host, server_port),
                     daemon=True).start()
    message = "This is a test string that will be sent as binary data over UDP in smaller packets."
    send_packets(('127.0.0.1',8081), ('127.0.0.1',8082), (server_host, server_port), message)
    # keep the main program alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")
















