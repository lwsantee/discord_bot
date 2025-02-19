import random
import discord
from discord.ext import commands
import requests
import googleapiclient.discovery
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cx = os.getenv("CX")  # Load CX from environment variables
        self.google_api_key = os.getenv(
            "GOOGLE_API_KEY"
        )  # Load Google API key from environment variables

    async def fetch_search_results(self, search_url, search_params):
        """
        Fetch search results from the given search URL with the specified parameters.
        """
        try:
            response = requests.get(search_url, params=search_params).json()
            return [item["link"] for item in response.get("items", [])]
        except Exception as error:
            raise error

    async def create_embed(self, ctx, query, result_type, results, number, footer_text):
        """
        Create and send an embed with the search results.
        """
        if not results:
            await ctx.reply(f"No {result_type} found.")
        elif number == '-1':
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
        """
        Perform a Google image search with the specified query and image type.
        """
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
        """
        Perform a YouTube video search with the specified query.
        """
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

    @commands.command(name="image")
    async def image_search(self, ctx, *, query):
        """
        Search for a random image.
        """
        parts = query.rsplit(' ', 1)
        if len(parts) == 2 and (parts[1].isdigit() and int(parts[1]) <= 10 and int(parts[1]) >= 1) or parts[1] == '-1':
            search_query, number = parts
            await self.google_image_search(ctx, search_query, number, "image")
        elif len(parts) == 2 and parts[1].isdigit():
            search_query, number = parts[0], random.randrange(1, 10)
            await self.google_image_search(ctx, search_query, number, "image")
        else:
            number = random.randrange(1, 10)
            await self.google_image_search(ctx, query, number, "image")


    @commands.command(name="gif")
    async def gif_search(self, ctx, *, query):
        """
        Search for a random GIF.
        """
        parts = query.rsplit(' ', 1)
        if len(parts) == 2 and (parts[1].isdigit() and int(parts[1]) <= 10 and int(parts[1]) >= 1) or parts[1] == '-1':
            search_query, number = parts
            await self.google_image_search(ctx, search_query, number, "GIF", img_type="animated")
        elif len(parts) == 2 and parts[1].isdigit():
            search_query, number = parts[0], random.randrange(1, 10)
            await self.google_image_search(ctx, search_query, number, "GIF", img_type="animated")
        else:
            number = random.randrange(1, 10)
            await self.google_image_search(ctx, query, number, "GIF", img_type="animated")
        
    @commands.command(name="video")
    async def video_search(self, ctx, *, query):
        """
        Search for a random video.
        """
        await self.youtube_video_search(ctx, query)


async def setup(bot):
    """
    Function to add the Media cog to the bot.
    """
    await bot.add_cog(Media(bot))
