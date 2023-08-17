import paho.mqtt.client as mqtt
import json
import time
import Adafruit_DHT

#main function to extract sensor data from the dh11 sensor and send it to appropriate MQTT topic 
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully!")
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")

#function to handle message publication 
def on_publish(client, userdata, mid):
    print(f"Published message with MID: {mid}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"Unexpected disconnection. Trying to reconnect...")
        client.reconnect()

def extract_and_publish_sensor_data():  

    broker_address = "localhost"  #the address here is localhost since the broker is hosted in the raspberry
    broker_port = 1883  
    topic = "datatopic"  # topic to publish the data

    client = mqtt.Client()
    client.tls_set('/home/hadak/Desktop/thesis/TinyJAMBU-authentication-digital-twin-and-iot-devices/server.crt')
    

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