
class App {
    constructor(baseUrl = 'http://localhost:8080', username = 'ditto', password = 'ditto') {
        this.baseUrl = baseUrl;
        this.username = username;
        this.password = password;
        this.thingId = "sensors:authenticated";
        this.useSSE = false;
        this.refreshIntervalMsecs = 100;
        this.intervalId = null;
        this.eventSource = null;
        this.eventListener = (e) => { this.handleMessage(e); };
        this.filesDownloaded = false;
        this.postRequestMade = false;
        this.deviceData = {
        };

    }

    generateRandomBytes(length) {
        const array = new Uint8Array(length);
        window.crypto.getRandomValues(array);
        return array;
    }
    //function used to make the post request to send messages to the digital twin
    sendMessageToThing(thingId, messageSubject, messagePayload, timeout = 0, successCallback, errorCallback) {
        const url = `${this.baseUrl}/api/2/things/${thingId}/inbox/messages/${encodeURIComponent(messageSubject)}?timeout=${timeout}`;
        const authHeader = `Basic ${btoa(`${this.username}:${this.password}`)}`;
        const jsonPayload = {
            "message body": messagePayload
        };

        $.ajax({
            url: url,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: authHeader,
            },
            data: JSON.stringify(jsonPayload),
            success: () => {
                this.pushLog('success', `Message sent successfully`);
                if (typeof successCallback === 'function') {
                    successCallback();
                }
            },
            error: (jqXHR, textStatus, errorThrown) => {
                this.pushLog('danger', `Error sending message: ${errorThrown}`);
                if (typeof errorCallback === 'function') {
                    errorCallback(jqXHR, textStatus, errorThrown);
                }
            },
        });
    }




    onConfigure() {
        this.updateModal();
    }


    //this function is called when the button to delete a connection is clicked, it makes the appropriate post request to delete the data connection 
    async deleteconnection() {
        const postUrl = 'http://localhost:8080/devops/piggyback/connectivity?timeout=10';
        const postUsername = 'devops';
        const postPassword = 'foobar';

        const postPayload = {
            "targetActorSelection": "/system/sharding/connection",
            "headers": {
                "aggregate": false
            },
            "piggybackCommand": {
                "type": "connectivity.commands:deleteConnection",
                "connectionId": "data-connection-source"
            }
        };

        try {
            const response = await fetch(postUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Basic ' + btoa(`${postUsername}:${postPassword}`)
                },
                body: JSON.stringify(postPayload)
            });

            if (!response.ok) {
                throw new Error('Network POST response was not ok');
            }

            console.log('POST request successful!');
            return response.json();
        } catch (error) {
            console.error('Error making the POST request:', error);
            this.pushLog('danger', 'Error making the POST request: ' + error.message);
        }
    }


    onRefresh() {
        // Fetch the "state" attribute before proceeding with the feature request
        this.requestGetAttributes(
            (data, textStatus, jqXHR) => {
                this.deviceData = data;
                console.log("Up to date Device attributes:", this.deviceData);

                // Check if the "state" attribute is set to true 
                if (data && data.state && data.state === true) {

                    this.enableAutoRefresh(true);

                    // If the "state" attribute is true, proceed with the feature request
                    this.requestGetFeature(
                        'measurements',
                        (data, textStatus, jqXHR) => {
                            console.log('Successfully retrieved measurements feature:', data);
                            this.updateTemperatureHumidity(data.properties);
                            console.log('Temperature and humidity data updated in the console.');
                        },
                        (jqXHR, textStatus, errorThrown) => {
                            console.error(`Error retrieving temperature and humidity: ${errorThrown}`);
                            console.log('Error details:', jqXHR.responseText);
                            this.enableAutoRefresh(false);
                        }
                    );
                    //display appropriate messages when the authentication is true 
                    $("#stateTrueMessage").show();
                    $("#sensorReadyMessage").show();
                    $("#deleteconnection").show();

                } else {


                    // If the "state" attribute is not set to true, display a message or take appropriate action
                    console.warn('The "state" attribute is not set to true. Auto refresh is disabled.');
                    this.enableAutoRefresh(false);

                }

                this.requestGetAttributes(
                    (data, textStatus, jqXHR) => {

                        // Check if the cipher and tag are received for the first time
                        if (data.auth_cipher && data.auth_tag && !this.filesDownloaded) {

                            // Trigger download and set the filesDownloaded flag to true
                            this.downloadFiles(data.auth_cipher, data.auth_tag, data.psk.psk, data.nonce.nonce, this.thingId);
                            this.filesDownloaded = true;
                        }
                    },
                    () => { },
                    (jqXHR, textStatus, errorThrown) => {
                        this.pushLog('danger', `Error retrieving device info: ${errorThrown}`);
                        console.error(`Error retrieving device info: ${errorThrown}`);
                    }
                );
            },
            () => { },
            (jqXHR, textStatus, errorThrown) => {
                this.pushLog('danger', `Error retrieving device info: ${errorThrown}`);
                console.error(`Error retrieving device info: ${errorThrown}`);
            }
        );
    }

    //function to display download interface and button 
    downloadFiles(cipher, tag, key, nonce, thingID) {
        // Function to show the message box with the button for download
        const messageBoxContainer = document.getElementById("messageBoxContainer");
        messageBoxContainer.style.display = "block";

        const downloadButton = document.getElementById("DownloadButton");
        downloadButton.onclick = () => {
            // If the user clicks the button, initiate the download
            this.triggerDownload(cipher, "cipher.txt");
            this.triggerDownload(tag, "tag.txt");
            this.triggerDownload(key, "key.txt");
            this.triggerDownload(nonce, "nonce.txt");
            this.triggerDownload(thingID, "thingID.txt");

            // Hide the message box after the download is triggered
            messageBoxContainer.style.display = "none";
        };
    }

    //function to dowanload files from the browser 
    triggerDownload(content, fileName) {
        // Create a Blob from the content
        const blob = new Blob([content], { type: "text/plain;charset=utf-8" });

        // Create an anchor element to initiate the download
        const anchor = document.createElement("a");
        anchor.href = URL.createObjectURL(blob);
        anchor.download = `${fileName}`;

        // Append the anchor to the document and click it to trigger the download
        document.body.appendChild(anchor);
        anchor.click();

        // Remove the anchor from the document after the download
        document.body.removeChild(anchor);
    }


    onSaveChanges() {
        this.enableAutoRefresh(false);
        this.enableEventSource(false);
        this.updateConfig();
        $('#configureModal').modal('hide');
    }

    // function that is called once the button to send a message is clicked
    onSendMessage() {
        const message = $('#messageToSensor').val();
        if (message) {
            const thingId = this.thingId;
            const messageSubject = 'subject'; // Replace 'subject' with your desired message subject
            const timeout = 0;

            // Construct the JSON payload with the desired format
            const messagePayload = {
                "content of message body": message
            };

            // Call the function to send a message using the API with the appropriate parameters and callbacks
            this.sendMessageToThing(
                thingId,
                messageSubject,
                messagePayload,
                timeout,
                () => {
                    console.log('Message sent successfully!');
                },
                (jqXHR, textStatus, errorThrown) => {
                    console.error('Error sending message:', errorThrown);
                    // Any additional error handling code you want to execute
                }
            );

            $('#sendMessageModal').modal('hide');
        } else {
            alert('Please enter a message to send.');
        }
    }

    //this function is trigerred when the send PSK and Nonce butto is clicked 
    sendAllAttributesToThing() {
        if (this.deviceData && this.deviceData.psk && this.deviceData.nonce) {
            const thingId = this.thingId;
            const messageSubject = 'authenticationPSK'; // Replace 'attributes' with your desired message subject
            const timeout = 0;
            const messagePayload = {
                psk: this.deviceData.psk,
                nonce: this.deviceData.nonce
            };

            // Send PSK and nonce
            this.sendMessageToThing(
                thingId,
                messageSubject,
                messagePayload,
                timeout,
                () => {
                    console.log('PSK sent successfully!');
                },
                (jqXHR, textStatus, errorThrown) => {
                    console.error('Error sending PSK:', errorThrown);
                    this.pushLog('danger', 'Error sending PSK: ' + errorThrown);
                }
            );



        } else {
            this.pushLog('danger', 'PSK or nonce attribute is missing. Unable to send the message.');
        }
    }

    //
    sendauthstatus() {
        if (this.deviceData && this.deviceData.state) {
            const thingId = this.thingId;
            const messageSubject = 'authenticationstatus'; // Replace 'attributes' with your desired message subject
            const timeout = 0;

            const messagePayload = {
                "state": {
                    "auth_result": "true"
                }

            };


            // Construct the JSON payload with only the PSK attribute


            // Call the modified function with the appropriate parameters and callbacks
            this.sendMessageToThing(
                thingId,
                messageSubject,
                messagePayload,
                timeout,
                () => {
                    // Success callback
                    console.log('Authentication status sent successfully!');
                    // Any additional code you want to execute upon successful message delivery
                },
                (jqXHR, textStatus, errorThrown) => {
                    // Error callback
                    console.error('Error sending Authentication status:', errorThrown);
                    console.log('Authentication status failed!');
                    // Any additional error handling code you want to execute
                    this.pushLog('danger', 'Error sending Authentication status: ' + errorThrown);
                }
            );

        } else {
            this.pushLog('danger', 'Authentication status attribute is missing. Unable to send the message.');
        }
    }





    onEvent(data) {
        if (data && data.thingId === this.thingId && data.features && data.features.measurements) {
            this.updateTemperatureHumidity(data.features.measurements.properties);
        }
    }

    //function using the Ditto API to extract thing attributes 
    requestGetAttributes(success, error) {
        $.getJSON(`${this.baseUrl}/api/2/things/${this.thingId}`, {
            fields: 'attributes'
        })
            .fail((jqXHR, textStatus, errorThrown) => {
                error(jqXHR, textStatus, errorThrown);
            })
            .done((data, textStatus, jqXHR) => {
                success(data.attributes, textStatus, jqXHR);
            });
    }
    //function using the Ditto API to extract thing features
    requestGetFeature(featureId, success, error) {
        $.getJSON(`${this.baseUrl}/api/2/things/${this.thingId}/features/${featureId}`)
            .done((data, textStatus, jqXHR) => {
                success(data, textStatus, jqXHR);
            })
            .fail((jqXHR, textStatus, errorThrown) => {
                console.error(`Error retrieving feature '${featureId}': ${errorThrown}`);
                console.log('Error details:', jqXHR.responseText);
                error(jqXHR, textStatus, errorThrown);
            });
    }

    //function to set the attribute PSK of the thing to a new value using the Ditto API 
    requestSetPSK(data, success, error) {
        const jsonPayload = {
            psk: data
        };
        $.ajax({
            type: 'PUT',
            url: `${this.baseUrl}/api/2/things/${this.thingId}/attributes/psk`,
            data: JSON.stringify(jsonPayload),
            contentType: 'application/json',
            headers: {
                'Authorization': 'Basic ' + btoa(`${this.username}:${this.password}`)
            }
        })
            .fail((jqXHR, textStatus, errorThrown) => {
                error(jqXHR, textStatus, errorThrown);
            })
            .done((data, textStatus, jqXHR) => {
                success(data, textStatus, jqXHR);
            });
    }
    resetstate(sucess, error) {
        const jsonPayload = "false"
        $.ajax({
            type: 'PUT',
            url: `${this.baseUrl}/api/2/things/${this.thingId}/attributes/state`,
            data: JSON.stringify(jsonPayload),
            contentType: 'application/json',
            headers: {
                'Authorization': 'Basic ' + btoa(`${this.username}:${this.password}`)
            }
        })
            .fail((jqXHR, textStatus, errorThrown) => {
                error(jqXHR, textStatus, errorThrown);
            })
            .done((data, textStatus, jqXHR) => {
                success(data, textStatus, jqXHR);
            });
    }
    deleteAtt(attributeName, success, error) {

        $.ajax({
            type: 'DELETE',
            url: `${this.baseUrl}/api/2/things/${this.thingId}/attributes/${attributeName}`,
            contentType: 'application/json',
            headers: {
                'Authorization': 'Basic ' + btoa(`${this.username}:${this.password}`)
            }
        })
            .done((data, textStatus, jqXHR) => {
                success(data, textStatus, jqXHR);
            })
            .fail((jqXHR, textStatus, errorThrown) => {
                error(jqXHR, textStatus, errorThrown);
            });
    }

    //function to set the attribute Nonce of the thing to a new value using the Ditto API 
    requestSetnonce(data, success, error) {
        const jsonPayload = {
            nonce: data
        };
        $.ajax({
            type: 'PUT',
            url: `${this.baseUrl}/api/2/things/${this.thingId}/attributes/nonce`,
            data: JSON.stringify(jsonPayload),
            contentType: 'application/json',
            headers: {
                'Authorization': 'Basic ' + btoa(`${this.username}:${this.password}`)
            }
        })
            .fail((jqXHR, textStatus, errorThrown) => {
                error(jqXHR, textStatus, errorThrown);
            })
            .done((data, textStatus, jqXHR) => {
                success(data, textStatus, jqXHR);
            });
    }




    enableAutoRefresh(enabled = true) {
        if (enabled) {
            this.intervalId = setInterval(() => {
                this.onRefresh();
            }, this.refreshIntervalMsecs);
        } else {
            clearInterval(this.intervalId);
        }
    }

    applyUpdateStrategy() {
        if (this.useSSE) {
            this.enableEventSource();

        } else {
            this.enableAutoRefresh();
        }
    }


    enableEventSource(enabled = true) {
        if (enabled) {
            this.eventSource = new EventSource(`${this.baseUrl}/api/2/things/${this.thingId}`);
            this.eventSource.addEventListener('message', this.eventListener);
        } else if (this.eventSource != null) {
            this.eventSource.removeEventListener('message', this.eventListener);
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    handleMessage(e) {
        if (e.data != null && e.data !== '') {
            var data = JSON.parse(e.data);
            if (data.thingId == this.thingId) {
                this.onEvent(data);
            }
        }
    }
    //function to update the UI with appropriate temperature and humidity values 
    updateTemperatureHumidity(properties) {
        if (properties && properties.temperature) {
            $('#temperatureValue').html(`<span>${properties.temperature} °C</span>`);
        }
        if (properties && properties.humidity) {
            $('#humidityValue').html(`<span>${properties.humidity} %</span>`);
        }
    }

    //function triggered when updating PSK 
    updatePSK() {
        const pskLengthBytes = 16; // 128 bits
        const newPSKValue = this.generateRandomBytes(pskLengthBytes);

        // Convert the binary random bytes to a hexadecimal string
        const newPSKHexString = Array.from(newPSKValue, byte => byte.toString(16).padStart(2, '0')).join('');
        //const testpsk = "7a0479bb7df60189876d2074137edb12";
        this.requestSetPSK(
            newPSKHexString,
            (data, textStatus, jqXHR) => {
                // Success callback
                console.log('PSK updated successfully:', data);

                // Fetch updated attributes and update the device information
                this.requestGetAttributes(
                    (data, textStatus, jqXHR) => {
                        // Update the deviceData object with the retrieved data
                        this.deviceData = data;
                        console.log("Device attributes:", this.deviceData);
                        // Call the updateDeviceInfo method to update the HTML placeholders
                        this.updateDeviceInfo(data, textStatus, jqXHR);

                    },
                    () => { },
                    (jqXHR, textStatus, errorThrown) => {
                        this.pushLog('danger', `Error retrieving device info: ${errorThrown}`);
                    }
                );

                // Display a success message to the user
                this.pushLog('success', 'PSK updated successfully!');


            },
            (jqXHR, textStatus, errorThrown) => {
                // Error callback
                console.error('Error updating PSK:', errorThrown);

                // Display an error message to the user
                this.pushLog('danger', 'Error updating PSK: ' + errorThrown);
            }
        );
    }


    //function triggered when updating Nonce
    updatenonce() {
        const nonceLengthBytes = 12; // 96 bits
        const newNonceValue = this.generateRandomBytes(nonceLengthBytes);
        const newNonceHexString = Array.from(newNonceValue, byte => byte.toString(16).padStart(2, '0')).join('');


        // Call the requestSetnonce method with appropriate callbacks
        this.requestSetnonce(
            newNonceHexString,
            (data, textStatus, jqXHR) => {
                // Success callback
                console.log('Nonce updated successfully:', data);

                // Fetch updated attributes and update the device information
                this.requestGetAttributes(
                    (data, textStatus, jqXHR) => {
                        // Update the deviceData object with the retrieved data
                        this.deviceData = data;
                        console.log("Device attributes:", this.deviceData);

                        // Call the updateDeviceInfo method to update the HTML placeholders
                        this.updateDeviceInfo(data, textStatus, jqXHR);
                    },
                    () => { },
                    (jqXHR, textStatus, errorThrown) => {
                        this.pushLog('danger', `Error retrieving device info: ${errorThrown}`);

                    }
                );

                // Display a success message to the user
                this.pushLog('success', 'Nonce updated successfully!');
            },
            (jqXHR, textStatus, errorThrown) => {
                // Error callback
                console.error('Error updating Nonce:', errorThrown);

                // Display an error message to the user
                this.pushLog('danger', 'Error updating Nonce: ' + errorThrown);
            }
        );
    }


    //function responsible of updating the UI with appropriate device attributes 
    updateDeviceInfo(data, textStatus, jqXHR) {
        const deviceInfoList = $("#deviceInfo"); // Get the <dl> element
        const deviceInfoItems = deviceInfoList.find("dd"); // Get the <dd> elements within the <dl>

        // Define the order of keys to match the HTML placeholders
        const keysOrder = ["type", "serial_number", "psk", "nonce", "state"];

        // Iterate through the keys in the desired order and update the values
        for (let i = 0; i < keysOrder.length; i++) {
            const key = keysOrder[i];
            let value = data[key] || "N/A";

            // Check if the key is "state" and update the value accordingly
            if (key === "state") {
                value = value === true ? "authenticated" : "non-authenticated";
            }

            const element = $("#" + key); // Find the corresponding HTML element by ID
            if (element.length) {
                // Update the text content of the HTML element
                element.text(value);
            }
        }

        console.log("Device Information Updated:", data);

    }

    pushLog(role, message) {
        $("#alerts").append(
            `<div class="alert alert-${role} alert-dismissible fade show" role="alert">
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
                ${message}
             </div>`
        );
    }

    updateConfig() {
        this.baseUrl = $('#dittoUrl').val();
        this.username = $('#dittoUser').val();
        this.password = $('#dittoPassword').val();
        this.thingId = $('#dittoThingId').val();
        this.refreshIntervalMsecs = $('#refreshInterval').val();
        this.useSSE = $("#useSSE").prop('checked');

        $.ajaxSetup({
            headers: {
                Authorization: 'Basic ' + btoa(`${this.username}:${this.password}`),
            },
        });
    }

    updateModal() {
        $('#dittoUrl').val(this.baseUrl);
        $('#dittoUser').val(this.username);
        $('#dittoPassword').val(this.password);
        $('#dittoThingId').val(this.thingId);
        $('#refreshInterval').val(this.refreshIntervalMsecs);
        $("#useSSE").prop('checked', this.useSSE);


    }

    main() {
        $('#saveChanges').click(() => {
            this.onSaveChanges();
        });
        $('#configure').click(() => {
            this.onConfigure();
        });
        $('#sendMessageToSensor').click(() => {
            this.onSendMessage();
        });
        $('#generatePSKButton').click(() => {
            this.updatePSK();
            $('#generatePSKButton').prop('disabled', true); // Disable the button after clicking

        });
        $('#generateNonceButton').click(() => {
            this.updatenonce();
            $('#generateNonceButton').prop('disabled', true);

        });
        $('#sendpsk').click(() => {
            this.sendAllAttributesToThing();
        });
        $('#deleteconnection').click(() => {
            this.deleteconnection();

            this.deleteAtt('auth_cipher',
                (data, textStatus, jqXHR) => {
                    // Attribute deleted successfully
                    console.log('Attribute deleted:', data);
                },
                (jqXHR, textStatus, errorThrown) => {
                    // Error deleting attribute
                    console.error('Error deleting attribute:', errorThrown);
                }
            );
            this.deleteAtt('auth_tag',
                (data, textStatus, jqXHR) => {
                    // Attribute deleted successfully
                    console.log('Attribute deleted:', data);
                },
                (jqXHR, textStatus, errorThrown) => {
                    // Error deleting attribute
                    console.error('Error deleting attribute:', errorThrown);
                }
            );

            this.resetstate(
                (data, textStatus, jqXHR) => {
                    console.log('resetstate successful:', data);
                },
                (jqXHR, textStatus, errorThrown) => {
                    console.error('resetstate error:', errorThrown);
                }
            );
            console.log("post request clicked");
        });

        this.updateModal();
        this.updateConfig();

        // initial load of attributes and features
        this.requestGetAttributes(
            (data, textStatus, jqXHR) => {
                // Update the deviceData object with the retrieved data
                this.deviceData = data;
                console.log("Device attributes:", this.deviceData);

                // Call the updateDeviceInfo method to update the HTML placeholders
                this.updateDeviceInfo(data, textStatus, jqXHR);
            },
            () => { },
            (jqXHR, textStatus, errorThrown) => {
                this.pushLog('danger', `Error retrieving device info: ${errorThrown}`);
            }
        );
        this.onRefresh();


        this.applyUpdateStrategy();
    }
}

isDefined = function (ref) {
    return typeof ref != 'undefined';
};

doIfDefined = function (ref, action) {
    if (isDefined(ref)) {
        action(ref);
    }
};

// Startup
$(document).ready(() => {
    new App().main();

});
