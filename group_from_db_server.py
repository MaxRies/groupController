import paho.mqtt.client as mqtt
import requests

client = mqtt.Client()

MQTT_HOST = "192.168.0.2"
API_URL = "http://192.168.0.3/api"
headers={
    'Content-type':'application/json', 
    'Accept':'application/json'
}


def restoreBarFromDb(chipName):
    r = requests.get(API_URL + "/bars/" + chipName)

    if r.status_code == 200:
        bar = r.json()
            
        client.publish('LLBars/{}/group/set'.format(bar['bar_name']), str(bar['bar_group']), retain=True, qos=1)
        print('Published to LLBars/{}/group/set: {}'.format(chipName, str(bar['bar_group'])))
        client.publish('LLBars/{}/position/set'.format(chipName), str(bar['bar_position']), retain=True, qos=1)
        print('Published to LLBars/{}/position/set: {}'.format(chipName, bar['bar_position']))
    else:
        # okay, no bar found, so add it to the database with random data.
        endpoint = API_URL + "/bars"

        bar = {
            "bar_name": chipName,
            "bar_ip": "unconfigured",
            "bar_group": 0,
            "bar_position": 0
        }

        r = requests.post(endpoint, json=bar, headers = headers)
    #maxPos = db.getMaxPositionId(conn, bar['bar_group'])
    #maxGroup = db.getMaxGroupId(conn)
    #client.publish('LLBars/groups/{}/maxPos'.format(bar['bar_group']), maxPos, retain=True, qos=1)  # Eigentlich interessiert hier barsInGroup!
    #client.publish("LLBars/groups/maxGroups", str(maxGroup), retain=True, qos=1)
    #    else:
    #        print("No record for this bar, adding it to database")
    #        db.addBar(conn, (chipName, 0, 0))


def helloCallback(client, userdata, msg):
    # Hello comes once when the bar boots.
    # Restore its group and position an max group.
    decodedPayload = msg.payload.decode('utf-8')
    print(msg.topic + " " + msg.payload.decode('utf-8'))
    topicTree = msg.topic.split('/')
    chipName = decodedPayload

    restoreBarFromDb(chipName)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # First update with max numbers
    r = requests.get(API_URL + "/bars/groups_and_max_positions")
    if r.status_code == requests.codes.ok:
        groups_and_positions = r.json()
        for entry in groups_and_positions:
            group = entry[0]
            maxPos = entry[1]
            client.publish('LLBars/groups/{}/maxPos'.format(group), maxPos, retain=True, qos=1)  # Eigentlich interessiert hier barsInGroup!
        
        highest_entry = max(groups_and_positions, key=lambda x: x[0])
        client.publish("LLBars/groups/maxGroups", str(highest_entry), retain=True, qos=1)
    
    # now we are ready to add new bars...
    client.subscribe("LLBars/hello", qos=1)
    client.message_callback_add('LLBars/hello', helloCallback)
# The callback for when a PUBLISH message is received from the server.

def on_message(client, userdata, msg):
    print(msg.topic+" "+msg.payload.decode('utf-8'))


if __name__ == "__main__":
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.0.2", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    #client.loop_forever(retry_first_connection=True, timeout=5)
    client.loop_forever()
