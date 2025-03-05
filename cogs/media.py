import random
import discord
from discord.ext import commands
import requests
import googleapiclient.discovery
from dotenv import load_dotenv
import os
from typing import Optional

# Load environment variables
load_dotenv()

class Media(commands.Cog):
    def __init__(self, bot):
        # Initialize bot and API keys
        self.bot = bot
        self.cx = os.getenv("CX")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

    async def fetch_search_results(self, search_url, search_params):
        # Fetch search results from an API
        try:
            response = requests.get(search_url, params=search_params).json()
            return [item["link"] for item in response.get("items", [])]
        except Exception as error:
            raise error

    async def create_embed(self, ctx, query, result_type, results, number, footer_text):
        # Create and send an embed with search results
        if not results:
            await ctx.reply(f"No {result_type} found.")
        elif number == "-1":
            embeds = []
            for result_url in results:
                embed = discord.Embed(
                    title=f"Here's a {query} {result_type} for you!",
                    color=discord.Color.blurple(),
                )
                embed.set_image(url=result_url)
                embed.set_footer(
                    text=f"{results.index(result_url) + 1} of {len(results)} {footer_text}"
                )
                embeds.append(embed)
                await ctx.reply(result_type)
            await ctx.reply(embeds=embeds)
        else:
            result_url = results[int(number) - 1]
            embed = discord.Embed(
                title=f"Here's a {query} {result_type} for you!",
                color=discord.Color.blurple(),
            )
            embed.set_image(url=result_url)
            embed.set_footer(
                text=f"{results.index(result_url) + 1} of {len(results)} {footer_text}"
            )
            await ctx.reply(embed=embed)

    async def google_image_search(self, ctx, query, number, result_type, img_type=None):
        # Perform a Google image search
        search_params = {
            "q": query,
            "searchType": "image",
            "cx": self.cx,
            "key": self.google_api_key,
            "num": 10,
        }
        if img_type:
            search_params["imgType"] = img_type

        results = await self.fetch_search_results(
            "https://www.googleapis.com/customsearch/v1", search_params
        )
        await self.create_embed(ctx, query, result_type, results, number, "")

    async def youtube_video_search(self, ctx, query):
        # Perform a YouTube video search
        try:
            search_params = {
                "q": query,
                "type": "video",
                "part": "id",
                "maxResults": 50,
            }
            youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=self.google_api_key
            )
            results = youtube.search().list(**search_params).execute()
            videos = [
                item["id"]["videoId"]
                for item in results["items"]
                if item["id"]["kind"] == "youtube#video"
            ]

            if not videos:
                await ctx.reply("No videos found.")
            else:
                video_id = random.choice(videos)
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                embed = discord.Embed(
                    title=f"Here's a {query} video for you!",
                    color=discord.Color.blurple(),
                )
                embed.add_field(name="Video URL", value=video_url, inline=False)
                embed.set_image(
                    url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                )
                embed.set_footer(
                    text=f"{videos.index(video_id) + 1} of {len(videos)} videos"
                )
                await ctx.reply(embed=embed)
        except Exception as error:
            await ctx.reply(f"An error occurred: {error}")
            raise error

    async def image_search_helper(self, ctx, query: str, is_gif: bool):
        # Handle search queries and determine image type
        parts = query.split(" ")
        if len(parts) == 0:
            await ctx.reply("Nothing to search for.")
            print("Query missing in `Media.image_search_helper`")
            return

        last_part = parts[-1]
        number = random.randint(1, 10)
        if last_part == "-1" or last_part.isdigit():
            number = int(last_part)
            query = " ".join(parts[:-1])
        else:
            query = " ".join(parts)

        if number > 10 or number == 0:
            number = random.randint(1, 10)

        if not is_gif:
            if number < 0:
                for n in range(1, 11):
                    await self.google_image_search(ctx, query, n, "image")
            else:
                await self.google_image_search(ctx, query, number, "image")
        else:
            if number < 0:
                for n in range(1, 11):
                    await self.google_image_search(
                        ctx, query, n, "GIF", img_type="animated"
                    )
            else:
                await self.google_image_search(
                    ctx, query, number, "GIF", img_type="animated"
                )

    @commands.command(name="image")
    async def image_search(self, ctx, *, query: str):
        # Search for an image
        await self.image_search_helper(ctx, query, False)

    @commands.command(name="gif")
    async def gif_search(self, ctx, *, query: str):
        # Search for a GIF
        await self.image_search_helper(ctx, query, True)

    @commands.command(name="video")
    async def video_search(self, ctx, *, query):
        # Search for a video
        await self.youtube_video_search(ctx, query)

async def setup(bot):
    # Add Media cog to the bot
    await bot.add_cog(Media(bot))
