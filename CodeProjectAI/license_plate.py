import datetime
from io import BytesIO
import json
import requests
import sys
from PIL import Image
import os
import time
import xml.etree.ElementTree as ET
import urllib.request
import yaml
import paho.mqtt.client as mqtt
import random

ai_host = os.getenv("AI_HOST", "" )
ai_port = int(os.getenv("AI_PORT", "32168"))

foscam_host = os.getenv("FOSCAM_HOST", "" )
foscam_port = int(os.getenv("FOSCAM_PORT", "88"))
foscam_user = os.getenv("FOSCAM_USER", "" )
foscam_password = os.getenv("FOSCAM_PASSWORD", "" )

mqtt_host = os.getenv("MQTT_HOST", "")
mqtt_port = int(os.getenv("MQTT_PORT", "1883" ) )
mqtt_user = os.getenv("MQTT_USER", "" )
mqtt_password = os.getenv("MQTT_PASSWORD", "" )
mqtt_password = os.getenv("MQTT_PASSWORD", "" )
mqtt_topic = os.getenv("MQTT_TOPIC", "CodeProjectAI")

polling_interval_seconds = float(os.getenv("POLLING_INTERVAL_SECONDS", "0.5" ))

known_plates = {
    "N465VH": "Lynk & co",
}

def connect_mqtt(mqttclientid, mqttBroker, mqttPort ):
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"Connected to MQTT Broker! {mqttBroker}:{mqttPort}")
        if reason_code > 0:
            print(f"Failed to connect, return code {reason_code}")
    # Set Connecting Client ID
    client = mqtt.Client(client_id=mqttclientid, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(mqtt_user, mqtt_password)
    client.on_connect = on_connect
    client.connect(mqttBroker, mqttPort)
    print(f"connection to mqtt Successful {mqttBroker}:{mqttPort}")
    return client

def send_mqtt(client, mqtt_topic, message):
  result = client.publish(mqtt_topic, message)
#  result = client.publish(mqtt_topic, json.dumps(json_body))
  status = result[0]

  if status == 0:
     print(f"Send topic `{mqtt_topic}`")
  else:
     print(f"Failed to send message to topic {mqtt_topic} ")

print(f"Intervaltime {polling_interval_seconds}")

try:
  response = requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr={foscam_user}&pwd={foscam_password}")
  img = Image.open(BytesIO(response.content))
  print(f"connection to Foscam camera Successful http://{foscam_host}:{foscam_port}")

  try:
    buf = BytesIO()
    with img:
      img.save(buf, 'jpeg')
      fp = buf.getvalue()

      response = requests.post(
        url=f"http://{ai_host}:{ai_port}/v1/vision/detection",
        files=dict(upload=fp),
      )
    print(f"connection to CodeProjec.AI camera Successful {ai_host}:{ai_port}")
  except:
    print(f"connection to CodeProjec.AI camera Failed http://{ai_host}:{ai_port}")
except:
  print(f"connection to Foscam camera Failed http://{foscam_host}:{foscam_port}")

mqttclientid = f'python-mqtt-{random.randint(0, 1000)}'

client=connect_mqtt(mqttclientid, mqtt_host, mqtt_port )
client.loop_start()

motion_last = ""
human_last = ""
car_last = ""

human_last_name = ""
car_last_name = ""

counter = 20

carDetectAlarmState = False
motionDetectAlarm = False
humanDetectAlarmState = False

while True:
  response = urllib.request.urlopen(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=getDevState").read()
  root_node = ET.fromstring(response)

  motion_now = root_node.findall('motionDetectAlarm')[0].text
  if (motion_now != motion_last):
    motion_last = motion_now
    motionDetectAlarm = (motion_last == "2")


  car_now = root_node.findall('carDetectAlarmState')[0].text
  if (car_now != car_last):
    car_last = car_now
    carDetectAlarmState = (car_last == "2")

  human_now = root_node.findall('humanDetectAlarmState')[0].text
  if (human_now != human_last):
    human_last = human_now
    humanDetectAlarmState = (human_last == "2")

  if True or humanDetectAlarmState:
          response = requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr={foscam_user}&pwd={foscam_password}")
          img = Image.open(BytesIO(response.content))

          buf = BytesIO()
          with img:
              img.save(buf, 'jpeg')
              fp = buf.getvalue()

          response = requests.post(
              url=f"http://{ai_host}:{ai_port}/v1/vision/detection",
              files=dict(upload=fp),
          )
          human = response.json()

          if (human['count'] > 0):
            for prediction in human['predictions']:
              if prediction['label'] == "person":
                response = requests.post(
                  url=f"http://{ai_host}:{ai_port}/v1/vision/face/list",
                  files=dict(upload=fp),
                )
                face = response.json()
                # print(f"face: {face['faces']}")
                if human_last_name != f"{face['faces']}":
                  send_mqtt(client, f"{mqtt_topic}/faces", f"{face['faces']}")
                  img.save(f"/media/face_{counter}.jpg") # Save the image
                  human_last_name = f"{face['faces']}"

                  # amount of pictures
                  if counter <= 0:
                    counter = 20
                  else:
                    counter = counter - 1

  if carDetectAlarmState:
          response = requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&{foscam_user}&pwd={foscam_password}")
          img = Image.open(BytesIO(response.content))

          buf = BytesIO()
          with img:
              img.save(buf, 'jpeg')
              fp = buf.getvalue()

          response = requests.post(
              url=f"http://{ai_host}:{ai_port}/v1/vision/alpr",
              files=dict(upload=fp),
          )

          plates = response.json()
          plate = None

          if len(plates["predictions"]) > 0 and plates["predictions"][0].get("plate"):
              plate = str(plates["predictions"][0]["plate"]).replace(" ", "")
              score = plates["predictions"][0]["confidence"]
              #print(f"Checking plate: {plate} in {known_plates.keys()}")


          if plate is None:
              plate = f"{plate}"
          else:
              plate = f"{known_plates[plate]} - {plate}"

          if car_last_name != plate:
            send_mqtt(client, f"{mqtt_topic}/car", f"{known_plates[plate]}")
            car_last_name = plate

  time.sleep(polling_interval_seconds)

