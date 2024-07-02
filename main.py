import sys
import paho.mqtt.client as mqtt
from topicStructure import *

import dbConnector as db

configMode = False
lastChipName = ""

client = mqtt.Client()

chips_ids = []

def restoreBarFromDb(chipName):
    conn = db.createConnection()
    with conn:
        barArray = db.retrieveBar(conn, chipName=chipName)
        if len(barArray) > 0 :
            bar = barArray[0]
            client.publish('LLBars/{}/group/set'.format(bar['chipName']), str(bar['groupId']), retain=True, qos=1)
            print('Published to LLBars/{}/group/set: '.format(chipName, str(bar['groupId'])))
            client.publish('LLBars/{}/position/set'.format(chipName), str(bar['position']), retain=True, qos=1)
            print('Published to LLBars/{}/position/set: {}'.format(chipName, bar['position']))
            maxPos = db.getMaxPositionId(conn, bar['groupId'])
            maxGroup = db.getMaxGroupId(conn)
            client.publish('LLBars/groups/{}/maxPos'.format(bar['groupId']), maxPos, retain=True, qos=1)  # Eigentlich interessiert hier barsInGroup!
            client.publish("LLBars/groups/maxGroups", str(maxGroup), retain=True, qos=1)
        else:
            print("No record for this bar.")


def restoreBarsFromDb():
    conn = db.createConnection()
    with conn:
        barArray = db.retrieveBars(conn)
        print(barArray)
        for bar in barArray:
            client.publish('LLBars/{}/group/set'.format(bar['chipName']), str(bar['groupId']), qos=1, retain=True)
            print('Published to LLBars/{}/group/set'.format(bar['chipName']))
            client.publish('LLBars/{}/position/set'.format(bar['chipName']), str(bar['position']), qos=1, retain=True)
            print('Published to bars/{}/position/set'.format(bar['chipName']))
            maxPos = db.getMaxPositionId(conn, bar['groupId'])
            client.publish('LLBars/groups/{}/maxPos'.format(bar['groupId']), maxPos, retain=True,
                           qos=1)  # Eigentlich interessiert hier barsInGroup!
        maxGroup = db.getMaxGroupId(conn)
        client.publish("LLBars/groups/maxGroups", str(maxGroup), retain=True, qos=1)


def addBarToGroup(chipName,  groupId):
    conn = db.createConnection()
    with conn:
        group = db.retrieveGroup(conn, groupId=groupId)
        position = len(group)
        db.addBar(conn, (chipName, groupId, position))
        client.publish('LLBars/{}/group/set'.format(chipName), str(groupId), qos=1, retain=True)
        print('Published to LLBars/{}/group/set'.format(chipName))
        client.publish('LLBars/{}/position/set'.format(chipName), str(position))
        print('Published to LLBars/{}/position/set'.format(chipName))
        print("Added {} to group {} on position {}".format(chipName, groupId, position))

        maxPos = db.getMaxPositionId(conn, groupId)
        maxGroup = db.getMaxGroupId(conn)
        client.publish('LLBars/groups/{}/maxPos'.format(groupId), maxPos, retain=True,
                       qos=1)  # Eigentlich interessiert hier barsInGroup!
        client.publish("LLBars/groups/maxGroups", str(maxGroup), retain=True, qos=1)


def addBarToGroupPosition(chipName,  groupId, position):
    conn = db.createConnection()
    with conn:
        db.addBar(conn, (chipName, groupId, position))
        client.publish('LLBars/{}/group/set'.format(chipName), str(groupId), qos=1, retain=True)
        print('Published to LLBars/{}/group/set'.format(chipName))
        client.publish('LLBars/{}/position/set'.format(chipName), str(position))
        print('Published to LLBars/{}/position/set'.format(chipName))
        print("Added {} to group {} on position {}".format(chipName, groupId, position))

        maxPos = db.getMaxPositionId(conn, groupId)
        maxGroup = db.getMaxGroupId(conn)
        client.publish('LLBars/groups/{}/maxPos'.format(groupId), maxPos, retain=True,
                       qos=1)  # Eigentlich interessiert hier barsInGroup!
        client.publish("LLBars/groups/maxGroups", str(maxGroup), retain=True, qos=1)


