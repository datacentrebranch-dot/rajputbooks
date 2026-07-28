import sqlite3
from datetime import datetime

class BookstoreInventorySystem:
    def __init__(self, db_name="rajput_book_depot.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT UNIQUE,
                title TEXT NOT NULL,
                author TEXT,
                selling_price REAL,
                stock_quantity INTEGER
            )
        """)
        self.conn.commit()

    def add_book(self, isbn, title, author, selling_price, stock_quantity):
        try:
            self.cursor.execute("""
                INSERT INTO books (isbn, title, author, selling_price, stock_quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (isbn, title, author, selling_price, stock_quantity))
            self.conn.commit()
            print(f"Successfully added: {title}")
        except sqlite3.IntegrityError:
            print(f"Book with ISBN {isbn} already exists.")

    def process_sale(self, isbn, quantity):
        self.cursor.execute("SELECT id, title, selling_price, stock_quantity FROM books WHERE isbn = ?", (isbn,))
        book = self.cursor.fetchone()
        
        if not book:
            print("Book not found.")
            return

        book_id, title, price, stock = book

        if stock < quantity:
            print(f"Insufficient stock for '{title}'. Available: {stock}")
            return

        new_stock = stock - quantity
        self.cursor.execute("UPDATE books SET stock_quantity = ? WHERE id = ?", (new_stock, book_id))
        self.conn.commit()
        
        total_cost = price * quantity
        print(f"Sale successful! Sold {quantity} copy/copies of '{title}'. Total: {total_cost:.2f}")

    def close(self):
        self.conn.close()

# Example Usage:
# sys = BookstoreInventorySystem()
# sys.add_book("978-0134494166", "Python Crash Course", "Eric Matthes", 1200.0, 15)
# sys.process_sale("978-0134494166", 2)