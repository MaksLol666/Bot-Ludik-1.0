from database_sqlite import db

def create_start_promos():
    """Создание стартовых промокодов (СИНХРОННАЯ)"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO promocodes (code, reward, max_uses)
        VALUES (?, ?, ?)
    """, ("NEW", 2500, 1))
    
    cursor.execute("""
        INSERT OR IGNORE INTO promocodes (code, reward, max_uses)
        VALUES (?, ?, ?)
    """, ("mëpтв", 25000, 25))
    
    conn.commit()
    print("✅ Стартовые промокоды созданы")
