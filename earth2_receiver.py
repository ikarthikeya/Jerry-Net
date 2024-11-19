import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64

def read_key_and_salt(file_path="aes_key_salt.txt"):
    """
    Reads the AES key and salt from the specified file.
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

def aes_decrypt(encrypted_data, key):
    """
    Decrypts encrypted data using AES with the given key.
    """
    try:
        # Decode the Base64-encoded key and encrypted data
        key = pad_base64(key.strip())
        decoded_key = base64.urlsafe_b64decode(key)
        encrypted_data = base64.urlsafe_b64decode(pad_base64(encrypted_data))

        # Extract IV and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]

        # Decrypt the ciphertext
        cipher = Cipher(algorithms.AES(decoded_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(f"Error during decryption: {e}")
        raise

if __name__ == "__main__":
    RECEIVER_ADDR = ('localhost', 8082)  # Address to bind Earth2 (receiver)
    BUFFER_SIZE = 1024

    # Read AES Key and Salt from File
    try:
        AES_KEY, _ = read_key_and_salt("aes_key_salt.txt")
    except Exception as e:
        print(f"Failed to read AES key and salt: {e}")
        exit(1)

    # Start the receiver
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver_socket:
        receiver_socket.bind(RECEIVER_ADDR)
        print(f"Earth2 Receiver is listening on {RECEIVER_ADDR}...")

        while True:
            # Receive encrypted data from Satellite
            encrypted_data, sender_address = receiver_socket.recvfrom(BUFFER_SIZE)
            print(f"Encrypted Data Received from {sender_address}: {encrypted_data.decode('utf-8')}")

            # Decrypt the data
            try:
                decrypted_message = aes_decrypt(encrypted_data.decode('utf-8'), AES_KEY)
                print(f"Decrypted Message: {decrypted_message}")
            except Exception as e:
                print(f"Failed to decrypt the message: {e}")
