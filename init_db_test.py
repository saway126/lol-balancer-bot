import asyncio
from db import init_db

async def main():
    await init_db('mmr_test.db')
    print('DB init complete')

if __name__ == '__main__':
    asyncio.run(main())
