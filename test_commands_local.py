import asyncio
from db import DB
from commands import parse_member_input

async def main():
    db = DB('mmr_test.db')
    await db.ensure()

    # Example mention string (simulate what you'd paste in Discord)
    team_a_mentions = '<@1430192573816897598> <@!1002>'
    team_b_ids = ['2001', '2002']

    a_ids = parse_member_input(team_a_mentions)
    print('Parsed team A IDs:', a_ids)

    # Upsert players for both teams
    for pid in a_ids:
        await db.upsert_player(pid, f'user_{pid}', regular=1200, general=1200)
    for pid in team_b_ids:
        await db.upsert_player(pid, f'user_{pid}', regular=1200, general=1200)

    # Register teams
    await db.register_team('TeamA', a_ids, seed_mmr=1200)
    await db.register_team('TeamB', team_b_ids, seed_mmr=1200)
    print('Teams registered')

    # Record a match: A wins
    await db.record_match(a_ids, team_b_ids, 'A')
    print('Recorded match: TeamA (A) wins')

    # Show top players
    tops = await db.list_top_players(10)
    print('\nTop players after match:')
    for p in tops:
        print(p)

if __name__ == '__main__':
    asyncio.run(main())
