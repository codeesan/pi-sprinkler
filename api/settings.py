import os

def init():
    global devmode 
    global devip
    global pi_version
    global current_bcm 
    current_bcm = None
    devmode = os.environ.get("SPRINKLER_DEV",False)
    devip = os.environ.get("SPRINKLER_IP")
    


