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

import datetime
import pytz

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

local_tz = pytz.timezone(os.getenv("TZ", "Europe/Amsterdam"))

polling_interval_seconds = float(os.getenv("POLLING_INTERVAL_SECONDS", "0.5" ))

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
    current_datetime = datetime.datetime.now(local_tz)
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    print(f"{formatted_datetime} connection to mqtt Successful {mqttBroker}:{mqttPort}")
    return client

def send_mqtt(client, mqtt_topic, msg):
  result = client.publish(mqtt_topic, msg, 1, retain=True)
  status = result[0]

  if status == 0:
     print(f"Send topic `{mqtt_topic}` { msg }")
  else:
     print(f"Failed to send message to topic {mqtt_topic} ")

def new_plate(client, plate):
  topic = f"homeassistant/binary_sensor/{ plate }"

  payload = {}
  payload["name"] = f"Kenteken { plate }"
  payload["device_class"] = "motion"
  payload["state_topic"] = f"{ topic }/state"
  payload["unique_id"] = f"kenteken{ plate }"

  payload["device"] = {}
  payload["device"]["identifiers"] = [ f"{ plate }" ]
  payload["device"]["name"] = known_plates[plate]

  send_mqtt(client, f"{ topic }/config", json.dumps(payload))

print(f"Intervaltime {polling_interval_seconds}")

try:
  requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=setSnapConfig&snapPicQuality=2")
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

human_last_name = ""
car_last_name = ""

car_counter = 20
reset_counter = 20

carDetectAlarmState = False
motionDetectAlarm = False
humanDetectAlarmState = False

known_plates["unknown"] = "unknown"
for plate in known_plates:
  new_plate(client, plate)
  topic = f"homeassistant/binary_sensor/{ plate }"

  send_mqtt(client, f"{ topic }/state", "OFF" )

while True:
  response = urllib.request.urlopen(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=getDevState").read()
  root_node = ET.fromstring(response)

  motion_now = root_node.findall('motionDetectAlarm')[0].text
#  if (motion_now != motion_last):
#    motion_last = motion_now
#    motionDetectAlarm = (motion_last == "2")

  car_now = root_node.findall('carDetectAlarmState')[0].text
#  if (car_now != car_last):
#    car_last = car_now
#    carDetectAlarmState = (car_last == "2")

  human_now = root_node.findall('humanDetectAlarmState')[0].text
#  if (human_now != human_last):
#    human_last = human_now
#    humanDetectAlarmState = (human_last == "2")

  carDetectAlarmState = (root_node.findall('carDetectAlarmState')[0].text == "2")
  humanDetectAlarmState = (root_node.findall('humanDetectAlarmState')[0].text == "2")

  if not humanDetectAlarmState:
     if reset_counter == 1:
        human_last_name = ""
     if reset_counter > 0:
        reset_counter = reset_counter - 1
  else:
    reset_counter = 20

  if not carDetectAlarmState:
    if car_counter == 1
      car_last_name = ""
      for plate in known_plates:
        topic = f"homeassistant/binary_sensor/{ plate }"
        send_mqtt(client, f"{ topic }/state", "OFF" )
    if car_counter > 0
      car_counter = car_counter -1

  if humanDetectAlarmState:
      response = requests.get(f"http://{foscam_host}:{foscam_port}/cgi-bin/CGIProxy.fcgi?usr={foscam_user}&pwd={foscam_password}&cmd=snapPicture2")
      try:
          img = Image.open(BytesIO(response.content))
#          img = Image.open(BytesIO(response.content))
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
              current_datetime = datetime.datetime.now(local_tz)
              formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
              if prediction['label'] == "person":
                response = requests.post(
                  url=f"http://{ai_host}:{ai_port}/v1/vision/face/list",
                  files=dict(upload=fp),
                )
                face = response.json()
                json_body = {}

                if human_last_name != f"{face['faces']}":
                  human_last_name = f"{face['faces']}"
                  json_body['name'] = f"{face['faces']}"
#                  img.save(f"/media/{human_last_name}_{formatted_datetime}.jpg".replace("'", "") ) # Save the image
#                  send_mqtt(client, f"{mqtt_topic}/faces", f"{human_last_name}")
                else:
                  json_body['name'] = "unknown"
                  human_last_name = "unknown"

                img.save(f"/media/face_{formatted_datetime}.jpg".replace("'", "") ) # Save the image
                json_body['filename'] = f"/media/face_{formatted_datetime}.jpg".replace("'", "")

                send_mqtt(client, f"{mqtt_topic}/faces", json.dumps(json_body))
      except Exception as e: 
        print(f"Error reading snapshot")
        print(e)
        print(response)

  if carDetectAlarmState:
      try:
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

          current_datetime = datetime.datetime.now(local_tz)
          formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")

          if len(plates["predictions"]) > 0:
            for prediction in plates['predictions']:
              print(f"car prediction: {prediction})")
              json_body = {}

              if prediction.get("plate"):
                plate = str(plates[prediction["plate"]]).replace(" ", "")

              plate_org = plate
              if plate is None:
                plate = f"{plate}"
                img.save(f"/media/car_{formatted_datetime}.jpg".replace("'", "")) # Save the image
                json_body['plate'] = plate
                json_body['filename'] = f"/media/car_{formatted_datetime}.jpg".replace("'", "")
              else:
                json_body['plate'] = plate_org
                if not known_plates.has_key(plate):
                  known_plates[plate] = "Onbekend kenteken"
                  new_plate(client, plate)
                plate = f"{known_plates[plate]} - {plate}"

                img.save(f"/media/car_{formatted_datetime}_{plate}.jpg".replace("'", "")) # Save the image
                json_body['plate'] = plate
                json_body['description'] = f"{known_plates[plate]}"
                json_body['filename'] = f"/media/car_{formatted_datetime}_{plate}.jpg".replace("'", "")

              if (car_last_name != plate_org) and not (plate_org == "") :
                send_mqtt(client, f"{mqtt_topic}/car", json.dumps(json_body))
                car_last_name = plate_org

                topic = f"homeassistant/binary_sensor/{ plate_org }"
                send_mqtt(client, f"{ topic }/state", "ON" )

      except Exception as e:
        print(f"Error reading snapshot")
        print(response)
        print(e)
        print(response)
  time.sleep(polling_interval_seconds)

