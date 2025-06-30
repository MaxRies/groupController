import sys
import paho.mqtt.client as mqtt
import requests

configMode = False
lastChipName = ""

client = mqtt.Client()

chip_ids = []

chip_dict = {}


MQTT_HOST = "192.168.0.2"
API_URL = "http://192.168.0.3/api"
headers={
    'Content-type':'application/json', 
    'Accept':'application/json'
}


def deleteAllBars():
    r = requests.delete(API_URL + "/bars")
    if r.status_code == requests.codes.ok:
        print("deleted all bars!")
    else:
        print("Error with deleting all bars.")
        print(r.status_code)

def addBarToChipDict(bar_name, bar_ip):
    global chip_dict
    chip_dict[bar_name] = bar_ip

def addBarToGroupPosition(chipName, ip, groupId, position):
    # Fix this to work with requests.
    endpoint = API_URL + "/bars"

    bar = {
        "bar_name": chipName,
        "bar_ip": ip,
        "bar_group": groupId,
        "bar_position": position
    }

    r = requests.post(endpoint, json=bar, headers = headers)
    print(r)
    if r.status_code == requests.codes.ok:
        print("Added bar.")
        print(bar)
    else:
        print("Error adding bar.")
        print(r.status_code)

    client.publish('LLBars/{}/group/set'.format(chipName), str(groupId), qos=1, retain=True)
    print('Published to LLBars/{}/group/set'.format(chipName))
    client.publish('LLBars/{}/position/set'.format(chipName), str(position))
    print('Published to LLBars/{}/position/set'.format(chipName))
    print("Added {} to group {} on position {}".format(chipName, groupId, position))

    # bug, weil ja die maxposition noch größer werden kann!
    #maxPos = db.getMaxPositionId(conn, groupId)
    #maxGroup = db.getMaxGroupId(conn)
    #client.publish('LLBars/groups/{}/maxPos'.format(groupId), maxPos, retain=True,
    #               qos=1)  # Eigentlich interessiert hier barsInGroup!
    #client.publish("LLBars/groups/maxGroups", str(maxGroup), retain=True, qos=1)
    return

def getMaxGroupAndPositions():
    endpoint = API_URL + "/bars/groups_and_max_positions"
    
    r = requests.get(endpoint)

    if r.status_code == requests.codes.ok:
        groups_and_positions = r.json()
        print(type(groups_and_max_positions))
        print(groups_and_max_positions)


def helloCallback(client, userdata, msg):
    decodedPayload = msg.payload.decode('utf-8')
    print(msg.topic + " " + msg.payload.decode('utf-8'))
    topicTree = msg.topic.split('/')
    chipName = decodedPayload

    chips_ids.append(chipName)
    print("Found {}. We have {} Bars.".format(chipName, len(chips_ids)))

def ipCallback(client, userdata, msg):
    decodedPayload = msg.payload.decode('utf-8')
    print(msg.topic + " " + msg.payload.decode('utf-8'))
    topicTree = msg.topic.split('/')

    chipName = topicTree[1]
    ip = decodedPayload

    addBarToChipDict(chipName, ip)
    print(f"Got bar: '{chipName}', IP: {ip}")


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # client.subscribe("LLBars/+/button", qos=1)
    client.subscribe("LLBars/hello", qos=1)
    client.subscribe("LLBars/+/IP", qos=1)

    # client.subscribe("brain/mode", qos=2)
    # client.message_callback_add('LLBars/+/button', buttonCallback)
    client.message_callback_add('LLBars/hello', helloCallback)
    client.message_callback_add('LLBars/+/IP', ipCallback)
    # client.publish("brain/mode", "normal", qos=1)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+msg.payload.decode('utf-8'))

def flash_bar(chip_id):
    client.publish('LLBars/{}/flash'.format(chip_id), str(1))
    print("Flashing bar {}".format(chip_id))

def unflash_bar(chip_id):
    client.publish('LLBars/{}/flash'.format(chip_id), str(0))
    print("Unflashing bar {}".format(chip_id))

def reset_brain():
    client.publish('brain/mode', str('config'))


if __name__ == "__main__":
    print("BAR CONFIGURATOR!")
    print("This will delete all bars from 192.168.0.3 database. Do you want to continue?")

    cont = str(input("Enter y to start configuration."))
    if cont == 'y':
        pass
    else:
        sys.exit()
    
    print("Deleting all bars...")
    deleteAllBars()

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.0.2", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    #client.loop_forever(retry_first_connection=True, timeout=5)
    client.loop_start()
    while True:
        try:
            print("We have {} bars. STRG + C to configure!".format(len(chip_dict.keys())))
        except KeyboardInterrupt:
            break
    letsgo = str(input("Enter y to start configuration."))
    if letsgo == 'y':
        pass
    else:
        sys.exit()
    for bar, ip in chip_dict.items():
        flash_bar(bar)
        group = int(input('Group?'))
        position = int(input('Position?'))
        addBarToGroupPosition(bar, ip, group, position)
        print("Added Bar {} to Group {} on Position {}".format(bar, group, position))
        unflash_bar(bar)
        print("DONE!")
    r = requests.get(API_URL + "/bars/groups_and_max_positions")
    if r.status_code == requests.codes.ok:
        groups_and_positions = r.json()
        for entry in groups_and_positions:
            group = entry[0]
            maxPos = entry[1]
            client.publish('LLBars/groups/{}/maxPos'.format(group), maxPos, retain=True, qos=1)  # Eigentlich interessiert hier barsInGroup!
        
        highest_entry = max(groups_and_positions, key=lambda x: x[0])
        client.publish("LLBars/groups/maxGroups", str(highest_entry), retain=True, qos=1)

    print("bye")



