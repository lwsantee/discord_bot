import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Channel ID where the bot will send the startup message
CHANNEL_ID = 1096284252125012068

# Create intents with default settings
intents = discord.Intents.default()
# Enable message content intent to receive message content events
intents.message_content = True
# Initialize the bot with custom command prefix and intents
bot = commands.Bot(command_prefix=".", intents=intents)

# Load environment variables from .env file
load_dotenv()


# Event triggered when the bot is ready
@bot.event
async def on_ready():
    # Print a message to indicate that the bot is logged in
    print(f"Logged in as {bot.user.name}")
    # Get the channel object based on the provided CHANNEL_ID
    channel = bot.get_channel(CHANNEL_ID)
    # Check if the channel exists
    if channel:
        # Send a message to the channel indicating that the bot is online
        await channel.send(f"{bot.user.name} is online!")
    else:
        # Print a message if the channel with the provided ID is not found
        print(f"Could not find channel with ID {CHANNEL_ID}")

    # Load all cog extensions from the 'cogs' directory
    for filename in os.listdir("./cogs"):
        # Check if the file is a Python file and not the __init__.py file
        if filename.endswith(".py") and filename != "__init__.py":
            # Load the extension by removing the file extension and prefixing with 'cogs.'
            await bot.load_extension(f"cogs.{filename[:-3]}")


# Run the bot with the Discord bot token loaded from environment variables
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
