"""
aes encryption and decryption: Sanjiv
"""
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