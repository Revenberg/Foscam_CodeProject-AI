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

ENV TZ Etc/UTC

ENV PUID 1000
ENV PGID 1000

RUN groupadd -g $PGID nonroot
RUN adduser --system --no-create-home -u $PUID nonroot
RUN usermod -a -G nonroot nonroot

WORKDIR /

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

USER nonroot
COPY . .
COPY ./license_plate.txt /config/license_plate.txt
CMD [ "python", "-u", "./license_plate.py" ]
