import struct
import copy

# Define the FRAMEBITS_NONCE, FRAMEBITS_AD, FRAMEBITS_CT, and FRAMEBITS_TAG
FRAMEBITS_NONCE = 0x10
FRAMEBITS_AD = 0x30
FRAMEBITS_CT = 0x50
FRAMEBITS_TAG = 0x70

# function to update the state array using the specified number of rounds.
def state_update(S, K, rounds):
    
    itr_cnt = rounds >> 5

    for i in range(itr_cnt):
        s47 = (S[2] << 17) | (S[1] >> 15)
        s70 = (S[3] << 26) | (S[2] >> 6)
        s85 = (S[3] << 11) | (S[2] >> 21)
        s91 = (S[3] << 5) | (S[2] >> 27)

        fbk = S[0] ^ s47 ^ (~(s70 & s85)) ^ s91 ^ K[i & 3]

        S[0], S[1], S[2], S[3] = S[1], S[2], S[3], fbk

    return S

# function to initialize the TinyJAMBU state array using key and nonce.
def initialize(state, key, nonce):
    state = copy.deepcopy(state)  # To avoid modifying the original state

    # key setup
    state_update(state, key, 1024)

    # nonce setup
    for i in range(3):
        state[1] ^= FRAMEBITS_NONCE
        state_update(state, key, 640)
        nonce_word = struct.unpack("<I", nonce[i * 4: (i + 1) * 4])[0]
        state[3] ^= nonce_word

    return state

# function to process associated data using the TinyJAMBU algorithm.
def process_associated_data(state, key, data):
    state = copy.deepcopy(state)  # To avoid modifying the original state

    part_byte_cnt = len(data) & 3

    b_off = 0
    while b_off < len(data):
        state[1] ^= FRAMEBITS_AD
        state_update(state, key, 640)
        take = min(4, len(data) - b_off)

        word = struct.unpack("<I", data[b_off: b_off + take].rjust(4, b"\x00"))[0]
        state[3] ^= word
        b_off += take

    state[1] ^= part_byte_cnt
    return state

#function to process plaintext using the TinyJAMBU algorithm.
def process_plain_text(state, key, text, ct_len):
    part_byte_cnt = ct_len & 3

    b_off = 0
    cipher = b""
    while b_off < ct_len:
        state[1] ^= FRAMEBITS_CT
        state_update(state, key, 1024)
        take = min(4, ct_len - b_off)

        word = 0
        for i in range(take):
            word |= text[b_off + i] << (i << 3)

        state[3] ^= word
        enc = state[2] ^ word

        # Apply mask to limit 'enc' to a 32-bit unsigned integer
        enc &= 0xFFFFFFFF

        # Handle the case when take < 4
        enc_bytes = struct.pack("<I", enc)
        cipher += enc_bytes[:take]

        b_off += take

    state[1] ^= part_byte_cnt
    return state, cipher


#function to process ciphertext using the TinyJAMBU algorithm.
def process_cipher_text(state, key, cipher, ct_len):
    part_byte_cnt = ct_len & 3

    b_off = 0
    text = b""
    while b_off < ct_len:
        state[1] ^= FRAMEBITS_CT
        state_update(state, key, 1024)
        take = min(4, ct_len - b_off)

        word = 0
        for i in range(take):
            word |= cipher[b_off + i] << (i << 3)

        dec = state[2] ^ word
        mask = 0xFFFFFFFF >> ((4 - take) << 3)
        state[3] ^= (dec & mask)

        for i in range(take):
            text += bytes([dec & 0xFF])
            dec >>= 8

        b_off += take

    state[1] ^= part_byte_cnt
    return state, text


#function to finalize the TinyJAMBU algorithm, generating the authentication tag.
def finalize(state, key, tag=None):
    state = copy.deepcopy(state)  # To avoid modifying the original state

    state[1] ^= FRAMEBITS_TAG
    state_update(state, key, 1024)

    # Apply the mask to ensure state[2] is represented as a 32-bit unsigned integer
    tag = bytearray(8) if tag is None else tag
    tag[:4] = struct.pack("<I", state[2] & 0xFFFFFFFF)

    state[1] ^= FRAMEBITS_TAG
    state_update(state, key, 640)

    # Apply the mask to ensure state[2] is represented as a 32-bit unsigned integer
    tag[4:] = struct.pack("<I", state[2] & 0xFFFFFFFF)

    return tag


