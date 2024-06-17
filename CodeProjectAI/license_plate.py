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
import re

import datetime
import pytz

ai_host = os.getenv("AI_HOST", "" )
ai_port = int(os.getenv("AI_PORT", "32168"))

foscam_host = os.getenv("FOSCAM_HOST", "" )
foscam_port = int(os.getenv("FOSCAM_PORT", "88"))
foscam_user = os.getenv("FOSCAM_USER", "" )
foscam_password = os.getenv("FOSCAM_PASSWORD", "" )
foscam_snapPicQuality = os.getenv("FOSCAM_SNAPPICQUALITY", "2" )

mqtt_host = os.getenv("MQTT_HOST", "")
mqtt_port = int(os.getenv("MQTT_PORT", "1883" ) )
mqtt_user = os.getenv("MQTT_USER", "" )
mqtt_password = os.getenv("MQTT_PASSWORD", "" )
mqtt_password = os.getenv("MQTT_PASSWORD", "" )
mqtt_topic = os.getenv("MQTT_TOPIC", "CodeProjectAI")

polling_interval_seconds = float(os.getenv("POLLING_INTERVAL_SECONDS", "0.5" ))

print( f"{os.getenv("TZ", "Europe/Amsterdam")}")

known_plates = {}
with open("/config/license_plate.txt") as myfile:
    for line in myfile:
        name, var = line.partition("=")[::2]
        known_plates[name.strip()] = var.replace("\n", "")

print(f"{known_plates}")

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
    current_datetime = datetime.datetime.now(pytz.timezone(os.getenv("TZ", "Europe/Amsterdam")))
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    print(f"{formatted_datetime} connection to mqtt Successful {mqttBroker}:{mqttPort}")
    return client

def send_mqtt(client, mqtt_topic, msg):
  result = client.publish(mqtt_topic, msg, 1, retain=True)
  status = result[0]
  current_datetime = datetime.datetime.now(pytz.timezone(os.getenv("TZ", "Europe/Amsterdam")))
  formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
  if status == 0:
     print(f"{formatted_datetime} Send topic `{mqtt_topic}` { msg }")
  else:
     print(f"{formatted_datetime} Failed to send message to topic {mqtt_topic} ")

def new_plate(client, plate):
  topic = f"homeassistant/binary_sensor/plate{ plate }"

  payload = {}
  payload["name"] = f"Kenteken { plate }"
  payload["device_class"] = "motion"
  payload["state_topic"] = f"{ topic }/state"
  payload["unique_id"] = f"kenteken{ plate }"

  payload["device"] = {}
  payload["device"]["manufacturer"] = "localdetection"
  payload["device"]["model"] = "plate"
  payload["device"]["identifiers"] = [ f"{ plate }" ]
  payload["device"]["name"] = known_plates[plate]

  send_mqtt(client, f"{ topic }/config", json.dumps(payload))
  time.sleep(1)

def new_face(client, face):
  topic = f"homeassistant/binary_sensor/face{ face }"

  payload = {}
  payload["name"] = f"Gezicht { face }"
  payload["device_class"] = "motion"
  payload["state_topic"] = f"{ topic }/state"
  payload["manufacturer"] = "localdetection"

  payload["device"] = {}
  payload["device"]["manufacturer"] = "localdetection"
  payload["device"]["model"] = "face"
  payload["device"]["identifiers"] = [ f"{ face }" ]
  payload["device"]["name"] = f"{ face }"

  send_mqtt(client, f"{ topic }/config", json.dumps(payload))
  time.sleep(1)
  send_mqtt(client, f"{ topic }/state", "ON" )

print(f"Intervaltime {polling_interval_seconds}")

try:
  requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=setSnapConfig&snapPicQuality={foscam_snapPicQuality}")
  response = requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=snapPicture2")
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

human_last_name = "onbekend"
car_last_name = ""

car_counter = 120
reset_counter = 120

carDetectAlarmState = False
motionDetectAlarm = False
humanDetectAlarmState = False

