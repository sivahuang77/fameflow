
import sqlite3

def add_products_table():
    """Connects to the database and adds the 'products' table if it doesn't exist."""
    db_path = 'influencers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQL statement to create the products table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        product_name TEXT NOT NULL,
        specifications TEXT,
        description TEXT,
        msrp REAL, -- Manufacturer's Suggested Retail Price
        discount_percentage REAL,
        notes TEXT
    );
    """

    cursor.execute(create_table_query)
    print("Table 'products' created or already exists.")

    # --- Optional: Add an example product if the table is empty ---
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        print("Table 'products' is empty. Inserting an example product...")
        example_product = (
            'SuperTech Inc.',
            'AI 智慧耳機 Pro',
            '顏色: 星際灰, 藍牙 5.4, 30小時續航',
            '搭載最新 AI 降噪演算法，提供沉浸式聽覺體驗，並可即時翻譯多國語言。',
            199.99,
            15.0, # 15% off
            '首批合作的網紅可額外獲得客製化充電盒。'
        )
        cursor.execute("""
            INSERT INTO products (company, product_name, specifications, description, msrp, discount_percentage, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, example_product)
        print("Example product inserted.")

    conn.commit()
    conn.close()
    print(f"Database '{db_path}' is updated with 'products' table.")

if __name__ == '__main__':
    add_products_table()
