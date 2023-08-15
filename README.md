# A TinyJAMBU lightweight Authenticated Encyption Scheme to authenticate IoT Devices and their  Digital Twins in Eclipse Ditto 

This epository is part of my Bachelor Thesis in Computer Science, supervised by Dr. Prof. Elhajj Mohamed at Constuctor University Bremen. 

---

[final web application] (assets/final_webapp.png) 
## Problem statement: 
Based on the detailed study of IoT and Digital Twins technologies presented in my thesis, it is obvious that one of the main challenges facing IoT environment, and more recently Digital Twin based IoT environment, is security. In breif, the main reason behind this is the weak computational and memory power of IoT nodes, the lack of standarization in communication and security protocols and the strong heterogenity of IoT environments. As a result and as showcased in my research, many IoT devices, Digital Twins environments and others are deployed to the consumer while lacking basic security requirements making the data and the system as a whole weak and vulnerable agains attacks and malicious usage. Please refer to my thesis paper for a detailed explanation. Thus, the goal of my project is to provide a novel mechanism that is compatible with constrained environments to ensure authentication of IoT devices and their adjacent digital counterpart. 

## Project description: 
This project aim at porviding a novel authentication scheme to authenticate IoT devices and their Digtial Twins implemented in Eclipse Ditto. The authentication scheme is based on the lightweight Authentication Encryption algorithm that is TinyJAMBU. The algorithm is implemented using Python and the communication is ensured through a Mosquitto MQTT broker, configured properly to use TLS/SSL (for more security), and deployed in the IoT envionment in a Rapberry Pi 3 model A+. A Web Application is also implemented that serves as the UI that present the live state of the sensor using its digital twin, but also serve to manage the digital twin, the incoming and ongoing messages and to showcase the authentication mechanism itself. The web application is a complete web page that uses the Ditto API. More information about Ditto API here.  

>> IMPORTANT NOTE: in the following installation guide I assume that users are familiar with all the abstractions that Eclipse Ditto use in order to represent digital twins, manage authorizations and connections. For a detailed explanation please refer to the official documentation here.    


## Prerequisites:
#### Hardware prerequisite: 
1. Local machine running the digital twin (Ubuntu 20.04 in my case),
2. Raspberry Pi (I used a model 3 A+) connected to the same WIFI as the local machine and accessible via SSH,   
3. A DH11 temperature and humidity sensor connected to appropriate GPIO of the raspberry. 

#### Software prerequisite: 
1. Eclipse Ditto installed in the local machine. 
2. Eclipse Mosquitto broker and clients installed in the Raspberry Pi and the local machine.
3. Python3.x, JDK 8 >= 1.8.0_92, Apache Maven 3.x, a running Docker daemon and Docker Compose installed in the local machine. 
4. Python3.x installed in the Raspberry Pi.
## Directory structure: 
```bash
.
├── TinyJAMBU/        #TinyJAMBU implementation directory
│   ├── TinyJAMBU.py  #Main implementation file, contain both encrypt() and decrypt() fucntions
│   ├── utility.py    #Basic utility functions used by tinyjambu 
│   ├── methods.py    #Main methods used by the tinyJAMBU algorithm, implemented following the official paper documentation. 
│   ├── AuthenticationTwinSide.py   #Main python code that decrypts received cipher and confirms or denies authentication.
│   ├── data_conn_source.json  #Configuration file to create a connection source for state update   
│   └── data_conn_target.json  #Configuration file to create a connection target for state update 
├── Webapp/           #Web application directory 
│   ├── node_modules/ 
│   ├── index.js      #Main web application code
│   ├── index.html    #HTML of the web application 
│   ├── package-lock.json
│   └── package.json
├── TwinConfigFiles/
│   ├── policy.json            #Configuration file to create a policy 
│   ├── thing.json             #Configuration file to create a thing (digital twin) 
│   ├── auth_conn_source.json  #Configuration file to create a connection source for authentication  
│   └── auth_conn_target.json  #Configuration file to create a connection target for authentication  
├── RaspberryFiles/
│   ├── TinyJAMBU/
│   ├── AuthenticationDeviceSide.py   #Python code to retrieve sensor data and publish it to the appropriate MQTT topic
│   └── RetreivePublishSensorData.py   #Python code to generate the cipher and the tag on the device side
└── README.md


```



## Set Up: 
This section will go through the necesarry set up in order to show through an example how to authenticate IoT devices using our developped scheme that is based on TinyJAMBU authentication encryption algorithm: 

1. In the desired directory of your local machine clone this repository using: 
```
~ $ git clone <project-path>
~ $ cd <project-path>
```
2. In the Raspberry Pi: 
    1. Copy the files inside `RaspberryFiles/` directory to the raspberry.
    2. Copy the `TinyJAMBU/` implementation directory to the Raspberry
        * Make sure to install the necessary packages of the implementation
        * Check that the TinyJAMU algorithm is properly working by running `python3 Tinyjambu.py`. When run, the program should generate a random key and nonce, use the algorithm to encrypt and decript an entered message and show the authentication status: 
        [TinyJAMBU test.](assets/tinyjambu_test.jpg)
    3. Assuming python is installed, make sure the necessary packages for the DH11 sensor are installed. The library is called Adafruit library. 
    4. Install Mosquitto MQTT broker and client and verify installation: 
    ```
    sudo apt install -y mosquitto mosquitto-clients
    ```
    5. Modify the configuration file to use TLS/SSL and listen on port 8883:   
        * file generarion 
        * RSA etc
    6. Copy the files  
