import paho.mqtt.client as mqtt
import utility as utility
import tinyjambu as tinyjambu
import json
import time
import Adafruit_DHT

#mqtt address
mqtt_broker = "localhost"
#mqtt topic for receiving key and nonce and receiving authentication result
mqtt_topic_auth = "dtAuthData/sensors:authenticated"
#mqtt topic to send generated cipher and tag from the device to the twin 
mqtt_topic_data = "deviceAuthData"
received_key = None
auth_confirmation_received = False
auth_result = None

# Function to wait for user input
def wait_for_enter():
    input("Press Enter to continue...")

# Callback when a key is received
def receive_key(client, userdata, msg):
    global received_key
    if msg.topic == mqtt_topic_auth:
        try:
            data = json.loads(msg.payload)
            psk = data["value"]["message body"]["psk"]
            received_key = psk
            print("Key extracted:", received_key)
        except json.JSONDecodeError:
            print("Error: Failed to parse the received data as JSON.")
        except KeyError:
            print("Error: 'psk' key not found in the received data.")
        finally:
            wait_for_enter()

# Callback when authentication data is received
def receive_authdata(client, userdata, msg):
    global received_key, received_nonce
    if msg.topic == mqtt_topic_auth:
        try:
            data = json.loads(msg.payload)
            if "value" in data and "message body" in data["value"] and "psk" in data["value"]["message body"]:
                psk = data["value"]["message body"]["psk"]["psk"]
                nonce = data["value"]["message body"]["nonce"]["nonce"]
                received_key = psk
                received_nonce = nonce
                print("Key extracted:", received_key)
                print("Nonce extracted:", received_nonce)
            else:
                print("Error: 'value', 'message body', or 'psk' key not found in the received data.")
        except json.JSONDecodeError:
            print("Error: Failed to parse the received data as JSON.")
        except KeyError:
            print("Error: 'psk' or 'nonce' key not found in the received data.")
        finally:
            wait_for_enter()

# Callback when MQTT client connects          
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully!")
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")

#function to handle message publication 
def on_publish(client, userdata, mid):
    print(f"Published message with MID: {mid}")

#function to handle broker disconnection 
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"Unexpected disconnection. Trying to reconnect...")
        client.reconnect()


#main function to extract sensor data from the dh11 sensor and send it to appropriate MQTT topic 
def extract_sensor_data():  

    broker_address = "localhost"  #the address here is localhost since the broker is hosted in the raspberry
    broker_port = 1883  
    topic = "datatopic"  # topic to publish the data

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish

    client.connect(broker_address, broker_port, 60)
    client.loop_start()

    sensor = Adafruit_DHT.DHT11
    pin = 4  

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
        if humidity is not None and temperature is not None:
            payload = {
                "temperature": int(temperature),
                "humidity": int(humidity),
                "thingId": "sensors:authenticated"
            }
            json_payload = json.dumps(payload)
            client.publish(topic, json_payload)
        else:
            print("Failed to retrieve data from the sensor.")
        time.sleep(10)  # Wait for 10 seconds before taking the next reading

    client.loop_stop()
    client.disconnect()

def receive_auth_confirmation(client, userdata, msg):
    global auth_confirmation_received, auth_result

    if msg.topic == mqtt_topic_auth:
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            auth_result = data["auth_result"]
            auth_confirmation_received = True

            if auth_result == "false":
                print("Authentication failed.")
                exit(1)
            elif auth_result == "true":
                print("Authentication successful. Proceeding to sensor data extraction.")
                extract_sensor_data()
            else:
                print("Unknown authentication result:", auth_result)
        except json.JSONDecodeError:
            print("Error: Failed to parse the received data as JSON.")
        except KeyError:
            print("Error: 'auth_result' key not found in the received data.")

def main():
    global received_key, received_nonce
    received_key = None
    received_nonce = None

    print("Welcome to the TinyJambu Encryption and Authentication Example")
    wait_for_enter()

    # Create the MQTT client and set up the callbacks
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = receive_authdata
    client.on_disconnect = on_disconnect

    # Connect to the MQTT broker and subscribe to the topic
    print(f"Connecting to MQTT broker \"{mqtt_broker}\"...")
    client.connect(mqtt_broker, 1883)
    print(f"Subscribing and listening the topic \"{mqtt_topic_auth}\" for the shared key and nonce...")
    client.subscribe(mqtt_topic_auth)

    # Start the MQTT loop in the background
    client.loop_start()

    # Wait until the key and nonce are received
    while received_key is None or received_nonce is None:
        pass

    print("Key and Nonce extracted, authentication ready to initiate")

    # Generate a random nonce
    #nonce = bytes.fromhex('788fbb6ea5563ceb46db8abd')


    #print("Random nonce generated:")

    # Define the data (empty in this case)
    data = b""

    # Get the authentication message from the user
    auth_message = input("Enter an authentication message: ")

    # Convert the authentication message to bytes
    text = auth_message.encode('utf-8')

    # Convert the received key to bytes
    try:
        key = bytes.fromhex(received_key)
        nonce = bytes.fromhex(received_nonce)
    except ValueError:
        print("Error: Failed to convert the received key or nonce to bytes.")
        return

    # Encrypt the message using TinyJambu
    cipher, tag = tinyjambu.encrypt(key, nonce, data, text)

    print("Generating tag and cipher...")


    # Print the generated cipher and tag
    print("Encrypted cipher:", utility.to_hex(cipher))
    print("Authentication tag:", utility.to_hex(tag))

    # Stop the MQTT loop before disconnecting
    client.loop_stop()

    # Disconnect from the MQTT broker and then connect again to publish the payload
    client.disconnect()
    print("Disconnected from MQTT broker.")
    print(f"Reconnecting to MQTT broker \"{mqtt_broker}\" to publish device authentication data")
    wait_for_enter()
    client.connect(mqtt_broker, 1883)

    # Publish the encrypted cipher and tag to "deviceAuthData" topic
    payload = {
        "auth_cipher": utility.to_hex(cipher),
        "auth_tag": utility.to_hex(tag),
        "thingId": "sensors:authenticated"
    }

    client.publish(mqtt_topic_data, json.dumps(payload))
    print("Encrypted cipher and tag published to topic:", mqtt_topic_data)

    # Re-start the MQTT loop
    client.loop_start()

    print(f"Subscribing to MQTT topic \"{mqtt_topic_auth}\" for authentication confirmation...")
    client.subscribe(mqtt_topic_auth)
    client.message_callback_add(mqtt_topic_auth, receive_auth_confirmation)

    # Wait for authentication confirmation
    while not auth_confirmation_received:
        pass

    if auth_result == "false":
        print("Authentication failed.")
        exit(1)
    elif auth_result == "true":
        print("Authentication successful. Proceeding to sensor data extraction.")
        wait_for_enter()
        #extract and publish sensor data
        extract_sensor_data()

if __name__ == "__main__":
    main()

