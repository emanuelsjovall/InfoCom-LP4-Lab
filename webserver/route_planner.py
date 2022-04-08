from cmath import pi
from flask import Flask, request, render_template, jsonify
from flask.globals import current_app 
from geopy.geocoders import Nominatim
from flask_cors import CORS
import redis
import json
import requests
from queue import Queue
from multiprocessing import Process, Pipe

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa5'

# change this to connect to your redis server
# ===============================================
redis_server = redis.Redis("localhost", decode_responses=True, charset="unicode_escape")
# ===============================================

geolocator = Nominatim(user_agent="my_request")
region = ", Lund, Skåne, Sweden"

# Example to send coords as request to the drone
def send_request(drone_url, coords):
    with requests.Session() as session:
        resp = session.post(drone_url, json=coords)

def getQ(child_conn):
    if not q.empty():
        child_conn.send(q.get())
    else:
        child_conn.send(None)
    child_conn.close()


@app.route('/planner', methods=['POST'])
def route_planner():
    Addresses =  json.loads(request.data.decode())
    FromAddress = Addresses['faddr']
    ToAddress = Addresses['taddr']
    from_location = geolocator.geocode(FromAddress + region, timeout=None)
    to_location = geolocator.geocode(ToAddress + region, timeout=None)
    if from_location is None:
        message = 'Departure address not found, please input a correct address'
        return message
    elif to_location is None:
        message = 'Destination address not found, please input a correct address'
        return message
    else:
        # If the coodinates are found by Nominatim, the coords will need to be sent the a drone that is available
        coords = {'from': (from_location.longitude, from_location.latitude),
                  'to': (to_location.longitude, to_location.latitude),
                  }
        # ======================================================================
        # Here you need to find a drone that is availale from the database. You need to check the status of the drone, there are two status, 'busy' or 'idle', only 'idle' drone is available and can be sent the coords to run delivery
        # 1. Find avialable drone in the database
        # if no drone is availble:
        # drones = ["Test", "drone124"]
        drones = ["drone124"]
        # drones = {"Test": '10.11.44.126', "drone124": '10.11.44.124'}
        drones = {"drone124": '10.11.44.124'}
        # if drones == None:
        #     print("No drones in redis database idk man")

        drone = None

        for k, v in drones.items():
            info = redis_server.get(k)
            info = json.loads(info)
            if info['status'] == 'idle':
                drone = v
                break


        if drone == None:
            message = 'No available drone, request placed in queue'
            q.put(coords)
        else:
            # 2. Get the IP of available drone, 
            DRONE_URL = 'http://' + drone +':5000'
            # 3. Send coords to the URL of available drone
            send_request(DRONE_URL, coords)
            message = 'Got address and sent request to the drone'
    return message
        # ======================================================================


if __name__ == "__main__":
    q = Queue()
    app.run(debug=True, host='0.0.0.0', port='5002')
