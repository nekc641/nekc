import discord
from discord.ext import commands
import random
import json
import os
import requests  # Import requests for checking game status
from bs4 import BeautifulSoup  # Import BeautifulSoup for web scraping

# Set up the bot with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Ensure this is set to True
bot = commands.Bot(command_prefix='!', intents=intents)

# Data storage
user_data = {}
user_predictions = {}
user_game_status = {}  # To track the game state for each user
user_profiles = {}  # To track user profiles

# Load data from files
try:
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

try:
    with open('user_predictions.json', 'r') as f:
        user_predictions = json.load(f)
except FileNotFoundError:
    user_predictions = {}

try:
    with open('user_profiles.json', 'r') as f:
        user_profiles = json.load(f)
except FileNotFoundError:
    user_profiles = {}

# Function to check if the game has started
async def check_game_status(user_id):
    # Implement API call or web scraping logic here
    url = f"https://bloxflip.com/user/{user_id}"  # Example URL (you'll need to adjust this)
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Look for an element that indicates if the game is started
        game_status_element = soup.find('div', class_='game-status-class')  # Replace with actual class
        return game_status_element is not None  # True if game has started, False otherwise
    return False

# Command to connect user's Bloxflip token
@bot.command()
async def connect(ctx):
    await ctx.author.send("Please upload a .txt file containing your Bloxflip token.")

    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    try:
        msg = await bot.wait_for('message', check=check, timeout=60)  # Wait for 60 seconds for response
        if msg.attachments:
            # Check for .txt file
            for attachment in msg.attachments:
                if attachment.filename.endswith('.txt'):
                    token = await attachment.read()  # Read the file content
                    token = token.decode('utf-8').strip()  # Decode and strip any whitespace

                    # Simulate token validation (implement your actual token check here)
                    if token:
                        user_data[str(ctx.author.id)] = token
                        await ctx.author.send("Connected successfully! You can now use the predictor.")
                        return
                    else:
                        await ctx.author.send("Invalid token. Please try again.")
                        return
    except Exception as e:
        await ctx.author.send("An error occurred: " + str(e))

    await ctx.author.send("No valid .txt file received. Please try again.")

# Command to create user profile
@bot.command()
async def profile(ctx):
    user_id = str(ctx.author.id)
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            'predictions_made': 0,
            'correct_predictions': 0,
            'wrong_predictions': 0,
        }
    
    profile_info = user_profiles[user_id]
    embed = discord.Embed(title=f"Profile of {ctx.author.name}", color=discord.Color.blue())
    embed.add_field(name="Predictions Made", value=profile_info['predictions_made'], inline=False)
    embed.add_field(name="Correct Predictions", value=profile_info['correct_predictions'], inline=False)
    embed.add_field(name="Wrong Predictions", value=profile_info['wrong_predictions'], inline=False)
    await ctx.send(embed=embed)

# Command to predict safe spots
@bot.command()
async def predict(ctx, count: int = None, *, command_suffix: str = None):
    user_id = str(ctx.author.id)

    if user_id not in user_data:
        await ctx.send("Please connect your account first using !connect.")
        return

    game_started = await check_game_status(user_id)  # Check if the game has started
    if not game_started:
        await ctx.send("Please start the mine game on Bloxflip first.")
        return

    if count is None or command_suffix is None or command_suffix.strip().lower() != "nekc":
        await ctx.send("Please use the algorithm format: `!predict <count> nekc`. For example, `!predict 5 nekc`.")
        return

    if count < 1 or count > 25:
        await ctx.send("Please provide a number between 1 and 25.")
        return

    await ctx.send("Predicting...")

    # Enhanced prediction algorithm (customizable)
    safe_spots = enhanced_prediction_algorithm(count)
    grid_size = 25
    grid = ['💣' if i not in safe_spots else '✅' for i in range(grid_size)]

    # Format the grid for display
    grid_display = '\n'.join(' '.join(grid[i:i + 5]) for i in range(0, grid_size, 5))

    # Create the embed
    embed = discord.Embed(title="**Here is my prediction:**", description=grid_display)
    embed.add_field(name="**Safe Spots:**", value=', '.join(map(str, safe_spots)), inline=False)  # Display safe spots
    embed.set_footer(text="Use '!feedback correct' or '!feedback incorrect' to give feedback.")
    
    await ctx.send(embed=embed)

    # Update user profile for statistics
    if user_id not in user_predictions:
        user_predictions[user_id] = []
    
    user_predictions[user_id].append((safe_spots, count))
    user_profiles[user_id]['predictions_made'] += 1

# Enhanced prediction algorithm
def enhanced_prediction_algorithm(count):
    # Here you can implement a more complex prediction algorithm
    # For simplicity, let's just randomize for now
    return random.sample(range(25), count)  # Randomly choose safe spots

# Command to give feedback
@bot.command()
async def feedback(ctx, result: str):
    user_id = str(ctx.author.id)
    
    if user_id not in user_predictions or not user_predictions[user_id]:
        await ctx.send("You haven't made any predictions yet.")
        return

    if result not in ['correct', 'incorrect']:
        await ctx.send("Please use 'correct' or 'incorrect' as your feedback.")
        return

    user_predictions[user_id].append(result)
    await ctx.send(f"Feedback recorded: {result}. Thank you!")

    # Update user profile for statistics
    if result == 'correct':
        user_profiles[user_id]['correct_predictions'] += 1
    else:
        user_profiles[user_id]['wrong_predictions'] += 1

    # Calculate accuracy
    total_predictions = user_profiles[user_id]['correct_predictions'] + user_profiles[user_id]['wrong_predictions']
    if total_predictions > 0:
        accuracy = (user_profiles[user_id]['correct_predictions'] / total_predictions) * 100
        await ctx.send(f"Your prediction accuracy is: {accuracy:.2f}%")

# Enhanced help command
bot.remove_command('help')  # Remove the existing help command
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help - Nekc Predictor", description="Here are the commands you can use:", color=discord.Color.blue())
    
    embed.add_field(name="!connect", value="Connect your Bloxflip account by uploading a .txt file with your token.", inline=False)
    embed.add_field(name="!predict <count> nekc", value="Predict safe spots in the mine game. Example: `!predict 5 nekc`. You must have started a mine game to use this.", inline=False)
    embed.add_field(name="!profile", value="View your prediction statistics.", inline=False)
    embed.add_field(name="!feedback <correct/incorrect>", value="Give feedback on your predictions to improve future accuracy.", inline=False)
    
    embed.set_footer(text="Make sure you have the 'Predictor' role to use these commands.")
    
    await ctx.send(embed=embed)

# Save data to a file periodically or when the bot is shutting down
@bot.event
async def on_disconnect():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

    with open('user_predictions.json', 'w') as f:
        json.dump(user_predictions, f)

    with open('user_profiles.json', 'w') as f:
        json.dump(user_profiles, f)

# Event to confirm bot is online
@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name} (ID: {bot.user.id})')

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
