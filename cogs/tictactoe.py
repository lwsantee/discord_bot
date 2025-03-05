from discord.ext import commands


class TicTacToe(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the TicTacToe game with the bot, game status, current player, and board.
        """
        self.bot = bot
        self.game_in_progress = False
        self.current_player = None
        self.board = None

    def reset_board(self):
        """
        Reset the TicTacToe board to its initial state with numbered cells.
        """
        self.board = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]

    def display_board(self):
        """
        Return the current state of the TicTacToe board as a string for display.
        """
        return "\n".join([" | ".join(row) for row in self.board])

    def check_winner(self, mark):
        """
        Check if a player with the specified mark ('X' or 'O') has won the game.
        """
        # Check rows for a win
        for row in self.board:
            if all(s == mark for s in row):
                return True

        # Check columns for a win
        for col in range(3):
            if all(self.board[row][col] == mark for row in range(3)):
                return True

        # Check diagonals for a win
        if all(self.board[i][i] == mark for i in range(3)):
            return True

        if all(self.board[i][2 - i] == mark for i in range(3)):
            return True

        return False

    def is_full(self):
        """
        Check if the board is full (i.e., no empty cells available).
        """
        return all(cell in ["X", "O"] for row in self.board for cell in row)

    def make_best_move(self):
        """
        AI logic for the bot to make the best possible move.
        The AI tries to win, block the player, take the center, take a corner, and then a side.
        """
        # Check if the bot can win on the next move
        for r in range(3):
            for c in range(3):
                if self.board[r][c] not in ["X", "O"]:
                    self.board[r][c] = "O"
                    if self.check_winner("O"):
                        return
                    self.board[r][c] = str(r * 3 + c + 1)  # Reset

        # Block player from winning
        for r in range(3):
            for c in range(3):
                if self.board[r][c] not in ["X", "O"]:
                    self.board[r][c] = "X"
                    if self.check_winner("X"):
                        self.board[r][c] = "O"
                        return
                    self.board[r][c] = str(r * 3 + c + 1)  # Reset

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
        """
        Start a new TicTacToe game if no game is in progress.
        """
        if self.game_in_progress:
            await ctx.send("A game is already in progress!")
            return

        self.game_in_progress = True
        self.current_player = (
            ctx.author
        )  # Set the current player to the person who starts the game
        self.reset_board()
        await ctx.send(
            f"Tic Tac Toe game started! {self.current_player.mention}, you are X. Enter a number (1-9) to make a move.\n```{self.display_board()}```"
        )

    @commands.command(name="move")
    async def make_move(self, ctx, pos: int):
        """
        Handle a player's move. The player provides a position (1-9), and the move is placed on the board.
        """
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

        self.current_player = ctx.author  # Switch to the next player
        await ctx.send(
            f"Your turn, {ctx.author.mention}!\n```{self.display_board()}```"
        )

    @commands.command(name="end")
    async def end_game(self, ctx):
        """
        End the current game if one is in progress.
        """
        if self.game_in_progress:
            self.game_in_progress = False
            await ctx.send("Game ended.")
        else:
            await ctx.send("No game in progress to end.")


async def setup(client):
    """
    Add the TicTacToe cog to the bot.
    """
    await client.add_cog(TicTacToe(client))
