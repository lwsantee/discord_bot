import discord
from discord.ext import commands
import random


class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_in_progress = False
        self.current_player = None
        self.board = None

    def reset_board(self):
        self.board = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]

    def display_board(self):
        return "\n".join([" | ".join(row) for row in self.board])

    def check_winner(self, mark):
        # Check rows
        for row in self.board:
            if all(s == mark for s in row):
                return True

        # Check columns
        for col in range(3):
            if all(self.board[row][col] == mark for row in range(3)):
                return True

        # Check diagonals
        if all(self.board[i][i] == mark for i in range(3)):
            return True

        if all(self.board[i][2 - i] == mark for i in range(3)):
            return True

        return False

    def is_full(self):
        return all(cell in ["X", "O"] for row in self.board for cell in row)

    def make_best_move(self):
        # Simple AI: Prioritize winning, then blocking, then center, then corners, then sides.
        # Check if the bot can win in the next move
        for r in range(3):
            for c in range(3):
                if self.board[r][c] not in ["X", "O"]:
                    self.board[r][c] = "O"
                    if self.check_winner("O"):
                        return
                    self.board[r][c] = str(r * 3 + c + 1)  # reset

        # Check if the player could win on their next move, and block them
        for r in range(3):
            for c in range(3):
                if self.board[r][c] not in ["X", "O"]:
                    self.board[r][c] = "X"
                    if self.check_winner("X"):
                        self.board[r][c] = "O"
                        return
                    self.board[r][c] = str(r * 3 + c + 1)  # reset

        # Take the center if available
        if self.board[1][1] not in ["X", "O"]:
            self.board[1][1] = "O"
            return

        # Take a corner if available
        for r, c in [(0, 0), (0, 2), (2, 0), (2, 2)]:
            if self.board[r][c] not in ["X", "O"]:
                self.board[r][c] = "O"
                return

        # Take a side if available
        for r, c in [(0, 1), (1, 0), (1, 2), (2, 1)]:
            if self.board[r][c] not in ["X", "O"]:
                self.board[r][c] = "O"
                return

    @commands.command(name="start")
    async def start_game(self, ctx):
        if self.game_in_progress:
            await ctx.send("A game is already in progress!")
            return

        self.game_in_progress = True
        self.current_player = ctx.author
        self.reset_board()
        await ctx.send(
            f"Tic Tac Toe game started! {self.current_player.mention}, you are X. Enter a number (1-9) to make a move.\n```{self.display_board()}```"
        )

    @commands.command(name="move")
    async def make_move(self, ctx, pos: int):
        if not self.game_in_progress:
            await ctx.send("No game in progress. Use `!start` to start a game.")
            return

        if ctx.author != self.current_player:
            await ctx.send("It's not your turn!")
            return

        if not (1 <= pos <= 9):
            await ctx.send("Invalid move! Enter a number between 1 and 9.")
            return

        # Convert 1-9 to board indices
        row, col = divmod(pos - 1, 3)

        if self.board[row][col] in ["X", "O"]:
            await ctx.send("Invalid move! Cell already taken.")
            return

        # Place the mark
        self.board[row][col] = "X"

        if self.check_winner("X"):
            await ctx.send(
                f"{self.current_player.mention} wins!\n```{self.display_board()}```"
            )
            self.game_in_progress = False
            return
        elif self.is_full():
            await ctx.send(f"The game is a draw!\n```{self.display_board()}```")
            self.game_in_progress = False
            return

        # Bot makes a move
        self.make_best_move()

        if self.check_winner("O"):
            await ctx.send(f"Bot wins!\n```{self.display_board()}```")
            self.game_in_progress = False
            return
        elif self.is_full():
            await ctx.send(f"The game is a draw!\n```{self.display_board()}```")
            self.game_in_progress = False
            return

        self.current_player = ctx.author
        await ctx.send(
            f"Your turn, {ctx.author.mention}!\n```{self.display_board()}```"
        )

    @commands.command(name="end")
    async def end_game(self, ctx):
        if self.game_in_progress:
            self.game_in_progress = False
            await ctx.send("Game ended.")
        else:
            await ctx.send("No game in progress to end.")


async def setup(client):
    await client.add_cog(TicTacToe(client))
