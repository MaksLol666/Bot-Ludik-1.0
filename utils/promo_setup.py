from database import db

async def create_start_promos():
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO promocodes (code, reward, max_uses)
            VALUES ($1, $2, $3)
            ON CONFLICT (code) DO NOTHING
        """, "NEW", 2500, 1)
        
        await conn.execute("""
            INSERT INTO promocodes (code, reward, max_uses)
            VALUES ($1, $2, $3)
            ON CONFLICT (code) DO NOTHING
        """, "mëpтв", 25000, 25)
