
class App {
    constructor(baseUrl = 'http://localhost:8080', username = 'ditto', password = 'ditto') {
        this.baseUrl = baseUrl;
        this.username = username;
        this.password = password;
        this.thingId = "sensors:dh11";
        this.useSSE = false;
        this.refreshIntervalMsecs = 100;
        this.intervalId = null;
        this.eventSource = null;
        this.eventListener = (e) => { this.handleMessage(e); };
    }


    sendMessageToThing(thingId, messageSubject, messagePayload, timeout = 0, successCallback, errorCallback) {
        const url = `${this.baseUrl}/api/2/things/${thingId}/inbox/messages/${encodeURIComponent(messageSubject)}?timeout=${timeout}`;
        const authHeader = `Basic ${btoa(`${this.username}:${this.password}`)}`;

        // Construct the JSON payload with the desired format
        const jsonPayload = {
            "message body": messagePayload
        };

        $.ajax({
            url: url,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Set the Content-Type to application/json for JSON payload
                Authorization: authHeader,
            },
            data: JSON.stringify(jsonPayload), // Convert the JSON object to a JSON string
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

    onRefresh() {
        this.requestGetFeature(
            'measurements',
            (data, textStatus, jqXHR) => { this.updateTemperatureHumidity(data.properties); },
            (jqXHR, textStatus, errorThrown) => {
                this.enableAutoRefresh(false);
                this.pushLog('danger', `Error retrieving temperature and humidity: ${errorThrown}. Auto refresh stopped, please reload the page.`);
            }
        );
    }



    onSaveChanges() {
        this.enableAutoRefresh(false);
        this.enableEventSource(false);
        this.updateConfig();
        $('#configureModal').modal('hide');
    }
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

            // Call the modified function with the appropriate parameters and callbacks
            this.sendMessageToThing(
                thingId,
                messageSubject,
                messagePayload,
                timeout,
                () => {
                    console.log('Message sent successfully!');
                    // Any additional code you want to execute upon successful message delivery
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





    onEvent(data) {
        if (data && data.thingId === this.thingId && data.features && data.features.measurements) {
            this.updateTemperatureHumidity(data.features.measurements.properties);
        }
    }


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

    requestGetFeature(featureId, success, error) {
        $.getJSON(`${this.baseUrl}/api/2/things/${this.thingId}/features/${featureId}`)
            .done((data, textStatus, jqXHR) => {
                success(data, textStatus, jqXHR);
            })
            .fail((jqXHR, textStatus, errorThrown) => {
                error(jqXHR, textStatus, errorThrown);
            });
    }

    requestSetProperty(featureId, propertyId, data, success, error) {
        $.ajax({
            type: 'PUT',
            url: `${this.baseUrl}/api/2/things/${this.thingId}`,
            data: JSON.stringify({
                features: {
                    [featureId]: {
                        [propertyId]: data
                    }
                }
            }),
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

    updateTemperatureHumidity(properties) {
        if (properties && properties.temperature) {
            $('#temperatureValue').html(`<span>${properties.temperature} °C</span>`);
        }
        if (properties && properties.humidity) {
            $('#humidityValue').html(`<span>${properties.humidity} %</span>`);
        }
    }





    updateDeviceInfo(data, textStatus, jqXHR) {
        $("#deviceInfo").html('');
        for (var k in data) {
            if (data.hasOwnProperty(k)) {
                $("#deviceInfo").append(`<dt>${k}</dt><dd>${data[k]}</dd>`);
            }
        }
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
        $('#deviceIdNewThing').html(this.thingIdNewThing);

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

        this.updateModal();
        this.updateConfig();

        // initial load of attributes and features
        this.requestGetAttributes(
            this.updateDeviceInfo,
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
