from database_sqlite import db

async def create_start_promos():
    """Создание стартовых промокодов (АСИНХРОННАЯ)"""
    conn = await db.get_connection()
    
    await conn.execute("""
        INSERT OR IGNORE INTO promocodes (code, reward, max_uses)
        VALUES (?, ?, ?)
    """, ("NEW", 2500, 1))
    
    await conn.execute("""
        INSERT OR IGNORE INTO promocodes (code, reward, max_uses)
        VALUES (?, ?, ?)
    """, ("mëpтв", 25000, 25))
    
    await conn.commit()
    print("✅ Стартовые промокоды созданы")
