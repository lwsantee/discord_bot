import urllib.parse
import requests
import json
import os
import subprocess


ffmpeg = None
librespot = None
SPOTIFY_API_PREFIX="https://api.spotify.com/v1"


def get_spotify_headers(): 
    return {
        "Authorization": f"Bearer {os.getenv('SPOTIFY_ACCESS_TOKEN')}",
    }


def search(query: str):
    encoded_query = urllib.parse.quote_plus(query)
    response = requests.get(f"{SPOTIFY_API_PREFIX}/search?q={encoded_query}&type=track&limit=1", headers=get_spotify_headers())
    if response.status_code == 200:
        return json.loads(response.text)
    else: 
        print(response.status_code)
        print(response.text)


def add_to_queue(uri: str): 
    encoded_uri = urllib.parse.quote(uri)
    response = requests.post(f"{SPOTIFY_API_PREFIX}/me/player/queue?uri={encoded_uri}&device_id={get_bot_device_id('Discord Bot')}", headers=get_spotify_headers())
    if response.status_code == 200:
        return response
    else:
        print(f"add_to_queue failed with response {response.status_code} and text {response.text}")


def get_bot_device_id(name: str): 
    response = requests.get(f"{SPOTIFY_API_PREFIX}/me/player/devices", headers=get_spotify_headers())
    if response.status_code == 200:
        body = json.loads(response.text)
        for device in body["devices"]: 
            if device["name"] == name: 
                print(f"found device {device['id']}")
                return device["id"]
        print("get_bot_device_id failed to find a device")
    else:
        print(f"get_bot_device_id failed with response {response.status_code} and text {response.text}")


def switch_to_device():
    headers = get_spotify_headers()
    headers["Content-Type"] = "application/json"
    response = requests.put(f"{SPOTIFY_API_PREFIX}/me/player", headers=headers, json={
        "device_ids": [
            get_bot_device_id('Discord Bot')
        ],
        "play": True
    })
    if 300 > response.status_code >= 200 :
        print("Successfully transferred playback")
    else:
        print(f"switch_to_device failed with code {response.status_code} and text {response.text}")


def set_volume_percent(percent: int): 
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100 inclusive")
    response = requests.put(f"{SPOTIFY_API_PREFIX}/me/player/volume?volume_percent={percent}", headers=get_spotify_headers())
    if 300 > response.status_code >= 200:
        print("Successfully set the volume")
    else:
        print(f"set_volume_percent failed with status {response.status_code} and message {response.text}")


def start_librespot():
    global librespot 
    librespot = subprocess.Popen([
        "librespot",
        "--name", "Discord Bot",
        "--backend", "pipe",
        "--bitrate", "320",
        "--access-token", os.getenv("SPOTIFY_ACCESS_TOKEN"),
        "--enable-volume-normalisation",
        "--initial-volume", "30",
    ], stdout=subprocess.PIPE)

    # ffmpeg will take librespot stdout and convert to Discord PCM
    ffmpeg = subprocess.Popen([
        "ffmpeg",
        "-f", "s16le", "-ar", "44100", "-ac", "2",
        "-i", "pipe:0",
        "-f", "s16le", "-ar", "48000", "-ac", "2",
        "pipe:1"
    ], stdin=librespot.stdout, stdout=subprocess.PIPE)
