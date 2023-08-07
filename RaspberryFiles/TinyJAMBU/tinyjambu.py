import utility as utility
import functions as functions
import json

# TinyJambu-128 Authenticated Encryption
def encrypt(key, nonce, data, text):
    """
    Encrypts the given plaintext message along with associated data using TinyJAMBU-128.

    Args:
        key (bytes): The encryption key.
        nonce (bytes): The nonce.
        data (bytes): The associated data.
        text (bytes): The plaintext message.

    Returns:
        tuple: Encrypted cipher and authentication tag.
    """
    state = [0, 0, 0, 0]
    key_ = [0, 0, 0, 0]

    for i in range(4):
        key_[i] = utility.from_le_bytes(key[i * 4: (i + 1) * 4])

    state = functions.initialize(state, key_, nonce)
    state = functions.process_associated_data(state, key_, data)
    state, cipher = functions.process_plain_text(state, key_, text, len(text))  # Pass 'len(text)' as ct_len
    tag = functions.finalize(state, key_)
    return cipher, tag

# TinyJambu-128 Verified Decryption
def decrypt(key, nonce, tag, data, cipher):
    """
    Decrypts and verifies the authenticity of the given ciphertext using TinyJAMBU-128.

    Args:
        key (bytes): The decryption key.
        nonce (bytes): The nonce.
        tag (bytes): The authentication tag.
        data (bytes): The associated data.
        cipher (bytes): The ciphertext.

    Returns:
        tuple: Decrypted plaintext and verification status.
    """
    state = [0, 0, 0, 0]
    key_ = [0, 0, 0, 0]
    tag_ = [0, 0, 0, 0, 0, 0, 0, 0]

    for i in range(4):
        key_[i] = utility.from_le_bytes(key[i * 4: (i + 1) * 4])

    state = functions.initialize(state, key_, nonce)
    state = functions.process_associated_data(state, key_, data)
    state, text = functions.process_cipher_text(state, key_, cipher, len(cipher))  # Add ct_len argument
    functions.finalize(state, key_, tag_)
    print("computed tag:", utility.to_hex(tag_))

    # Verify the authentication tag
    is_verified = all(tag[i] == tag_[i] for i in range(8))

    # Prevent release of unverified plain text
    if not is_verified:
        text = b'\x00' * len(text)

    return text, is_verified

# Test the encryption and decryption
if __name__ == "__main__":
    key = utility.random_data(16)
    nonce = utility.random_data(12)
    nonce2 = utility.random_data(12)
    data = b""
    message_json = {
    "temperature": 20.1,
    "humidity": 70,
    "deviceId": "sensors:authenticated"
    }

# Convert dictionary to JSON string and then encode to bytes
    message_str = json.dumps(message_json)
    text = message_str.encode('utf-8')  

    print("Original key:", utility.to_hex(key))
    print("Original nonce:", nonce)
    print("Original data:", data)
    print("Original text:", message_str)

    cipher, tag = encrypt(key, nonce, data, text)
    print("Encrypted cipher:", cipher)
    print("Authentication tag:", tag)

    decrypted_text, is_verified = decrypt(key, nonce, tag, data, cipher)
    print("Decrypted text:", decrypted_text)
    print("Is verified:", is_verified)
