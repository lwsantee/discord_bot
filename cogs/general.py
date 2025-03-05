from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        """
        Initializes the General cog with the bot instance.
        """
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """
        Responds with the bot's latency.
        """
        await ctx.reply(f"Pong! Latency: {round(self.bot.latency * 1000)}ms")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Listens for errors raised during command execution and handles specific errors.
        """
        if isinstance(error, commands.CommandNotFound):
            await ctx.reply("That command was not found.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("You are missing a required argument.")
        elif isinstance(error, commands.BadArgument):
            await ctx.reply("There was an issue with one of your arguments.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply("You do not have permission to run this command.")
        else:
            await ctx.reply("An error occurred. Please try again later.")
            raise error


async def setup(client):
    """
    Sets up the General cog by adding it to the bot client.
    """
    await client.add_cog(General(client))
