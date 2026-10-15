import asyncpg
from config import *

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)