def getNewGroupId():
    maxGroupId = getMaxGroupId()
    newGroupId = maxGroupId + 1

    client.publish("LLBars/groups/maxGroups", str(newGroupId), qos=1, retain=True)

    return newGroupId


def getMaxGroupId() -> int:
    conn = db.createConnection()
    with conn:
        maxGroupId = db.getMaxGroupId(conn)
        if maxGroupId is None:
            maxGroupId = 0
        return maxGroupId


def undoChip(chipName: str):
    conn = db.createConnection()
    with conn:
        db.deleteChipRecord(conn, chipName)


def buttonCallback(client, userdata, msg):
    global lastChipName
    decodedPayload = msg.payload.decode('utf-8')
    print(msg.topic + " " + msg.payload.decode('utf-8'))
    topicTree = msg.topic.split('/')
    chipName = topicTree[chipNamePosition]

    if configMode:
        if lastChipName == chipName:
            undoChip(chipName = chipName)
            lastChipName = 'nikoStinkt'
            print("Reset group for Bar: {}".format(chipName))
        else:
            lastChipName = chipName
            print("New chip: {}".format(chipName))

        if decodedPayload == 'short':
            currentGroupNumber = getMaxGroupId()
            addBarToGroup(chipName, currentGroupNumber)
            print('{} added to current group {}'.format(chipName, currentGroupNumber))
        elif decodedPayload == 'long':
            newGroupId = getNewGroupId()
            addBarToGroup(chipName, newGroupId)
            print('{} added to new group {} on position 0'.format(chipName, newGroupId))
        else:
            print("cannot add bar {} to any group. discarded.".format(chipName))
    else:
        print("Button on {} pushed. No action taken. Not in config mode.".format(chipName))


def modeCallback(client, userdata, msg):
    global configMode
    decodedPayload = msg.payload.decode('utf-8')
    print(msg.topic + " " + msg.payload.decode('utf-8'))
    if decodedPayload == 'config':
        configMode = True
        print("Set mode to config mode.")
    elif decodedPayload == 'reset':
        conn = db.createConnection()
        with conn:
            groupsToReset = db.getMaxGroupId(conn)
            client.publish("LLBars/groups/maxGroups", str(0), qos=1, retain=True)
            for group in range(0, groupsToReset+1):
                client.publish('LLBars/groups/{}/maxPos'.format(str(group)), str(0), qos=1, retain=True)
            db.deleteAllBars(conn)
            print("Deleted All bars")
    elif decodedPayload == 'restore':
        conn = db.createConnection()
        with conn:
            restoreBarsFromDb()


    elif decodedPayload == 'normal':
        configMode = False
        print("Set mode to normal mode.")


def helloCallback(client, userdata, msg):
    decodedPayload = msg.payload.decode('utf-8')
    print(msg.topic + " " + msg.payload.decode('utf-8'))
    topicTree = msg.topic.split('/')
    chipName = decodedPayload

    chips_ids.append(chipName)
    print("Found {}. We have {} Bars.".format(chipName, len(chips_ids)))


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # client.subscribe("LLBars/+/button", qos=1)
    client.subscribe("LLBars/hello", qos=1)
    # client.subscribe("brain/mode", qos=2)
    # client.message_callback_add('LLBars/+/button', buttonCallback)
    client.message_callback_add('LLBars/hello', helloCallback)
    client.message_callback_add('brain/mode', modeCallback)
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
            print("We have {} bars. STRG + C to confiugre!".format(len(chips_ids)))
        except KeyboardInterrupt:
            break
    letsgo = str(input("Enter y to start configuration."))
    if letsgo == 'y':
        pass
    else:
        sys.exit()
    for bar in chips_ids:
        flash_bar(bar)
        group = int(input('Group?'))
        position = int(input('Position?'))
        addBarToGroupPosition(bar, group, position)
        print("Added Bar {} to Group {} on Position {}".format(bar, group, position))
        unflash_bar(bar)
    print("DONE!")




