"""
Aplicación principal que ejecuta el bot de Discord y el servidor Flask
"""

import asyncio
import threading
import os
from dotenv import load_dotenv
from discord import Intents, Client
from responses import get_response
from twitter_monitor import start_twitter_monitoring
from web import app
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# STEP 0: LOAD OUR TOKEN FROM SOMEWHERE SAFE
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# STEP 1: BOT SETUP
intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)


# STEP 2: MESSAGE FUNCTIONALITY
async def send_message(message, user_message):
    if not user_message:
        print('(Message was empty because intents were not enabled probably)')
        return

    if user_message[0] == '?':
        is_private = True
        user_message = user_message[1:]
    else:
        is_private = False

    try:
        response = get_response(user_message)
        if is_private:
            await message.author.send(response)
        else:
            await message.channel.send(response)
    except Exception as e:
        print(e)


# STEP 3: HANDLING THE STARTUP FOR OUR BOT
@client.event
async def on_ready():
    print(f'{client.user} is now running!')
    
    # Print available guilds and channels for debugging
    print('\n=== AVAILABLE SERVERS AND CHANNELS ===')
    for guild in client.guilds:
        print(f'\nServer: {guild.name} (ID: {guild.id})')
        for channel in guild.text_channels:
            print(f'   # {channel.name} (ID: {channel.id})')
    print('\n=====================================\n')
    
    # Start Twitter monitoring in the background
    asyncio.create_task(start_twitter_monitoring(client))


# STEP 4: HANDLING INCOMING MESSAGES
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    username = str(message.author)
    user_message = message.content
    channel = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)


def run_flask():
    """Ejecuta el servidor Flask en un thread separado"""
    print("\n" + "="*60)
    print("[WEB] Iniciando servidor Flask...")
    print("="*60)
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


def run_discord():
    """Ejecuta el cliente de Discord"""
    print("\n" + "="*60)
    print("[DISCORD] Iniciando bot de Discord...")
    print("="*60)
    client.run(token=TOKEN)


if __name__ == '__main__':
    # Iniciar Flask en un thread separado
    flask_thread = threading.Thread(target=run_flask, daemon=False)
    flask_thread.start()
    
    print("[MAIN] Esperando a que Flask se inicie...")
    import time
    time.sleep(2)
    
    # Iniciar Discord en el thread principal
    run_discord()
