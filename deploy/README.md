# Deploying to Raspberry Pi

## What gets installed
| Component | How it runs |
|---|---|
| FastAPI backend | systemd service (`sprinkler-api`) via uvicorn |
| Vue frontend | nginx serving the built `dist/` on port 80 |

---

## One-time setup

### 1. Clone the repo onto the Pi
SSH into the Pi, then:
```bash
git clone https://github.com/codeesan/pi-sprinkler.git ~/pi-sprinkler
cd ~/pi-sprinkler
```

### 2. Enable I2C
The PCF8575 relay board communicates over I2C — enable it before installing (see the [I2C setup](#i2c-setup) section below).

### 3. Run the install script
```bash
sudo bash deploy/install.sh
```

The script will:
- Install nginx, python3, python3-venv, python3-pip, nodejs, npm, i2c-tools
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

On the Pi:
```bash
cd ~/pi-sprinkler
git pull
bash deploy/restart.sh
```
`restart.sh` re-syncs Python dependencies, rebuilds the frontend, and restarts the `sprinkler-api` service — it needs passwordless sudo for `systemctl` (or run it as root).

---

## I2C setup

The PCF8575 relay board communicates over I2C. Enable it once:
```bash
sudo raspi-config nonint do_i2c 0
```
Then reboot. Verify the board is visible:
```bash
sudo i2cdetect -y 1
# Should show 0x27 in the grid
```
