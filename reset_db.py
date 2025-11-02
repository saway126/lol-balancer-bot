import sqlite3
import shutil
import os

DB_FILE = 'mmr_bot.db'
BACKUP = 'mmr_bot.db.bak'

if os.path.exists(DB_FILE):
    print(f'Backing up {DB_FILE} -> {BACKUP}')
    shutil.copyfile(DB_FILE, BACKUP)
    os.remove(DB_FILE)
    print('Database file removed. Run init_db_test.py or start the bot to recreate schema.')
else:
    print('No DB file found; nothing to backup or remove.')
