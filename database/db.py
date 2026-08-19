import asyncpg

async def get_connection():
    return await asyncpg.connect("postgresql://postgres:rTb2Az6!@localhost:5432/dt1830")