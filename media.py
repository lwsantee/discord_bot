import random
import discord
import requests
import googleapiclient.discovery


# Method to search for images based on a query
async def image_search(ctx, *, query, CX, GOOGLE_API_KEY):
    try:
        # Set the search URL and parameters for the search
        search_url = "https://www.googleapis.com/customsearch/v1"
        search_params = {
            "q": query,
            "searchType": "image",
            "cx": CX,
            "key": GOOGLE_API_KEY,
            "num": 10
        }
        # Get the response from the URL
        response = requests.get(search_url, params=search_params).json()
        # Extract image links from the response
        images = [item["link"] for item in response.get("items", [])]
        # If no images were found, inform the user
        if not images:
            await ctx.send("No images found.")
        else:
            # Choose a random image from the results
            image_url = random.choice(images)
            # Create and return the embed
            embed = discord.Embed(
                title=f"Here's a {query} image for you!", color=discord.Color.blurple())
            embed.set_image(url=image_url)
            embed.set_footer(
                text=f'{images.index(image_url) + 1} of {len(images)}')
            await ctx.reply(embed=embed)
    except Exception as error:
        raise error


# Method to search for GIFs based on a query
async def gif_search(ctx, *, query, CX, GOOGLE_API_KEY):
    try:
        # Set the search URL and parameters for the search
        search_url = "https://www.googleapis.com/customsearch/v1"
        search_params = {
            "q": query,
            "searchType": "image",
            "imgType": "animated",
            "cx": CX,
            "key": GOOGLE_API_KEY,
            "num": 10
        }
        # Get the response from the URL
        response = requests.get(search_url, params=search_params).json()
        # Extract GIF links from the response
        gifs = [item["link"] for item in response.get("items", [])]
        # If no GIFs were found, inform the user
        if not gifs:
            await ctx.send("No GIFs found.")
        else:
            # Choose a random GIF from the results
            gif_url = random.choice(gifs)
            # Create and return the embed
            embed = discord.Embed(
                title=f"Here's a {query} GIF for you!", color=discord.Color.blurple())
            embed.set_image(url=gif_url)
            embed.set_footer(text=f'{gifs.index(gif_url) + 1} of {len(gifs)}')
            await ctx.reply(embed=embed)
    except Exception as error:
        raise error


# Method to search for videos based on a query
async def video_search(ctx, *, query, GOOGLE_API_KEY):
    try:
        # Set the parameters for the search
        search_params = {
            "q": query,
            "type": "video",
            "part": "id",
            "maxResults": 50
        }
        # Get the response from the URL
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=GOOGLE_API_KEY)
        results = youtube.search().list(**search_params).execute()
        # Extract video IDs from the response
        videos = [item["id"]["videoId"] for item in results["items"]
                  if item["id"]["kind"] == "youtube#video"]
        # If no videos were found, inform the user
        if not videos:
            await ctx.send("No videos found.")
        else:
            # Choose a random video from the results
            video_id = random.choice(videos)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            # Create and return the embed
            embed = discord.Embed(
                title=f"Here's a {query} video for you!", color=discord.Color.blurple())
            embed.add_field(name="Video URL", value=video_url, inline=False)
            embed.set_image(
                url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
            embed.set_footer(
                text=f'{videos.index(video_id) + 1} of {len(videos)}')
            await ctx.reply(embed=embed)
    except Exception as error:
        raise error
