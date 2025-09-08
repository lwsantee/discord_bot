from flask import Flask, request
import os
import base64
import requests
import json
import threading
import time

app = Flask(__name__)


def clean_old_token(wait: int = 3600) -> bool:
    """
    Delete outdated access token after `wait` seconds. `wait` is usually defined by the 
    `expires_in` key in the authorization response from Spotify. By default, this is set 
    to one hour or 3600 seconds 

    :param wait: The number of seconds to wait before deleting an outdated key 
    :returns: `True` if the old token was successfully removed. `False` otherwise
    """

    time.sleep(wait)
    try: 
        del os.environ["SPOTIFY_ACCESS_TOKEN"]
        return True
    except KeyError:
        print("clean_old_token: SPOTIFY_ACCESS_TOKEN is already null")
        return False


@app.route("/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if os.getenv("AUTH_SERVER_SECURITY") is None:
        return {"error": "Problem fetching state"}, 500

    if state != os.getenv("AUTH_SERVER_SECURITY"):
        return {"error": "Received bad state"}, 401

    if state is None:
        return {"error": "Missing 'state' query parameter"}, 400
    if code is None:
        return {"error": "Missing 'code' query parameter"}, 400

    auth_form = f"code={code}&redirect_uri={os.getenv('AUTH_SERVER')}/callback&grant_type=authorization_code"
    encoded_auth = base64.b64encode(bytes(f"{os.getenv('SPOTIFY_CLIENT_ID')}:{os.getenv('SPOTIFY_CLIENT_SECRET')}", "utf-8"))
    headers = {
        "Authorization": f"Basic {encoded_auth.decode('utf-8')}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=auth_form)
    if response.status_code == 200:
        body = json.loads(response.text)
        print(body)
        os.environ["SPOTIFY_ACCESS_TOKEN"] = body["access_token"]
        os.environ["SPOTIFY_REFRESH_TOKEN"] = body["refresh_token"]
        clean_thread = threading.Thread(target=clean_old_token, args=(body["expires_in"],))
        clean_thread.start()
        return "Login Successful", 200
    else:
        return response.text, 400


@app.route("/access-token/<state>", methods=["GET"])
def access_token(state: str):
    if os.getenv("AUTH_SERVER_SECURITY") is None:
        return {"error": "Problem fetching state"}, 500

    if state != os.getenv("AUTH_SERVER_SECURITY"):
        return {"error": "Received bad state"}, 401

    if os.getenv("SPOTIFY_ACCESS_TOKEN") is None:
        return {"error": "not found"}, 404

    return os.getenv("SPOTIFY_ACCESS_TOKEN"), 200
        

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
