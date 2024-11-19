from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os
import base64

def generate_aes_key_and_save(password, output_file="aes_key_salt.txt"):
    """
    Generate an AES key and save it with the salt to a file.
    """
    # Generate a random 16-byte salt
    salt = os.urandom(16)

    # Generate a 256-bit AES key using PBKDF2 with SHA256
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode('utf-8'))
    aes_key = base64.urlsafe_b64encode(key)
    encoded_salt = base64.urlsafe_b64encode(salt)

    # Save the key and salt to a file
    with open(output_file, "w") as f:
        f.write("AES Key: " + aes_key.decode('utf-8') + "\n")
        f.write("Salt: " + encoded_salt.decode('utf-8') + "\n")

    print(f"Generated AES key and salt saved to {output_file}")

if __name__ == "__main__":
    password = input("Enter a strong password to derive the AES key: ")
    output_file = "aes_key_salt.txt"  # Change the filename if needed
    generate_aes_key_and_save(password, output_file)
