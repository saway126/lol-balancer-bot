import os
import asyncio
import logging

from discord.ext import commands
import discord

from commands import setup_commands
try:
    import keyring
except Exception:
    keyring = None

logging.basicConfig(level=logging.INFO)

INTENTS = discord.Intents.default()
# Control privileged intents via environment variable for safety
enable_priv = os.getenv('ENABLE_PRIVILEGED_INTENTS', '0') == '1'
INTENTS.message_content = enable_priv
INTENTS.members = enable_priv

PREFIX = '!'

def main():
    token = os.getenv('DISCORD_TOKEN')
    # Fallback: try keyring (Windows Credential Manager) if available
    if not token and keyring is not None:
        try:
            token = keyring.get_password('mmr_bot', 'discord_token')
            if token:
                logging.info('Loaded DISCORD_TOKEN from keyring')
        except Exception:
            logging.exception('Failed to read token from keyring')

    if not token:
        raise SystemExit('Set DISCORD_TOKEN environment variable or store token in keyring (use store_token.ps1)')

    logging.info(f'Privileged intents enabled: {enable_priv}')
    bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS)

    @bot.event
    async def on_ready():
        logging.info(f'Logged in as {bot.user} (id={bot.user.id})')
        try:
            # register slash commands
            await bot.tree.sync()
            logging.info('Slash commands synced')
        except Exception as e:
            logging.warning('Failed to sync commands: %s', e)

    setup_commands(bot)

    bot.run(token)

if __name__ == '__main__':
    try:
        main()
    except discord.errors.LoginFailure:
        # Friendly error message for invalid/expired token
        print('ERROR: Invalid or expired DISCORD_TOKEN.\nPlease regenerate the bot token in the Discord Developer Portal and try again.\nDo NOT share the token publicly.')
        raise
    except discord.errors.PrivilegedIntentsRequired as e:
        # Provide clear instructions on how to enable privileged intents
        print('\nERROR: The bot requested privileged gateway intents that are not enabled for this application.')
        print('Actions you can take:')
        print('  1) Enable the needed intents in the Discord Developer Portal:')
        print('     - Open https://discord.com/developers/applications')
        print('     - Select your application -> Bot -> Privileged Gateway Intents')
        print('     - Enable "Message Content Intent" and/or "Server Members Intent" as needed, then Save Changes.')
        print('     - Restart the bot.')
        print('\n  2) Or modify the bot to not request privileged intents (if you only want slash commands):')
        print('     - In bot.py set INTENTS.message_content = False and INTENTS.members = False, then restart.\n')
        print('Detailed error from library:')
        print(str(e))
        raise
