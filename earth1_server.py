import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import base64

def read_key_and_salt(file_path="aes_key_salt.txt"):
    """
    Reads the AES key and salt from the specified file and ensures proper formatting.
    """
    with open(file_path, "r") as file:
        lines = file.readlines()
        aes_key = lines[0].split(":")[1].strip()  # Extract AES key
        salt = lines[1].split(":")[1].strip()     # Extract salt
    return aes_key, salt

def pad_base64(data):
    """
    Adds padding to a Base64 string if necessary.
    """
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += "=" * (4 - missing_padding)
    return data

def aes_encrypt(data, key):
    """
    Encrypts data using AES with the given key.
    """
    try:
        # Ensure key is properly padded and decoded
        key = pad_base64(key.strip())
        decoded_key = base64.urlsafe_b64decode(key)
        iv = os.urandom(16)  # Generate a random Initialization Vector (IV)
        cipher = Cipher(algorithms.AES(decoded_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
        return base64.urlsafe_b64encode(iv + encrypted_data).decode('utf-8')
    except Exception as e:
        print(f"Error during encryption: {e}")
        raise

if __name__ == "__main__":
    # Read AES Key and Salt from File
    try:
        AES_KEY, _ = read_key_and_salt("aes_key_salt.txt")
    except Exception as e:
        print(f"Failed to read AES key and salt: {e}")
        exit(1)

    # Configuration
    SERVER_ADDR = ('localhost', 8080)  # Address to bind Earth1 (server)
    BUFFER_SIZE = 1024

    # Start the server
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(SERVER_ADDR)
        print(f"Earth1 Server is listening on {SERVER_ADDR}...")

        while True:
            # Wait for a request from the satellite
            print("Waiting for request from Satellite...")
            try:
                request, client_address = server_socket.recvfrom(BUFFER_SIZE)
                print(f"Received request from {client_address}: {request.decode('utf-8')}")
            except Exception as e:
                print(f"Error receiving request: {e}")
                continue

            # Generate the message and encrypt it
            message = "Sensor data from Earth1"
            print(f"Original Message: {message}")

            try:
                encrypted_message = aes_encrypt(message, AES_KEY)
                print(f"Encrypted Message: {encrypted_message}")
            except Exception as e:
                print(f"Failed to encrypt the message: {e}")
                continue

            # Send the encrypted data to the satellite
            server_socket.sendto(encrypted_message.encode('utf-8'), client_address)
            print("Encrypted data sent to Satellite.")
