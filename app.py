from ahk import AHK, Hotkey
import requests
from flask import Flask, abort, request
import argparse
import atexit

app = Flask(__name__)
ahk = AHK()

def get_mute(device_number, component_type):
    return ahk.sound_get(device_number=device_number, component_type=component_type, control_type='MUTE')

def set_mute(value, device_number, component_type):
    # Set mute state
    ahk.sound_set(value, device_number=device_number, component_type=component_type, control_type='MUTE')
    
    # Get mute state
    mic_state = get_mute(device_number, component_type)
    
    # Display mute state
    ahk.show_tooltip(f'Mute {mic_state}', second=1)
    


@app.route("/tryunmute")
def tryunmute():
    # Only this computer can unmute the mic
    if request.remote_addr != '127.0.0.1':
        abort(403)  # Forbidden

    # If mute is off, enable mute without sending requests
    if get_mute(app.config['ARGS'].device_number, app.config['ARGS'].component_type) == 'Off':
        set_mute(1, app.config['ARGS'].device_number, app.config['ARGS'].component_type)
        return "Muting because already unmuted"
    
    # Turn off mic mute
    set_mute(0, app.config['ARGS'].device_number, app.config['ARGS'].component_type)
    
    # Tell every other computer to mute their mics
    for ip in app.config['ARGS'].ip_addresses:
        r = requests.get(f'http://{ip}:65432/mute')
        print(r.text)
    
    return "Unmuted"

@app.route("/mute")
def mute():
    # Only this computer and the computers passed as arguments can mute the mic
    if request.remote_addr not in app.config['ARGS'].ip_addresses and request.remote_addr != '127.0.0.1':
        abort(403)  # Forbidden
    
    # Mute the mic
    set_mute(1, app.config['ARGS'].device_number, app.config['ARGS'].component_type)
    
    return "Muted"
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mutually Exclusive Unmute')

    parser.add_argument('device_number', type=int)
    parser.add_argument('component_type', choices=['MASTER', 'SPEAKERS', 'DIGITAL', 'LINE', 'MICROPHONE', 'SYNTH', 'CD', 'TELEPHONE', 'PCSPEAKER', 'WAVE', 'AUX', 'ANALOG', 'HEADPHONES', 'N/A'])
    parser.add_argument('ip_addresses', nargs='*', metavar='ip')
    args = parser.parse_args()
    
    hotkey = Hotkey(ahk, 'F4', 'UrlDownloadToFile, http://127.0.0.1:65432/unmute, %A_ScriptDir%\temp.txt')
    hotkey.start()
    
    @atexit.register
    def closing():
        print("=== Closing down ===")
        hotkey.stop()
    
    app.config["ARGS"] = args
    app.run(host="0.0.0.0", port=65432)

