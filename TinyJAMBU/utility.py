import struct
import random

#helper function to convert a sequence of little-endian bytes to an integer.
def from_le_bytes(bytes_data):
    return struct.unpack("<I", bytes_data)[0]

#helper function to convert an integer to a sequence of little-endian bytes.
def to_le_bytes(word):
    return struct.pack("<I", word)

#helper function that generates random bytes of a specified length.
def random_data(dt_len):
    return bytes(random.randint(0, 255) for _ in range(dt_len))

#helper function that converts bytes to a hexadecimal string representation.
def to_hex(bytes_data):
    return "".join(f"{byte:02x}" for byte in bytes_data)

# helper function that converts a hexadecimal string to bytes.
def hex_to_bytes(hex_string):
    # Remove leading and trailing whitespaces (including newline characters)
    hex_string = hex_string.replace(" ", "")
    # Ensure the hex_string has an even length
    if len(hex_string) % 2 != 0:
        hex_string = '0' + hex_string
    # Convert the hex string to bytes
    return bytes.fromhex(hex_string)