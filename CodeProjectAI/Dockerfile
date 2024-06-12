FROM python:3

ENV AI_HOST         localhost
ENV AI_PORT         32168

ENV FOSCAM_HOST     localhost
ENV FOSCAM_PORT     88
ENV FOSCAM_USER     admin
ENV FOSCAM_PASSWORD admin

ENV MQTT_HOST       localhost
ENV MQTT_PORT       1883
ENV MQTT_USER       admin
ENV MQTT_PASSWORD   admin
ENV MQTT_TOPIC      CodeProjectAI
ENV POLLING_INTERVAL_SECONDS .5

WORKDIR /

COPY requirements.txt ./
COPY ./license_plate.txt /config/license_plate.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


CMD [ "python", "-u", "./license_plate.py" ]
