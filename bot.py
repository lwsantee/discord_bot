import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from flask import Flask, request
import threading
import base64
import requests
import json
from spotify_controller import start_librespot


librespot = None 
app = Flask(__name__)
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix=".", help_command=None, intents=intents)

load_dotenv()


@app.route("/callback", methods=["GET"])
def callback():
    global librespot
    code = request.args.get("code")
    state = request.args.get("state")
    if code is None:
        return {"error": "Missing 'code' query parameter"}, 400

    auth_form = f"code={code}&redirect_uri={os.getenv('CALLBACK_URI')}&grant_type=authorization_code"
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
        start_librespot()
        return "Login Successful", 200
    else:
        return response.text, 400


@bot.event
async def on_ready():
    """
    Event triggered when the bot has successfully connected to Discord and is ready to operate.

    This event sends a message to a specific channel to notify that the bot is online.
    It also loads all the cogs from the "cogs" directory, except the "__init__.py" file.
    """
    print(f"Logged in as {bot.user.name}")

    channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))

    if channel:
        await channel.send(f"{bot.user.name} is online!")
    else:
        print(f"Could not find channel with provided ID")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")


def run_flask():
    app.run(port=3000, debug=False)


flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
