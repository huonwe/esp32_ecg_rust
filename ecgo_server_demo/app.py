from flask import Flask, render_template, Response, request, redirect, jsonify, make_response
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import numpy as np
import biosppy.signals.ecg as bsecg
import biosppy.signals.tools as st

from io import BytesIO
import base64
from flask_sock import Sock
import time
# import thread
MAX_ECG_QUEUE = 1500

global ecg_b64
ecg_queue = [0] * MAX_ECG_QUEUE
ecg_b64 = ""

def on_connect(client, userdata, flags, rc):
    print("conncected")
    client.subscribe('ecg')
    plt.subplot(2,2,1)
    plt.cla()
    plt.plot(np.arange(0,MAX_ECG_QUEUE)/500,np.zeros((MAX_ECG_QUEUE)))
    plt.grid(color = 'r', linestyle = '--', linewidth = 0.5)
    plt.title("filtered wave")
    plt.ylim(-500,1500)
    plt.subplots_adjust(wspace=0.5,hspace=0.7)
    figfile = BytesIO()
    plt.savefig(figfile,format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    global ecg_b64
    ecg_b64 = str(figdata_png, "utf-8")
    
def on_message(client, userdata, msg):
    data = msg.payload
    # print(len(data)/2)
    for i in range(0,len(data)//2):
        value = int.from_bytes(data[2*i:2*i+2],byteorder="big")
        ecg_queue.append(value)
        if len(ecg_queue) > MAX_ECG_QUEUE:
            # bsecg.ecg(ecg_queue,500)
            ecg_queue.pop(0)
    if len(ecg_queue) < 500:
        return
    
    isHighQ = False
    Processed = False
    try:
        out = bsecg.ecg(signal=ecg_queue,sampling_rate=500,show=False)
        filtered = out['filtered']
        Processed = True
    except Exception:
        order = int(0.3 * 500)
        filtered, _, _ = st.filter_signal(
            signal=np.array(ecg_queue),
            ftype="FIR",
            band="bandpass",
            order=order,
            frequency=[3, 45],
            sampling_rate=500,
        )
    
    plt.subplot(2,2,1)
    plt.cla()
    plt.plot(np.arange(0,len(filtered))/500,filtered)
    plt.grid(color = 'r', linestyle = '--', linewidth = 0.5)
    plt.title("filtered wave")
    plt.ylim(-500,1500)
    
    isHighQ = True
    if np.max(ecg_queue) < 500:
        isHighQ = False
    #if np.min(ecg_queue) > -500:
     #   isHighQ = False
        
    if Processed:
        plt.subplot(1,2,2)
        plt.cla()
        for t in out['templates']:
            if isHighQ:
                plt.plot(out['templates_ts'],t)
            else:
                plt.plot(out['templates_ts'],np.zeros((len(t))))
        plt.grid(color = 'r', linestyle = '--', linewidth = 0.5)
        plt.title("templates")
        
        plt.subplot(2,2,3)
        plt.cla()
        plt.ylim(50,150)
        if isHighQ:
            plt.plot(np.arange(0,len(out['heart_rate'])),out['heart_rate'])
        else:
            plt.plot(np.arange(0,len(out['heart_rate'])),np.zeros((len(out['heart_rate']))))
        # plt.plot(np.arange(0,len(out['heart_rate'])),out['heart_rate'])
        plt.grid(color = 'r', linestyle = '--', linewidth = 0.5)
        plt.title("heart rate")
    
    plt.subplots_adjust(wspace=0.5,hspace=0.7)
    figfile = BytesIO()
    plt.savefig(figfile,format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    global ecg_b64
    ecg_b64 = str(figdata_png, "utf-8")
    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("47.113.224.100")
client.loop_start()

app = Flask(__name__,static_folder="statics")
app.secret_key = 'huonwe'
sock = Sock(app)

@app.route("/")
def index():
    return render_template("index.html")

@sock.route("/plot")
def plot(sock):
    while True:
        time.sleep(0.5)
        sock.send(ecg_b64)

@sock.route("/neon")
def neon(sock):
    while True:
        rgb = sock.receive()
        # print(rgb)
        client.publish('led',payload=rgb)

app.run("0.0.0.0",port=5501)
