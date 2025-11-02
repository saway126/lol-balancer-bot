import aiosqlite
import asyncio
from typing import List, Optional

DB_PATH = 'mmr_bot.db'

CREATE_PLAYERS = '''
CREATE TABLE IF NOT EXISTS players (
    discord_id TEXT PRIMARY KEY,
    name TEXT,
    mmr_regular INTEGER DEFAULT 1200,
    mmr_general INTEGER DEFAULT 1200,
    games_played INTEGER DEFAULT 0,
    max_mmr INTEGER DEFAULT 1200
);
'''

CREATE_TEAMS = '''
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    member_ids TEXT,
    seed_mmr INTEGER DEFAULT 0
);
'''

CREATE_MATCHES = '''
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_a TEXT,
    team_b TEXT,
    winner TEXT,
    mmr_delta INTEGER,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
'''

async def init_db(path: str = DB_PATH):
    db = await aiosqlite.connect(path)
    await db.executescript('\n'.join([CREATE_PLAYERS, CREATE_TEAMS, CREATE_MATCHES]))
    # Ensure wins/losses columns exist (for simple +/-25 system)
    cur = await db.execute("PRAGMA table_info(players)")
    cols = await cur.fetchall()
    col_names = [c[1] for c in cols]
    if 'wins' not in col_names:
        await db.execute('ALTER TABLE players ADD COLUMN wins INTEGER DEFAULT 0')
    if 'losses' not in col_names:
        await db.execute('ALTER TABLE players ADD COLUMN losses INTEGER DEFAULT 0')
    await db.commit()
    await db.close()

