import os
import json
import utility as utility 
import tinyjambu as tinyjambu
import time
from base64 import b64encode
import requests
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully!")
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")

def on_publish(client, userdata, mid):
    print(f"Published message with MID: {mid}")

#function to create the data connection source to update the device state with appropriate sensor data 
def create_connection():
    base_url = 'http://localhost:8080/devops/piggyback/connectivity?timeout=10'
    username = 'devops'
    password = 'foobar'

    # Load the JSON data from the file
    with open('data_source.json', 'r') as file:
        payload = json.load(file)

    try:
        response = requests.post(base_url, json=payload, auth=(username, password))
        response.raise_for_status()
        print("Connection created successfully!")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print("Error creating the connection:", e)

#update the 'state' attribute the value of "true"
def update_attribute(attribute_name, data):
    base_url = 'http://localhost:8080'
    username = 'ditto'
    password = 'ditto'
    thing_id = "sensors:authenticated"
    url = f"{base_url}/api/2/things/{thing_id}/attributes/{attribute_name}"

    # Convert data to a string ("true" or "false")
    data_str = "true" if data else "false"

    try:
        auth_header = {
            'Authorization': 'Basic ' + b64encode(f"{username}:{password}".encode()).decode()
        }

        response = requests.put(url, data_str, headers=auth_header)
        response.raise_for_status()
        print(f"Successfully updated attribute '{attribute_name}' to '{data_str}'")
    except requests.exceptions.RequestException as e:
        print(f"Error updating attribute '{attribute_name}': {e}")


def wait_for_files():
    downloads_directory = os.path.expanduser("~/Downloads")

    # Check if both "cipher.txt" and "tag.txt" are present in the "Downloads" directory
    while not (os.path.isfile(os.path.join(downloads_directory, "cipher.txt")) and
               os.path.isfile(os.path.join(downloads_directory, "tag.txt")) and 
               os.path.isfile(os.path.join(downloads_directory, "key.txt")) and 
               os.path.isfile(os.path.join(downloads_directory, "thingID.txt")) and 
               os.path.isfile(os.path.join(downloads_directory, "nonce.txt"))):
        time.sleep(1)

def wait_for_enter():
    input("Press Enter to continue...")

def main():
    print("Waiting for 'cipher.txt' and 'tag.txt' , 'key.txt' , 'nonce.txt' , 'thingID.txt' in the 'Downloads' directory...")
    wait_for_files()

    downloads_directory = os.path.expanduser("~/Downloads")

    # Read the content of 'cipher.txt' and 'tag.txt' as strings
    cipher_file_path = os.path.join(downloads_directory, "cipher.txt")
    tag_file_path = os.path.join(downloads_directory, "tag.txt")
    thingID_file_path = os.path.join(downloads_directory, "thingID.txt")
    nonce_file_path = os.path.join(downloads_directory, "nonce.txt")
    key_file_path = os.path.join(downloads_directory, "key.txt")
    mqtt_broker = "192.168.0.174"

    try:
        with open(cipher_file_path, "r") as cipher_file:
            cipher_str = cipher_file.read().strip()
        with open(tag_file_path, "r") as tag_file:
            tag_str = tag_file.read().strip()
        with open(nonce_file_path, "r") as nonce_file:
            nonce_str = nonce_file.read().strip()
        with open(key_file_path, "r") as key_file:
            key_str = key_file.read().strip()
        with open(thingID_file_path, "r") as thingID_file:
            thingID_str = thingID_file.read().strip()
    except FileNotFoundError:
        print(f"Error: File not found. Make sure all '{thingID_file_path}', '{nonce_file_path}' '{cipher_file_path}' and '{tag_file_path}' are present.")
        return
    except Exception as e:
        print(f"Error occurred while reading the files: {e}")
        return
    
    ##delete the files once data is extracted
    os.remove(cipher_file_path)
    os.remove(tag_file_path)
    os.remove(nonce_file_path)
    os.remove(key_file_path)
    os.remove(thingID_file_path)

   

    cipherinbytes = bytes.fromhex(cipher_str)

    tagbytes = bytes.fromhex(tag_str)
    # Convert the tag to a bytearray
    tag_bytearray = bytearray(tagbytes)

    # Display the values of the extracted cipher and tag
    print("Extracted key:", key_str)
    print("Extracted nonce:", nonce_str)
    print("Extracted Cipher:", cipher_str)
    print("Extracted Tag:", tag_str)
    print("Extracted thingID:", thingID_str)

    # Key (replace with your actual key)
    #key_bytes1 = bytes.fromhex('7a0479bb7df60189876d2074137edb12')
    nonce_bytes = bytes.fromhex(nonce_str)
    key_bytes = bytes.fromhex(key_str)
    
    
    wait_for_enter()

    # Perform decryption using TinyJambu implementation
    try:
        print("Parameters of decrypt:")
        print("Key:", key_bytes)
        print("Nonce:", nonce_bytes)
        print("Tag:", tag_bytearray)
        print("Associated Data:", b"")
        print("Cipher:", cipherinbytes)
        decrypted_result, is_verified = tinyjambu.decrypt(key_bytes, nonce_bytes, tag_bytearray, b"", cipherinbytes)
    except Exception as e:
        print(f"Error occurred during decryption: {e}")
        return
    print("Decryption finished, results are ready. Writing result to a file")
    print("DECRIPTED CIPHER:", decrypted_result)
    wait_for_enter()

    # Check if decryption and tag verification are successful and if the decrypted cipher matches thingID
    is_authentication_successful = is_verified and decrypted_result.decode("utf-8") == thingID_str

    # Write the authentication result to "auth_result.txt"
    if is_authentication_successful:
        print("Authentication is successful.")
        decrypted_text = decrypted_result.decode("utf-8")
        print("Computed Decrypted Text:", decrypted_text)
        update_attribute("state", is_authentication_successful)
        create_connection()
        client = mqtt.Client()
        
        client.on_connect = on_connect
        client.on_publish = on_publish

        # Connect to the MQTT broker
        print(f"Connecting to MQTT broker \"{mqtt_broker}\"...")
        client.connect(mqtt_broker, 1883)

        # Prepare the auth_result message
        auth_result_message = {"auth_result": "true"}
        auth_result_message_json = json.dumps(auth_result_message)

        # Publish the auth_result message to the specified topic
        print("Publishing authentication result: true")
        client.publish("dtAuthData/sensors:authenticated", auth_result_message_json)

        # Disconnect from the MQTT broker
        client.disconnect()
        print("Disconnected from MQTT broker.")

    else:
        print("Authentication is not successful.")
        # Create the MQTT client and set up the callbacks
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_publish = on_publish

        # Connect to the MQTT broker
        print(f"Connecting to MQTT broker \"{mqtt_broker}\"...")
        client.connect(mqtt_broker, 1883)

        # Prepare the auth_result message
        auth_result_message = {"auth_result": "false"}
        auth_result_message_json = json.dumps(auth_result_message)

        # Publish the auth_result message to the specified topic
        print("Publishing authentication result: false")
        client.publish("dtAuthData/sensors:authenticated", auth_result_message_json)

        # Disconnect from the MQTT broker
        client.disconnect()
        print("Disconnected from MQTT broker.")

    
if __name__ == "__main__":
    main()
