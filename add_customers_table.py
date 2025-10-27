
import sqlite3

def add_customers_table():
    """Connects to the database and adds the 'customers' table if it doesn't exist."""
    db_path = 'influencers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQL statement to create the customers table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL UNIQUE,
        address TEXT,
        phone TEXT,
        rep_email TEXT, -- Representative's Email
        rep_title TEXT, -- Representative's Title
        rep_name TEXT,  -- Representative's Name
        notes TEXT
    );
    """

    cursor.execute(create_table_query)
    print("Table 'customers' created or already exists.")

    # --- Add an example customer if the table is empty ---
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        print("Table 'customers' is empty. Inserting an example customer...")
        example_customer = (
            '未來科技股份有限公司',
            '123 創新大道, 科技城',
            '02-1234-5678',
            'contact@future-tech.com',
            '行銷總監',
            '林志明',
            '長期合作夥伴，專注於高科技產品線。'
        )
        cursor.execute("""
            INSERT INTO customers (company_name, address, phone, rep_email, rep_title, rep_name, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, example_customer)
        print("Example customer inserted.")

    conn.commit()
    conn.close()
    print(f"Database '{db_path}' is updated with 'customers' table.")

if __name__ == '__main__':
    add_customers_table()
