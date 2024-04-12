# sprinklers

## base raspberryPi install
#### install nginx
```sudo apt-get install nginx```
```sudo systemctl enable nginx```

#### install postgres
```sudo apt-get install postgresql```
```sudo systemctl enable postgresql```

## api
#### setup
I have a venv of sprinkers_venv: 
``` python3 -m venv sprinkers_venv```
``` source sprinkers_venv/bin/activate```
``` pip3 install -r requirements.txt```

#### development of api
```uvicorn main:app --reload```
http://localhost:8000 
http://localhost:8000/docs 
