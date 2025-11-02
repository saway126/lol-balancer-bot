import asyncio
from db import DB

async def seed_players(db: DB):
    # create sample players
    sample = [
        ('1001', 'Alice', 1300),
        ('1002', 'Bob', 1250),
        ('1003', 'Carol', 1200),
        ('1004', 'Dave', 1180),
    ]
    for pid, name, mmr in sample:
        await db.upsert_player(pid, name, general=mmr) if False else await db.upsert_player(pid, name, regular=mmr, general=mmr)

async def show_players(db: DB):
    tops = await db.list_top_players(10)
    print('Top players:')
    for p in tops:
        print(p)

async def run():
    db = DB('mmr_test.db')
    await db.ensure()
    await seed_players(db)
    print('Before:')
    await show_players(db)
    await db.record_match(['1001','1002'], ['1003','1004'], 'A')
    print('\nAfter match (A wins):')
    await show_players(db)

if __name__ == '__main__':
    asyncio.run(run())
