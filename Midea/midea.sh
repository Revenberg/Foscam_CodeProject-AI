from midea_beautiful import find_appliances, appliance_state, connect_to_cloud
from midea_inventor_lib import MideaClient
import time
from msmart.device import air_conditioning as ac
from msmart.device.base import device
import logging
import time
#logging.basicConfig(level=logging.DEBUG)
from midea_python_client import MideaClient

appliances = find_appliances(
    account="sander@revenberg.info",  # Account e-mail
    password="Rev61272/",  # Account password
)

for appliance in appliances:
    print(f"{appliance!r}")
    print("========================")


appliance = appliance_state(
    address="192.168.2.242",  # APPLIANCE_IP_ADDRESS 
    account="sander@revenberg.info",  # Account e-mail
    password="Rev61272/",  # Account password
)
print(f"{appliance!r}")





_email="sander@revenberg.info"
_password="Rev61272/"
_sha256password = ""
_verbose = True		#Enable logging
_debug = False		#Disable debug messages
_logfile = ""		#Log to console (default)
client = MideaClient(_email, _password, _sha256password, _debug, _verbose, _logfile)

#client = MideaClient(_email="sander@revenberg.info", _password="Rev61272/", _sha256password ="", _debug=True)

res = client.login()
if res == -1:
  print( "Login error: please check log messages.")
else:
  sessionId = client.current["sessionId"]

appliances = {}
appliances = client.listAppliances()
print(appliances)
print("####################")
for a in appliances:
  print("----------------------------")
  print( "[id="+a["id"]+" type="+a["type"]+" name="+a["name"]+"]")
  print(a)




client = MideaClient("sander@revenberg.info", "Rev61272/", "")

res = client.login()
if res == -1:
  print( "Login error: please check log messages.")
else:
  sessionId = client.current["sessionId"]

appliances = {}
appliances = client.listAppliances()
for a in appliances:
  print( "[id="+a["id"]+" type="+a["type"]+" name="+a["name"]+"]")

  deviceId=a["id"]
  res = client.get_device_status(deviceId)
  if res == 1:
    print( client.deviceStatus.toString())













count=0
while True:
   count=count+1
   print(count)
   time.sleep(5)






