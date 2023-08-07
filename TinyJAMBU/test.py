import unittest
import utility
import tinyjambu as tinyjambu

class TestTinyJambu(unittest.TestCase):
    def test_tag_mismatch(self):
        # Generate random key, nonce, data, and text
        key = utility.random_data(16)
        nonce = utility.random_data(12)
        data = utility.random_data(16)
        text = utility.random_data(20)

        # Encrypt the text
        cipher, tag = tinyjambu.encrypt(key, nonce, data, text)

        # Modify a single byte in the tag to make it incorrect
        modified_tag = bytearray(tag)
        modified_tag[0] ^= 0x01  # Flip a bit in the first byte

        # Decrypt with the modified tag
        decrypted_text, is_verified = tinyjambu.decrypt(key, nonce, modified_tag, data, cipher)

        # Verify that the decryption failed
        
        self.assertEqual(decrypted_text, b'\x00' * len(text))  # Decrypted text should be all zeros


if __name__ == "__main__":
    unittest.main()