3. In the local machine: 
    1. Install and set up a local instance of Eclipse Ditto: 
        * Using Docker, docker-compose, and the official github repository. 
        * Make sure a running instance of ditto is running by visiting: http://localhost 
        > For a full installation guide of Eclipse Ditto refer to this [link!](https://github.com/eclipse-ditto/ditto/tree/master/deployment). 

    2. Install and set up Mosquitto MQTT broker in the local machine.
    3. Using the files in `TwinCinfigFiles/`, create a Policy, a Thing, and two Connections that will serve for authentication: 
    ```
    curl -X PUT 'http://localhost:8080/api/2/policies/thesis:policy' -u 'ditto:ditto' -H 'Content-Type: application/json' -d policy.json
    ```
    ```
    curl -X PUT 'http://localhost:8080/api/2/things/sensors:authenticated' -u 'ditto:ditto' -H 'Content-Type: application/json' -d thing.json
    ```
    ```
    curl -X PUT 'http://localhost:8080/devops/piggyback/connectivity?timeout=10000' -u 'devops:foobar' -H 'Content-Type: application/json' -d auth_conn_source.json
    ```
    ```
    curl -X PUT 'http://localhost:8080/devops/piggyback/connectivity?timeout=10000' -u 'devops:foobar' -H 'Content-Type: application/json' -d auth_conn_target.json
    ```

    > The current configuration files will create a policy for the user `ditto` that has read and write permissions to all things and messages under this policy, a digital twin with ThingID `sensors:authenticated`, a connection source and a connection target exclusive for the authentication exchange. Make sure you provide the generated keys in step 2.4. in order to ensure TLS/SSL communication with the broker. The generated keys and certificates must be copied to the Connections configuration files `auth_conn_source.json` and `auth_conn_target.json` in the appropriate fields before creating the connections.

4. The WebUI: 
    1. Navigate to the `Webapp/` directory and fetch the necessary dependencies using:  
    ```
    npm install 
    ```
    2. After installing the dependencies, simply open the file `index.js` in a web browser 
    > The WebUI must show the attributes of the earlier created digital twin, without the ability to display temperature and humidity values since the authentication is not completed and the digital twin is not yet being updated with sensor data. 

### Authentication mechanism: 
Below I will descibe how the authentication is ensured using the developed scheme via an example authetication of our DH11 sensor and the Digital Twin before exchanging the data : 
1. In a terminal of the Raspberry Pi, run the `AuthenticationDeviceSide.py` file. The scipt will listen on an MQTT topic for a Key and a Nonce necessary for the encryption to be sent from the digital twin. 
```
python3 authentication-device-side.py
```
[first run of the device script] (assets/device_script_first_run.png)
2. Using the WebUI, generate and send a pair of Key and Nonce and send it to the sensor device (python script) through MQTT. 
3. The scipt in the raspberry will receive the key and nonce, and will use the implemented tinyjambu algorithm to encrypt an authentication message and thus generate a Cipher and a Tag. The scipt will then send the Cipher and the Tag back to the Digital Twin (Using MQTT) to check the authentication and wait for a response.
>It is important to note that the authentication message must match the thingID created in Eclipse Ditto, otherwise even if the tag is matching, the authentication will fail. 
[second screenshot of the device script] (assets/device_script_main_run.png)

4. In a terminal in the local machine, open the `TinyJAMBU/` directory and run `AuthenticationTwinSide.py`. The script will wait for necessary data to check the authentication.
```
cd TinyJAMBU
python3 authentication-twin-side.py
``` 
5. Once the Digital Twin receives the Cipher and Nonce, the WebUI automatically prompt the user  to download necessary files for authentication. 
[download prompt](assets/download_prompt.png)
6. Upon download, the script use the tinyJAMBU implementation to decrypt the cipher and check authentication. Authentication is confirmed only if two conditions hold: the tags are matching, the decrypted authentication cipher matches the ThingID declared earlier. 
7. Upon successful authentication, the script first modifies the `state` attribute to the value "true" meaning that the device is authenticated, then it creates two new MQTT connections that will be used to update twin state direcly from the sensor device and to receive live messages from the twin. The script will also send a confirmation message back to the sensor using the authentication target connection. 
> Upon succesful authentication, `AuthenticationTwinSide.py` script, the Ditto Connections and the Thing Attributes will look like this: 
[Twin script](assets/twin_script.png)
[attributes from ditto ui] (assets/attributes_ui.png)
[connections from ditto ui] (assets/connections_ui.png)


8. Upon reception of a success message, the `AuthenticationDeviceSide.py` script in the raspberry will use the `RetreivePublishSensorData.py` script to continuously gather sensor data and publish it to the appropriate MQTT topic. Thus, the state of the Twin will be updated as new data messages are published to the topic. 
[final device scipt](assets/device_script_final_run.png)

9. Back in the WebUI, upon successful authentication, the Thing attributes are successfully updated (`state`) and the temperature and humidity values are being updated in the UI as the twin state is also being updated. 
[web page 1](assets/attributes_authenticated.png)
[web page 1](assets/features_authenticated.png)

10. An authenticated sensor can only run the `RetreivePublishSensorData.py` sensor to update the DT with sensor values. If a user wantd to remove a device from the authenticated devices and wish to require a new authentication, a button is present in the  Web Application that deletes the data connection, remove "auth_cipher" and "auth_tag" Attributes from the DT and update the "state" attribute to "false" to come back to the initial set up. 

### Security considerations: 
Please refer to my thesis paper for a detailed security analysis of the developed scheme. 



