import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("rajput_book_depot.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Books Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE,
            title TEXT NOT NULL,
            author TEXT,
            category TEXT,
            purchase_price REAL,
            selling_price REAL,
            stock_quantity INTEGER
        )
    """)
    
    # Sales Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            sale_date TEXT,
            customer_name TEXT,
            total_amount REAL
        )
    """)
    
    # Sale Items Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            book_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            subtotal REAL,
            FOREIGN KEY(sale_id) REFERENCES sales(id),
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
    """)
    
    # Purchases Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            purchase_date TEXT,
            supplier_name TEXT,
            total_amount REAL
        )
    """)
    
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# --- STREAMLIT UI CONFIGURATION ---
st.set_page_config(page_title="Rajput Book Depot", page_icon="📚", layout="wide")

st.title("📚 Rajput Book Depot")
st.subheader("Inventory, Sales & Purchase Management System")

# Sidebar Navigation
menu = ["Dashboard", "Inventory Management", "Point of Sale (POS)", "Purchase Stock", "View Sales History"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- 1. DASHBOARD ---
if choice == "Dashboard":
    st.header("Store Overview")
    
    # Fetch metrics
    cursor.execute("SELECT COUNT(*), SUM(stock_quantity), SUM(stock_quantity * selling_price) FROM books")
    total_titles, total_stock, total_value = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM sales")
    total_sales_count, total_revenue = cursor.fetchone()
    
    total_value = total_value if total_value else 0.0
    total_revenue = total_revenue if total_revenue else 0.0
    total_stock = total_stock if total_stock else 0
    total_titles = total_titles if total_titles else 0
    total_sales_count = total_sales_count if total_sales_count else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Book Titles", total_titles)
    col2.metric("Total Units in Stock", total_stock)
    col3.metric("Inventory Asset Value", f"Rs. {total_value:,.2f}")
    col4.metric("Total Revenue", f"Rs. {total_revenue:,.2f}")
    
    st.markdown("---")
    st.subheader("Low Stock Alert (Less than 5 items)")
    cursor.execute("SELECT title, author, stock_quantity, selling_price FROM books WHERE stock_quantity < 5")
    low_stock_books = cursor.fetchall()
    if low_stock_books:
        df_low = pd.DataFrame(low_stock_books, columns=["Title", "Author", "Stock Quantity", "Selling Price"])
        st.dataframe(df_low, use_container_width=True)
    else:
        st.success("All book stocks are at healthy levels!")

# --- 2. INVENTORY MANAGEMENT ---
elif choice == "Inventory Management":
    st.header("Inventory Management")
    
    tab1, tab2 = st.tabs(["Add New Book", "View / Update Stock"])
    
    with tab1:
        st.subheader("Add a New Book")
        with st.form("add_book_form"):
            col1, col2 = st.columns(2)
            with col1:
                isbn = st.text_input("ISBN / Barcode")
                title = st.text_input("Book Title")
                author = st.text_input("Author")
                category = st.text_input("Category (e.g., Academic, Novel, Competitive)")
            with col2:
                purchase_price = st.number_input("Purchase Price (Rs.)", min_value=0.0, format="%.2f")
                selling_price = st.number_input("Selling Price (Rs.)", min_value=0.0, format="%.2f")
                stock_quantity = st.number_input("Initial Stock Quantity", min_value=0, step=1)
                
            submit_book = st.form_submit_button("Save Book to Inventory")
            
            if submit_book:
                if title and isbn:
                    try:
                        cursor.execute("""
                            INSERT INTO books (isbn, title, author, category, purchase_price, selling_price, stock_quantity)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (isbn, title, author, category, purchase_price, selling_price, stock_quantity))
                        conn.commit()
                        st.success(f"Successfully added '{title}' to inventory!")
                    except sqlite3.IntegrityError:
                        st.error(f"Error: A book with ISBN {isbn} already exists.")
                else:
                    st.warning("Please fill in at least the Title and ISBN.")
                    
    with tab2:
        st.subheader("Current Inventory Catalog")
        cursor.execute("SELECT id, isbn, title, author, category, purchase_price, selling_price, stock_quantity FROM books")
        books_data = cursor.fetchall()
        if books_data:
            df_books = pd.DataFrame(books_data, columns=["ID", "ISBN", "Title", "Author", "Category", "Purchase Price", "Selling Price", "Stock"])
            st.dataframe(df_books, use_container_width=True)
        else:
            st.info("No books found in inventory yet.")

# --- 3. POINT OF SALE (POS) ---
elif choice == "Point of Sale (POS)":
    st.header("Billing & Sales Counter")
    
    cursor.execute("SELECT id, title, isbn, selling_price, stock_quantity FROM books WHERE stock_quantity > 0")
    available_books = cursor.fetchall()
    
    if not available_books:
        st.warning("No books available in stock to sell.")
    else:
        book_dict = {f"{b[1]} (ISBN: {b[2]}) - Stock: {b[4]} - Rs. {b[3]}": b for b in available_books}
        
        customer_name = st.text_input("Customer Name", value="Walk-in Customer")
        selected_book_label = st.selectbox("Select Book", options=list(book_dict.keys()))
        
        selected_book = book_dict[selected_book_label]
        book_id, title, isbn, price, max_stock = selected_book
        
        quantity = st.number_input("Quantity", min_value=1, max_value=max_stock, step=1)
        
        if st.button("Complete Sale"):
            invoice_no = f"INV-{int(datetime.now().timestamp())}"
            sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_amount = price * quantity
            
            # Record Sale Master
            cursor.execute("""
                INSERT INTO sales (invoice_number, sale_date, customer_name, total_amount)
                VALUES (?, ?, ?, ?)
            """, (invoice_no, sale_date, customer_name, total_amount))
            sale_id = cursor.lastrowid
            
            # Record Sale Item
            cursor.execute("""
                INSERT INTO sale_items (sale_id, book_id, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, book_id, quantity, price, total_amount))
            
            # Update Stock
            cursor.execute("""
                UPDATE books SET stock_quantity = stock_quantity - ? WHERE id = ?
            """, (quantity, book_id))
            
            conn.commit()
            st.success(f"Sale completed successfully! Invoice: {invoice_no} | Total: Rs. {total_amount:,.2f}")

# --- 4. PURCHASE STOCK ---
elif choice == "Purchase Stock":
    st.header("Purchase Stock from Supplier")
    
    cursor.execute("SELECT id, title, isbn FROM books")
    all_books = cursor.fetchall()
    
    if not all_books:
        st.warning("Please add books to the inventory catalog before recording purchases.")
    else:
        book_dict_p = {f"{b[1]} (ISBN: {b[2]})": b[0] for b in all_books}
        
        with st.form("purchase_form"):
            supplier_name = st.text_input("Supplier / Publisher Name")
            invoice_number = st.text_input("Supplier Invoice Number")
            selected_book_str = st.selectbox("Select Book", options=list(book_dict_p.keys()))
            purch_qty = st.number_input("Purchased Quantity", min_value=1, step=1)
            unit_cost = st.number_input("Unit Purchase Cost (Rs.)", min_value=0.0, format="%.2f")
            
            submit_purchase = st.form_submit_button("Record Purchase & Update Stock")
            
            if submit_purchase:
                book_id = book_dict_p[selected_book_str]
                purchase_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                total_cost = unit_cost * purch_qty
                
                # Insert Purchase Record
                cursor.execute("""
                    INSERT INTO purchases (invoice_number, purchase_date, supplier_name, total_amount)
                    VALUES (?, ?, ?, ?)
                """, (invoice_number, purchase_date, supplier_name, total_cost))
                
                # Update Inventory Stock & Purchase Price
                cursor.execute("""
                    UPDATE books SET stock_quantity = stock_quantity + ?, purchase_price = ? WHERE id = ?
                """, (purch_qty, unit_cost, book_id))
                
                conn.commit()
                st.success(f"Stock updated successfully for {selected_book_str} (+{purch_qty} units).")

# --- 5. VIEW SALES HISTORY ---
elif choice == "View Sales History":
    st.header("Sales History & Transactions")
    
    cursor.execute("""
        SELECT s.invoice_number, s.sale_date, s.customer_name, b.title, si.quantity, si.unit_price, s.total_amount
        FROM sales s
        JOIN sale_items si ON s.id = si.sale_id
        JOIN books b ON si.book_id = b.id
        ORDER BY s.id DESC
    """)
    sales_history = cursor.fetchall()
    
    if sales_history:
        df_sales = pd.DataFrame(sales_history, columns=["Invoice No", "Date & Time", "Customer", "Book Title", "Qty Sold", "Unit Price", "Total Amount"])
        st.dataframe(df_sales, use_container_width=True)
    else:
        st.info("No sales recorded yet.")
