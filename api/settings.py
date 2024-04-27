import os

def init():
    global devmode 
    global devip
    global pi_version
    devmode = os.environ.get("SPRINKLER_DEV",False)
    devip = os.environ.get("SPRINKLER_IP")


