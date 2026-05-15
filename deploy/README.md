# Deploying to Raspberry Pi

## What gets installed
| Component | How it runs |
|---|---|
| FastAPI backend | systemd service (`sprinkler-api`) via uvicorn |
| Vue frontend | nginx serving the built `dist/` on port 80 |

---

## One-time setup

### 1. Copy the project to the Pi
```bash
# From your Mac, rsync the project over (adjust hostname/path as needed)
rsync -av --exclude node_modules --exclude __pycache__ --exclude sprinklers_venv \
  /Users/cchandler/workspace/sprinklers/ pi@raspberrypi.local:~/sprinklers/
```

### 2. Run the install script on the Pi
SSH into the Pi, then:
```bash
cd ~/sprinklers
sudo bash deploy/install.sh
```

The script will:
- Install nginx, python3-venv, nodejs, npm
- Create the Python virtualenv and install all pip dependencies (including `smbus2` for the relay board)
- Build the Vue frontend into `frontend/dist/`
- Install and enable the `sprinkler-api` systemd service
- Configure nginx to serve the frontend on port 80

---

## After installation

| What | Command |
|---|---|
| Check API status | `sudo systemctl status sprinkler-api` |
| Tail API logs | `sudo journalctl -u sprinkler-api -f` |
| Restart API | `sudo systemctl restart sprinkler-api` |
| Check nginx | `sudo systemctl status nginx` |

Open a browser to `http://raspberrypi.local` (or the Pi's IP address).

---

## Updating after code changes

```bash
# From your Mac — push new code
rsync -av --exclude node_modules --exclude __pycache__ --exclude sprinklers_venv \
  /Users/cchandler/workspace/sprinklers/ pi@raspberrypi.local:~/sprinklers/

# On the Pi — rebuild frontend and restart API
cd ~/sprinklers
source sprinklers_venv/bin/activate
cd frontend && npm run build && cd ..
sudo systemctl restart sprinkler-api
```

---

## I2C setup (if not already enabled)

The PCF8575 relay board communicates over I2C. Enable it once:
```bash
sudo raspi-config nonint do_i2c 0
```
Then reboot. Verify the board is visible:
```bash
sudo i2cdetect -y 1
# Should show 0x27 in the grid
```