#known_plates["onbekend"] = "onbekend"

for plate in known_plates:
  new_plate(client, plate)
  topic = f"homeassistant/binary_sensor/plate{ plate }"

  send_mqtt(client, f"{ topic }/state", "OFF" )

new_face(client, "onbekend")

while True:
  response = urllib.request.urlopen(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=getDevState").read()
  root_node = ET.fromstring(response)

  motion_now = root_node.findall('motionDetectAlarm')[0].text
  car_now = root_node.findall('carDetectAlarmState')[0].text
  human_now = root_node.findall('humanDetectAlarmState')[0].text

  carDetectAlarmState = (root_node.findall('carDetectAlarmState')[0].text == "2")
  humanDetectAlarmState = (root_node.findall('humanDetectAlarmState')[0].text == "2")

  if not humanDetectAlarmState:
     if reset_counter == 1:
        topic = f"homeassistant/binary_sensor/face{ human_last_name }"
        send_mqtt(client, f"{ topic }/state", "OFF" )
        human_last_name = ""

     if reset_counter > 0:
        reset_counter = reset_counter - 1
  else:
    reset_counter = 120

  if not carDetectAlarmState:
    if car_counter == 1:
      topic = f"homeassistant/binary_sensor/plate{ car_last_name }"
      send_mqtt(client, f"{ topic }/state", "OFF" )
      car_last_name = ""

    if car_counter > 0:
      car_counter = car_counter -1

  if humanDetectAlarmState:
    for x in range(10):
      try:
          response = requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=snapPicture2")

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
              current_datetime = datetime.datetime.now(pytz.timezone(os.getenv("TZ", "Europe/Amsterdam")))
              formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
              if prediction['label'] == "person":
                response = requests.post(
                  url=f"http://{ai_host}:{ai_port}/v1/vision/face/list",
                  files=dict(upload=fp),
                )
                face_resp = response.json()

                face = f"{face_resp['faces']}".replace("[", "").replace("]", "")
                if face == "":
                  human_last_name = "onbekend"

                if human_last_name != face:
                   img.save(f"/media/face_{formatted_datetime}.jpg".replace("'", "") ) # Save the image
                   new_face(client, human_last_name)

      except Exception as e:
        print(f"Fase Error reading snapshot")
        print(e)
        print(response)

  if carDetectAlarmState:
      try:
        for x in range(10):
          response = requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=snapPicture2")
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

          current_datetime = datetime.datetime.now(pytz.timezone(os.getenv("TZ", "Europe/Amsterdam")))
          formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
          if plates["predictions"] is None:
             print("Geen kentekenplaat")
          else:
            if len(plates["predictions"]) == 0:
               print("Geen kentekenplaat")

            if len(plates["predictions"]) > 0:
              for prediction in plates["predictions"]:
                  plate = prediction["plate"]
                  if plate is None:
                    plate = ""
                  else:
                    plate = re.sub(r'[^a-zA-Z0-9]', '', str(prediction["plate"]))
                    plate_org = plate
                    if known_plates.get(plate) is None:
                      known_plates[plate] = "onbekend kenteken"
                      new_plate(client, plate)
                      img.save(f"/media/car_{formatted_datetime}_{ plate }.jpg".replace("'", "")) # Save the image
                    else:
                      plate = f"{known_plates[plate]} - {plate}"
                      img.save(f"/media/car_{formatted_datetime}_{plate}.jpg".replace("'", "")) # Save the image

                    if (car_last_name != plate_org) and not (plate_org == "") :
                      topic = f"homeassistant/binary_sensor/plate{ plate }"
                      topic = f"homeassistant/binary_sensor/plate{ car_last_name }"

                      car_last_name = plate_org

                      topic = f"homeassistant/binary_sensor/plate{ plate_org }"
                      send_mqtt(client, f"{ topic }/state", "ON" )

      except Exception as e:
        print(f"Car Error reading snapshot")
        print(response)
        print(e)
  time.sleep(polling_interval_seconds)
