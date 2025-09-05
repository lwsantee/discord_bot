from flask import Flask, request
import os
import base64
import requests
import json

app = Flask(__name__)


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
    app.run(port=3000, debug=False)
