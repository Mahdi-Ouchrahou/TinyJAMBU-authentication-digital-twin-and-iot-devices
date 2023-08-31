import os
import json
import utility as utility 
import tinyjambu as tinyjambu
import time
from base64 import b64encode
import requests
import paho.mqtt.client as mqtt
import psutil


execution_times = {}

def measure_execution_time(func):
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())  # Get the current process

        # Measure CPU usage before the function call
        start_cpu_percent = process.cpu_percent(interval=None)

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time

        # Measure CPU usage after the function call
        end_cpu_percent = process.cpu_percent(interval=None)

        # Calculate average CPU usage during the function call
        avg_cpu_percent = (start_cpu_percent + end_cpu_percent) / 2

        execution_times[func.__name__] = {
            "execution_time": execution_time,
            "cpu_usage": avg_cpu_percent
        }

        # Write execution time and CPU usage to the log file
        with open("execution_times.log", "a") as log_file:
            log_file.write(f"{func.__name__}: "
                           f"Execution Time: {execution_time:.6f} seconds, "
                           f"CPU Usage: {avg_cpu_percent:.2f}%\n")

        print(f"{func.__name__} execution time: {execution_time:.6f} seconds")
        print(f"{func.__name__} CPU usage: {avg_cpu_percent:.2f}%")
        return result
    return wrapper



@measure_execution_time
def decrypt_and_verify(key, nonce, tag, cipher):
    decrypted_result, is_verified = tinyjambu.decrypt_192(key, nonce, tag, b"", cipher)
    return decrypted_result, is_verified

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully!")
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")

def on_publish(client, userdata, mid):
    print(f"Published message with MID: {mid}")

@measure_execution_time
def publish_authentication_result(client, message):
    client.publish("dtAuthData/sensors:authenticated", message)


#function to create the data connection source to update the device state with appropriate sensor data 
@measure_execution_time
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
@measure_execution_time
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
        decrypted_result, is_verified = decrypt_and_verify(key_bytes, nonce_bytes, tag_bytearray, cipherinbytes)
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
        client.tls_set('/home/hadak/Desktop/thesis/TinyJAMBU-authentication-digital-twin-and-iot-devices/TLS/ca.crt')
        client.on_connect = on_connect
        client.on_publish = on_publish

        # Connect to the MQTT broker
        print(f"Connecting to MQTT broker \"{mqtt_broker}\"...")
        client.connect(mqtt_broker, 8883)

        # Prepare the auth_result message
        auth_result_message = {"auth_result": "true"}
        auth_result_message_json = json.dumps(auth_result_message)

        # Publish the auth_result message to the specified topic
        print("Publishing authentication result: true")
        publish_authentication_result(client, auth_result_message_json)


        # Disconnect from the MQTT broker
        client.disconnect()
        print("Disconnected from MQTT broker.")

    else:
        print("Authentication is not successful.")
        # Create the MQTT client and set up the callbacks
        client = mqtt.Client()
        client.tls_set('/home/hadak/Desktop/thesis/TinyJAMBU-authentication-digital-twin-and-iot-devices/TLS/ca.crt')

        client.on_connect = on_connect
        client.on_publish = on_publish

        # Connect to the MQTT broker
        print(f"Connecting to MQTT broker \"{mqtt_broker}\"...")
        client.connect(mqtt_broker, 8883)

        # Prepare the auth_result message
        auth_result_message = {"auth_result": "false"}
        auth_result_message_json = json.dumps(auth_result_message)

        # Publish the auth_result message to the specified topic
        print("Publishing authentication result: false")
        publish_authentication_result(client, auth_result_message_json)

        # Disconnect from the MQTT broker
        client.disconnect()
        print("Disconnected from MQTT broker.")
    
    with open("execution_times.json", "w") as json_file:
        json.dump(execution_times, json_file)

    
if __name__ == "__main__":
    main()
