import socket
import time

if __name__ == "__main__":
    # printing format
    red = "\033[1;31m"
    yellow = "\033[1;33m"
    green = "\033[1;32m"
    reset = "\033[0m"

    # configuration
    SERVER_ADDR=('localhost',8080)
    BUFFER_SIZE = 1024
    CHUNK_SIZE = 10
    TIMEOUT = 1 # 1s
    DEBUG_INTERVAL= 1 # sending interval for debug
    # Data to be sent
    message = "This is a test string that will be sent as binary data over UDP in smaller packets."
    binary_stream = message.encode('utf-8')
    chunks = [binary_stream[i:i+CHUNK_SIZE] for i in range(0,len(binary_stream),CHUNK_SIZE)]
    total_packets = len(chunks)
    total_send = 0
    rtts =[]

    # Create a UDP socket
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as client_socket:
        client_socket.settimeout(TIMEOUT)  # set timeout
        print(f"\nSending udp://{SERVER_ADDR[0]}:{SERVER_ADDR[1]} with {total_packets} packets:\n")

        for packet_number, chunk in enumerate(chunks):
            # header = packet_number(32bit), total_packets(32bit)
            header = packet_number.to_bytes(4,'big') + total_packets.to_bytes(4,'big')
            packet = header+chunk
            print(f"Sent packet {packet_number}/{total_packets}")
            while True:
                try:
                    # send the packet
                    total_send += 1
                    start_time = time.time()
                    client_socket.sendto(packet, SERVER_ADDR)
                    # Wait for acknowledgement
                    ack,_ = client_socket.recvfrom(BUFFER_SIZE)
                    end_time = time.time()
                    # round trip time
                    rtt = (end_time-start_time)*1000 # convert to milliseconds
                    rtts.append(rtt)
                    ack_number = int.from_bytes(ack,'big')
                    print(f"Received ACK from {SERVER_ADDR[0]}:{SERVER_ADDR[1]}: packet_num={ack_number}, time={rtt:.2f} ms")
                    break
                except socket.timeout:
                    print(yellow+f"Timeout: packet_num={packet_number}, resending..."+reset)
                except Exception:
                    print(yellow + f"Request failed, packet_num={packet_number}" + reset)
                time.sleep(DEBUG_INTERVAL)
            time.sleep(DEBUG_INTERVAL)

    print(f"\n--- UDP://{SERVER_ADDR[0]}:{SERVER_ADDR[1]} statistics ---\n")
    packets_transmitted = total_send
    packets_received = len(rtts)
    packet_lost_count = packets_transmitted - packets_received
    packet_loss = ((packets_transmitted - packets_received) / packets_transmitted) * 100
    print(f"{packets_transmitted} packets transmitted, "
          f"{packets_received} received, "
          f"{packet_lost_count} lost.")
    if packet_loss == 0:
        print(green + f"({packet_loss:.1f}% loss)\n" + reset)
    elif packet_loss < 80:
        print(yellow + f"({packet_loss:.1f}% loss)\n" + reset)
    else:
        print(red + f"({packet_loss:.1f}% loss)\n" + reset)

    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        print(f"rtt min={min_rtt:.2f} ms, avg={avg_rtt:.2f} ms, max={max_rtt:.2f} ms\n")
    else:
        print("No RTT data available.\n")

