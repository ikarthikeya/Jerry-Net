import socket

def forward_data(data, target_address):
    """
    Forward data to the specified target address.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as forward_socket:
        forward_socket.sendto(data, target_address)
        print(f"Forwarded data to {target_address}: {data.decode('utf-8')}")

if __name__ == "__main__":
    CLIENT_ADDR = ('localhost', 8081)  # Address to bind Satellite (client)
    SERVER_ADDR = ('localhost', 8080)  # Address of Earth1 (server)
    EARTH2_ADDR = ('localhost', 8082)  # Address of Earth2 (receiver)
    BUFFER_SIZE = 1024

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.bind(CLIENT_ADDR)
        print(f"Satellite Client is listening on {CLIENT_ADDR}...")

        # Send a request to Earth1 Server
        request_message = "Request data"
        client_socket.sendto(request_message.encode('utf-8'), SERVER_ADDR)
        print(f"Request sent to Server: {request_message}")

        # Receive the encrypted data from the server
        encrypted_data, server_address = client_socket.recvfrom(BUFFER_SIZE)
        print(f"Encrypted Data Received from {server_address}: {encrypted_data.decode('utf-8')}")

        # Forward the encrypted data to Earth2
        forward_data(encrypted_data, EARTH2_ADDR)
