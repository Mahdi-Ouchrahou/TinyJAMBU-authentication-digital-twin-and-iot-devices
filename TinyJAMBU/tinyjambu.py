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
def encrypt_192(key, nonce, data, text):
    state = [0, 0, 0, 0]
    key_ = [0, 0, 0, 0]

    for i in range(4):
        key_[i] = utility.from_le_bytes(key[i * 4: (i + 1) * 4])

    state = functions.initialize_192(state, key_, nonce)
    state = functions.process_associated_data_192(state, key_, data)
    state, cipher = functions.process_plain_text_192(state, key_, text, len(text))  # Pass 'len(text)' as ct_len
    tag = functions.finalize_192(state, key_)
    return cipher, tag

# TinyJambu-192 Verified Decryption
def decrypt_192(key, nonce, tag, data, cipher):
    state = [0, 0, 0, 0]
    key_ = [0, 0, 0, 0]
    tag_ = [0, 0, 0, 0, 0, 0, 0, 0]

    for i in range(4):
        key_[i] = utility.from_le_bytes(key[i * 4: (i + 1) * 4])

    state = functions.initialize_192(state, key_, nonce)
    state = functions.process_associated_data_192(state, key_, data)
    state, text = functions.process_cipher_text_192(state, key_, cipher, len(cipher))  # Add ct_len argument
    functions.finalize_192(state, key_, tag_)

    # Verify the authentication tag
    is_verified = all(tag[i] == tag_[i] for i in range(8))

    # Prevent release of unverified plain text
    if not is_verified:
        text = b'\x00' * len(text)

    return text, is_verified

def encrypt_256(key, nonce, data, text):
    state = [0, 0, 0, 0]
    key_ = [0, 0, 0, 0]

    for i in range(4):
        key_[i] = utility.from_le_bytes(key[i * 4: (i + 1) * 4])

    state = functions.initialize_256(state, key_, nonce)
    state = functions.process_associated_data_256(state, key_, data)
    state, cipher = functions.process_plain_text_256(state, key_, text, len(text))  # Pass 'len(text)' as ct_len
    tag = functions.finalize_256(state, key_)
    return cipher, tag

# TinyJambu-192 Verified Decryption
def decrypt_256(key, nonce, tag, data, cipher):
    state = [0, 0, 0, 0]
    key_ = [0, 0, 0, 0]
    tag_ = [0, 0, 0, 0, 0, 0, 0, 0]

    for i in range(4):
        key_[i] = utility.from_le_bytes(key[i * 4: (i + 1) * 4])

    state = functions.initialize_256(state, key_, nonce)
    state = functions.process_associated_data_256(state, key_, data)
    state, text = functions.process_cipher_text_256(state, key_, cipher, len(cipher))  # Add ct_len argument
    functions.finalize_256(state, key_, tag_)

    # Verify the authentication tag
    is_verified = all(tag[i] == tag_[i] for i in range(8))

    # Prevent release of unverified plain text
    if not is_verified:
        text = b'\x00' * len(text)

    return text, is_verified

def choose_variant():
    print("Choose the TinyJambu variant:")
    print("1. TinyJambu-128")
    print("2. TinyJambu-192")
    print("3. TinyJambu-256")
    choice = int(input("Enter your choice (1/2/3): "))
    
    if choice == 1:
        return 16, 16  # 128-bit key and nonce
    elif choice == 2:
        return 24, 16  # 192-bit key and nonce
    elif choice == 3:
        return 32, 16  # 256-bit key and 192-bit nonce

def simulate_authentication_failure(cipher, tag):
    # Modify the last byte of the ciphertext or tag
    modified_cipher = cipher[:-1] + bytes([cipher[-1] ^ 0x01])
    #modified_tag = tag[:-1] + bytes([tag[-1] ^ 0x01])
    return modified_cipher

# Test the encryption and decryption
if __name__ == "__main__":
    key_size, nonce_size = choose_variant()
    key = utility.random_data(key_size)
    nonce = utility.random_data(nonce_size)
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

    # Choose the appropriate encryption and decryption functions based on the selected variant
    if key_size == 16:
        encrypt_func = encrypt
        decrypt_func = decrypt
    elif key_size == 24:
        encrypt_func = encrypt_192
        decrypt_func = decrypt_192
    elif key_size == 32:
        encrypt_func = encrypt_256
        decrypt_func = decrypt_256

    cipher, tag = encrypt_func(key, nonce, data, text)
    print("Encrypted cipher:", cipher)
    print("Authentication tag:", tag)
    mcipher = simulate_authentication_failure(cipher, tag)

    decrypted_text, is_verified = decrypt_func(key, nonce, tag, data, cipher)
    print("Decrypted text:", decrypted_text)
    print("Is verified:", is_verified)