class DB:
    def __init__(self, path: str = DB_PATH):
        self.path = path

    async def connect(self):
        self.db = await aiosqlite.connect(self.path)
        await self.db.execute('PRAGMA foreign_keys = ON')

    async def close(self):
        await self.db.close()

    async def ensure(self):
        await init_db(self.path)

    async def get_player(self, discord_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute('SELECT discord_id, name, mmr_regular, mmr_general, games_played, max_mmr, wins, losses FROM players WHERE discord_id = ?', (discord_id,))
            row = await cur.fetchone()
            if not row:
                return None
            keys = ['discord_id', 'name', 'mmr_regular', 'mmr_general', 'games_played', 'max_mmr', 'wins', 'losses']
            return dict(zip(keys, row))

    async def upsert_player(self, discord_id: str, name: str, regular: int = 1200, general: int = 1200, wins: int = 0, losses: int = 0):
        async with aiosqlite.connect(self.path) as db:
            # Use INSERT OR IGNORE then UPDATE to preserve existing wins/losses/games_played if present
            await db.execute('INSERT OR IGNORE INTO players(discord_id, name, mmr_regular, mmr_general, games_played, max_mmr, wins, losses) VALUES(?,?,?,?,?,?,?,?)', (discord_id, name, regular, general, 0, max(regular, general), wins, losses))
            await db.execute('UPDATE players SET name = ?, mmr_regular = ?, mmr_general = ? WHERE discord_id = ?', (name, regular, general, discord_id))
            await db.commit()

    async def set_player_mmr(self, discord_id: str, regular: Optional[int] = None, general: Optional[int] = None):
        async with aiosqlite.connect(self.path) as db:
            if regular is not None:
                await db.execute('UPDATE players SET mmr_regular = ?, games_played = games_played + 1, max_mmr = CASE WHEN ? > max_mmr THEN ? ELSE max_mmr END WHERE discord_id = ?', (regular, regular, regular, discord_id))
            if general is not None:
                await db.execute('UPDATE players SET mmr_general = ?, games_played = games_played + 1, max_mmr = CASE WHEN ? > max_mmr THEN ? ELSE max_mmr END WHERE discord_id = ?', (general, general, general, discord_id))
            await db.commit()

    async def register_team(self, name: str, member_ids: List[str], seed_mmr: int = 0):
        members_serial = ','.join(member_ids)
        async with aiosqlite.connect(self.path) as db:
            await db.execute('INSERT INTO teams(name, member_ids, seed_mmr) VALUES(?,?,?)', (name, members_serial, seed_mmr))
            await db.commit()

    async def list_top_players(self, limit: int = 10, use_regular: bool = False):
        col = 'mmr_regular' if use_regular else 'mmr_general'
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(f'SELECT discord_id, name, {col}, games_played, wins, losses, max_mmr FROM players ORDER BY {col} DESC LIMIT ?', (limit,))
            rows = await cur.fetchall()
            return [{'discord_id': r[0], 'name': r[1], 'mmr': r[2], 'games_played': r[3], 'wins': r[4], 'losses': r[5], 'max_mmr': r[6]} for r in rows]

    async def get_team(self, team_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute('SELECT id, name, member_ids, seed_mmr FROM teams WHERE id = ?', (team_id,))
            row = await cur.fetchone()
            if not row:
                return None
            return {'id': row[0], 'name': row[1], 'member_ids': row[2].split(',') if row[2] else [], 'seed_mmr': row[3]}

    async def get_team_members_mmrs(self, member_ids: List[str], use_regular: bool = False) -> List[int]:
        col = 'mmr_regular' if use_regular else 'mmr_general'
        if not member_ids:
            return []
        qmarks = ','.join('?' for _ in member_ids)
        async with aiosqlite.connect(self.path) as db:
            # If some players don't exist, auto-create them with default MMR
            cur = await db.execute(f'SELECT discord_id, {col} FROM players WHERE discord_id IN ({qmarks})', tuple(member_ids))
            rows = await cur.fetchall()
            found = {r[0]: r[1] for r in rows}
            results = []
            for pid in member_ids:
                if pid in found:
                    results.append(found[pid])
                else:
                    # create player with default MMR 1200
                    await self.upsert_player(pid, pid, regular=1200, general=1200)
                    results.append(1200)
            return results

    async def record_match(self, team_a_ids: List[str], team_b_ids: List[str], winner: str, use_regular: bool = False):
        """Record a match using simple +/-25 per player. Winner is 'A' or 'B'.
        Also updates wins/losses, games_played, max_mmr.
        """
        # Ensure players exist and fetch current mmrs
        a_mmrs = await self.get_team_members_mmrs(team_a_ids, use_regular)
        b_mmrs = await self.get_team_members_mmrs(team_b_ids, use_regular)

        # simple delta
        delta_win = 25
        delta_lose = -25

        async with aiosqlite.connect(self.path) as db:
            # Update team A
            for i, pid in enumerate(team_a_ids):
                # fetch current mmr
                cur = await db.execute('SELECT mmr_general, wins, losses, max_mmr FROM players WHERE discord_id = ?', (pid,))
                row = await cur.fetchone()
                if not row:
                    # should not happen because get_team_members_mmrs upserts, but guard
                    mmr = 1200
                    wins = 0
                    losses = 0
                    max_mmr = 1200
                else:
                    mmr, wins, losses, max_mmr = row
                if winner == 'A':
                    mmr = max(0, mmr + delta_win)
                    wins = wins + 1
                else:
                    mmr = max(0, mmr + delta_lose)
                    losses = losses + 1
                max_mmr = max(max_mmr, mmr)
                await db.execute('UPDATE players SET mmr_general = ?, games_played = games_played + 1, wins = ?, losses = ?, max_mmr = ? WHERE discord_id = ?', (mmr, wins, losses, max_mmr, pid))

            # Update team B
            for i, pid in enumerate(team_b_ids):
                cur = await db.execute('SELECT mmr_general, wins, losses, max_mmr FROM players WHERE discord_id = ?', (pid,))
                row = await cur.fetchone()
                if not row:
                    mmr = 1200
                    wins = 0
                    losses = 0
                    max_mmr = 1200
                else:
                    mmr, wins, losses, max_mmr = row
                if winner == 'B':
                    mmr = max(0, mmr + delta_win)
                    wins = wins + 1
                else:
                    mmr = max(0, mmr + delta_lose)
                    losses = losses + 1
                max_mmr = max(max_mmr, mmr)
                await db.execute('UPDATE players SET mmr_general = ?, games_played = games_played + 1, wins = ?, losses = ?, max_mmr = ? WHERE discord_id = ?', (mmr, wins, losses, max_mmr, pid))

            # record match summary (store mmr_delta as positive int for winner)
            mmr_delta = delta_win if winner == 'A' else delta_win
            await db.execute('INSERT INTO matches(team_a, team_b, winner, mmr_delta) VALUES(?,?,?,?)', (','.join(team_a_ids), ','.join(team_b_ids), winner, mmr_delta))
            await db.commit()
