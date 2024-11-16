import socket

if __name__ == "__main__":
    # configuration
    SERVER_ADDR=('localhost',8080)
    BUFFER_SIZE = 1024

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(SERVER_ADDR)
        print(f"Server is listening on {SERVER_ADDR[0]}:{SERVER_ADDR[1]}...")

        received_packets = {}
        total_packets = None  # Total packets to expect

        while True:
            # Receive a packet
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)

            # Decode the packet
            packet_number, total_packets, chunk = data[:4], data[4:8], data[8:]
            packet_number = int.from_bytes(packet_number, 'big')
            total_packets = int.from_bytes(total_packets, 'big')

            # Store the packet content
            received_packets[packet_number] = chunk
            print(f"Received packet {packet_number}/{total_packets} from {client_address}")

            # Send acknowledgment for the received packet
            ack = packet_number.to_bytes(4, 'big')
            server_socket.sendto(ack, client_address)

            # If all packets are received, reassemble the binary stream
            if len(received_packets) == total_packets:
                print("All packets received!")
                # Reassemble and decode the original string
                binary_stream = b''.join(received_packets[i] for i in range(total_packets))
                original_string = binary_stream.decode()
                print("Reconstructed String:", original_string)

