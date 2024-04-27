# Sprinklers 
---
# Development Getting Started

## base raspberryPi install
#### install nginx
```sudo apt-get install nginx```   
```sudo systemctl enable nginx```

## api
#### setup
I have a venv of sprinkers_venv: 

``` python3 -m venv sprinklers_venv```  
``` source sprinklers_venv/bin/activate```  
``` pip3 install -r requirements.txt```

#### development of api
```uvicorn main:app --reload```  
http://localhost:8000   
http://localhost:8000/docs 

#### development with remote Raspberry Pi
So you'll need to setup your Raspberry Pi to allow for remote gpio check this out: 
https://gpiozero.readthedocs.io/en/stable/remote_gpio.html 
For development mode on your local computer just set an environment variable 
``` 
export SPRINKLER_DEV=true 
export SPRINKLER_IP=192.16.1.10
```
settings.py will load these values at boot. default is set to False for devmode.

```python
    devmode = os.environ.get("SPRINKLER_DEV",False)
    devip = os.environ.get("SPRINKLER_IP")
```


#### factory reset 
There is a script under the api called factory_reset.py. This is referenced at /factoryreset and requires that you validate intent by stating "I want to reset". This will drop all tables and load with basic data including pin/bcm, and a couple valves and zones. 

---
# What was I thinking when I built it?

### pins
For RaspberryPi we leverage a GPIO library to turn trigger a relay that operates the valves. However you need a map (provided in the "support" folder) to understand the GPIO BCM (refrence) vs the Pins (physical). There is a table "pins" referenced by the endpoints under /pins/. Currently we have mapping for RaspberryPi 4 & 5, funny enough they are the same.. but rather than hard code this, figued RaspberryPi 6 would change everything and I'd be angry... so it's there..

### valves
Valves are to make human understandable tags to reference a pin. Connecting "pin 3" (GPIO refrenence BCM 3) via a wire to relay port 1 seems a bit confusing. So you can label it as "Front Yard Flowers" or "Front Yard Lawn East". 

### zones
Zones are not a requirement, however are handy to group valves. Say you had multiple front yard lawn valves and wanted to water the entire "front yard lawn" at 8am. You can create a zone including multiple valves and run that in series. You can reference zones and valves in any schedule. 