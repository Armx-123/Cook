import os
import discord
import zipfile
from discord.ext import commands
import subprocess
# Define constants
MERGED_ZIP_PATH = "zip.zip"
TEMP_DIR = "temp"  # Temporary directory for storing ZIP parts

# Replace with the ID of the channel where the bot should upload the ZIP file
CHANNEL_ID = 1497264653628215508  # Replace with your target channel ID

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# Download all files from Discord and reassemble the original ZIP file
async def download_and_merge_zip(channel):
    zip_parts = []

    # Fetch all messages in channel and download attachments
    async for message in channel.history(limit=200):  # Increase limit if needed
        for attachment in message.attachments:
            part_path = os.path.join(TEMP_DIR, f"{attachment.id}_{attachment.filename}")  # Unique naming
            zip_parts.append((attachment.id, part_path))  # Store attachment ID for sorting
            await attachment.save(part_path)
            print(f"Downloaded {attachment.filename}")

    # Sort parts by attachment ID to ensure correct order
    zip_parts.sort(key=lambda x: x[0])  # Sort by attachment ID

    if zip_parts:
        print("Merging files...")
        with open(MERGED_ZIP_PATH, "wb") as merged_file:
            for _, part_path in zip_parts:
                with open(part_path, "rb") as part_file:
                    merged_file.write(part_file.read())
                os.remove(part_path)  # Clean up part after merging
        print(f"Merged ZIP file created: {MERGED_ZIP_PATH}")

        # Validate the merged ZIP file
        if validate_zip(MERGED_ZIP_PATH):
            print("ZIP file is valid.")
        else:
            print("Invalid ZIP file created.")
    else:
        print("No files found to merge.")

# Function to validate if the ZIP file is valid
def validate_zip(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            zip_file.testzip()  # Test the integrity of the ZIP file
        return True
    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        return False

# Run bot and merge files on start
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await download_and_merge_zip(channel)
    await bot.close()  # Stop bot after merging files

# Run the bot
bot.run(os.environ['RYNX'])
subprocess.run(["python", "SEO/unzip.py"], check=True)
# os.environ['TOKEN']
