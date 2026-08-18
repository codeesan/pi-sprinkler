# Sprinklers 
---
# Development Getting Started

## base raspberryPi install
The `deploy/` folder has a script that installs nginx, the systemd service, the Python venv, and builds the frontend in one shot — see [`deploy/README.md`](deploy/README.md) for the full walkthrough:
```
sudo bash deploy/install.sh
```
Prefer to do it by hand? Keep reading below for the manual steps.

#### install nginx
```sudo apt-get install nginx```   
```sudo systemctl enable nginx```
## api
#### setup
I have a venv of sprinklers_venv (created at the project root, not inside `api/`):

``` python3 -m venv sprinklers_venv```  
``` source sprinklers_venv/bin/activate```
``` cd api ```  
``` pip3 install -r requirements.txt```

### i2c setup
The relay board (PCF8575) talks over I2C. Enable it once and confirm it's visible:
```
sudo raspi-config nonint do_i2c 0
sudo i2cdetect -y 1
# should show 0x27 in the grid
```

#### development of api
```uvicorn main:app --reload```  
http://localhost:8000   
http://localhost:8000/docs 

#### development off the Pi (e.g. on a Mac)
`smbus2` and the I2C bus only exist on the Pi. `main.py` detects when `smbus2` can't be imported and falls back to no-op hardware functions, so you can run the API anywhere for frontend/API work — the valve endpoints will just respond without actually switching anything.

## frontend
```
cd frontend
npm install
npm run dev
```
That starts the Vite dev server. `npm run build` produces the `dist/` folder that nginx serves in production — `deploy/install.sh` and `deploy/restart.sh` do this for you automatically.

---
# What was I thinking when I built it?

### pins
For RaspberryPi we leverage a GPIO library to turn trigger a relay that operates the valves. However you need a map (provided in the "support" folder) to understand the GPIO BCM (refrence) vs the Pins (physical). There is a table "pins" referenced by the endpoints under /pins/. Currently we have mapping for RaspberryPi 4 & 5, funny enough they are the same.. but rather than hard code this, figued RaspberryPi 6 would change everything and I'd be angry... so it's there..

### valves
Valves are to make human understandable tags to reference a pin. Connecting "pin 3" (GPIO refrenence BCM 3) via a wire to relay port 1 seems a bit confusing. So you can label it as "Front Yard Flowers" or "Front Yard Lawn East". 

### zones
Zones are not a requirement, however are handy to group valves. Say you had multiple front yard lawn valves and wanted to water the entire "front yard lawn" at 8am. You can create a zone including multiple valves and run that in series. You can reference zones and valves in any schedule. 