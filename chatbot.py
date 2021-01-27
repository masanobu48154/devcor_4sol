from flask import Flask, request, json
import requests
from messenger import Messenger
import meraki
from pprint import pprint

app = Flask(__name__)
port = 5005

msg = Messenger()

@app.route('/', methods=['GET', 'POST'])
def index():
    """Receive a notification from Webex Teams and handle it"""
    if request.method == 'GET':
        return f'Request received on local port {port}'
    elif request.method == 'POST':
        if 'application/json' in request.headers.get('Content-Type'):
            # Notification payload, received from Webex Teams webhook
            data = request.get_json()

            # Loop prevention, ignore messages which were posted by bot itself.
            # The bot_id attribute is collected from the Webex Teams API
            # at object instatiation.
            if msg.bot_id == data.get('data').get('personId'):
                return 'Message from self ignored'
            else:
                # Print the notification payload, received from the webhook
                print(json.dumps(data,indent=4))

                # Collect the roomId from the notification,
                # so you know where to post the response
                # Set the msg object attribute.
                room_id = data.get('data').get('roomId')
                msg.room_id = room_id

                # Collect the message id from the notification, 
                # so you can fetch the message content
                message_id = data.get('data').get('id')
              
                # Get the contents of the received message. 
                msg.get_message(message_id)

                # If message starts with '/meraki', 
                # make some API calls to the Meraki API server.
                # If not, just post a confirmation that a message was received.
                if msg.message_text.startswith('/meraki'):
                    # Default action is to list SSIDs of a predefined network.
                    try:
                        action = msg.message_text.split()[1]
                    except IndexError:
                        action = 'ssids'

                    # '/meraki networks' fetches all the networks,
                    # belonging to the organization, and prints them in the room
                    if action == 'networks':
                        network_list = meraki.get_networks()

                        msg_reply = f'Networks for organization {meraki.org_id}'
                        for network in network_list:
                            msg_reply += f"\n{network['name']} {network['id']}"

                        msg.post_message(msg.room_id, msg_reply)

                    # '/meraki ssids' fetches SSIDs on the specified network.
                    # If network_id is not provided, use the predefined value.
                    elif action == 'ssids':
                        try:
                            network_id = msg.message_text.split()[2]
                        except IndexError:
                            network_id = meraki.def_network_id

                        ssid_list = meraki.get_ssids(network_id)

                        msg_reply = f'SSIDs for network {network_id}'
                        for ssid in ssid_list:
                            msg_reply += f"\n{ssid['number']} {ssid['name']}\
                                Enabled: {ssid['enabled']}"
                        
                        msg.post_message(msg.room_id, msg_reply)

                    # '/meraki location' prints the last received 
                    # location data of some clients
                    elif action == 'location':
                        try:
                            subaction = msg.message_text.split()[2]
                        except IndexError:
                            subaction = 'startscan'

                        if subaction == 'startscan':
                            msg_reply = meraki.start_scanning()
                        elif subaction == 'get':
                            msg_reply = json.dumps(meraki.get_location(),indent=4)

                        msg.post_message(msg.room_id, msg_reply)

                else:
                    msg.reply = f'Bot received message "{msg.message_text}"'
                    msg.post_message(msg.room_id, msg.reply)

                return data
        else: 
            return ('Wrong data format', 400)


############## Meraki Location Data Receiver #######
# https://github.com/CiscoDevNet/meraki_location_scanning_simulator

############## USER DEFINED SETTINGS ###############
# MERAKI SETTINGS
validator = "EnterYourValidator"
secret = "simulator"
version = "2.0"  # This code was written to support the CMX JSON version specified
locationdata = "Location Data Holder"
####################################################

@app.route("/location", methods=["POST"])
def get_locationJSON():
    global locationdata

    if not request.json or not "data" in request.json:
        return ("invalid data", 400)

    # Get location data, on update post a message with client data to the room
    locationdata = request.json

    pprint(locationdata, indent=1)
    print("Received POST from ", request.environ["REMOTE_ADDR"])

    # Verify secret
    if locationdata["secret"] != secret:
        print("secret invalid:", locationdata["secret"])
        return ("invalid secret", 403)

    else:
        print("secret verified: ", locationdata["secret"])

    # Verify version
    if locationdata["version"] != version:
        print("invalid version")
        return ("invalid version", 400)

    else:
        print("version verified: ", locationdata["version"])

    # Determine device type
    if locationdata["type"] == "DevicesSeen":
        print("WiFi Devices Seen")
    elif locationdata["type"] == "BluetoothDevicesSeen":
        print("Bluetooth Devices Seen")
    else:
        print("Unknown Device 'type'")
        return ("invalid device type", 403)

    # Return success message
    #return locationdata
    return "Location Scanning POST Received"

@app.route("/getlocation", methods=["GET"])
def get_location():
    return locationdata

@app.route("/location", methods=["GET"])
def get_validator():
    print("validator sent to: ", request.environ["REMOTE_ADDR"])
    return validator

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port, debug=True)
