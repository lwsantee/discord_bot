import asyncio
from typing import Optional
import discord
import json
from discord.ext import commands
import os
import subprocess


class SoundSelect(discord.ui.View):
    def __init__(self, soundboard, ctx):
        super().__init__(timeout=60)  # Buttons expire after 60 seconds
        self.soundboard = soundboard
        self.ctx = ctx

        for sound_name in self.soundboard.sounds.keys():
            self.add_item(SoundButton(sound_name, soundboard, ctx))

class SoundButton(discord.ui.Button):
    def __init__(self, sound_name, soundboard, ctx):
        super().__init__(label=sound_name, style=discord.ButtonStyle.primary)
        self.sound_name = sound_name
        self.soundboard = soundboard
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can't select this!", ephemeral=True)
            return
        
        sound = self.soundboard.sounds[self.sound_name]
        voice_client = discord.utils.get(self.ctx.bot.voice_clients, guild=self.ctx.guild)
        
        if not voice_client or not voice_client.is_connected():
            if self.ctx.author.voice and self.ctx.author.voice.channel:
                voice_client = await self.ctx.author.voice.channel.connect()
            else:
                await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                return
        
        if voice_client.is_playing():
            voice_client.stop()

        def after_playing(error):
            if voice_client.is_playing():
                print("Still playing audio in soundboard.")
                return

            coro = voice_client.disconnect()
            fut = asyncio.run_coroutine_threadsafe(coro, self.ctx.bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Error in after_playing: {e}")
        
        voice_client.play(discord.FFmpegPCMAudio(sound.file), after=after_playing)
        await interaction.response.defer()  # Some response is required to let the user know their interaction worked


class Sound:
    def __init__(self, name: str, file: str, url: Optional[str]) -> None:
        self.name = name
        self.file = file
        self.url = url

    def to_json(self) -> dict[str, Optional[str]]:
        return self.__dict__


class Soundboard(commands.Cog):
    def __init__(self, client):
        self.client = client  # Discord bot client
        self.sounds: dict[str, Sound] = self.init_sounds()

    def init_sounds(self) -> dict[str, Sound]:
        try:
            with open("sounds.json", "r") as f:
                sound_data = json.load(f)
        except FileNotFoundError:
            with open("sounds.json", "w") as f:
                f.write("{}")
                sound_data = {}
        except json.JSONDecodeError:
            print("Error in Soundboard. Could not decode sounds.json")
            sound_data = {}

        sounds: dict[str, Sound] = {}
        for name, sound in sound_data.items():
            sounds[name] = Sound(name, sound["file"], sound["url"])
        return sounds

    def add_sound(self, sound: Sound):
        self.sounds[sound.name] = sound
        with open("sounds.json", "w") as f:
            json.dump(self.to_json(), f)

    def remove_sound(self, name: str) -> Optional[Sound]: 
        if name not in self.sounds: 
            return None
        sound = self.sounds.pop(name)

        try:
            os.remove(sound.file)
        except FileNotFoundError:
            print(f"Failed to remove {sound.file} in `Soundboard.remove_sound`")

        with open("sounds.json", "w") as f:
            json.dump(self.to_json(), f)

        return sound

    def to_json(self) -> dict[str, Optional[str]]:
        json = {}
        for name, sound in self.sounds.items():
            json[name] = sound.to_json()
        return json

    @commands.group(name="sound", invoke_without_command=True)
    async def sound(self, ctx):
        await ctx.reply("```\nlist\nadd\nrm\nplay\n```")

    @sound.command()
    async def add(self, ctx, url: str, name: str):
        # TODO: Allow renaming existing soundbytes
        if name in self.sounds:
            await ctx.reply(f"There is already a soundbyte called {name}")
            return 

        # TODO: Handle bad urls 
        os.makedirs("sounds", exist_ok=True)
        subprocess.run(f"python3 -m yt_dlp -x --format=bestaudio --embed-thumbnail --add-metadata -o sounds/{name} {url}".split(" "))
        self.add_sound(Sound(name, f"sounds/{name}.opus", url))
        await ctx.reply(f"Added soundbyte called {name} from {url}")

    @sound.command()
    async def pick(self, ctx):
        if not self.sounds: 
            await ctx.reply("No sounds available! You can add some with ```\n.sound add <url> <name>```")
            return 

        view = SoundSelect(self, ctx)
        await ctx.reply("Pick a sound to play:", view=view)
        

# Function to set up the Music cog
async def setup(client):
    await client.add_cog(Soundboard(client))
