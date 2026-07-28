import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("rajput_book_depot.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Books Table (Checking and adding missing columns safely for existing databases)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE,
            title TEXT NOT NULL,
            author TEXT,
            school_group TEXT,
            academic_class TEXT,
            category TEXT,
            purchase_price REAL,
            selling_price REAL,
            stock_quantity INTEGER
        )
    """)
    
    # Safely migrate columns if an older database version already exists without them
    cursor.execute("PRAGMA table_info(books)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "school_group" not in existing_columns:
        cursor.execute("ALTER TABLE books ADD COLUMN school_group TEXT")
    if "academic_class" not in existing_columns:
        cursor.execute("ALTER TABLE books ADD COLUMN academic_class TEXT")
    
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

    # Expenses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT,
            category TEXT,
            amount REAL,
            description TEXT
        )
    """)
    
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# --- CONSTANTS FOR CLASSIFICATION ---
SCHOOL_GROUPS = [
    "General / Public Board",
    "Oxford / Cambridge System",
    "Private Allied / Beaconhouse Style",
    "Madrasah / Dars-e-Nizami",
    "Degree College & University Level"
]

ACADEMIC_CLASSES = [
    "Play Group", "Nursery", "Prep",
    "Class 1", "Class 2", "Class 3", "Class 4", "Class 5",
    "Class 6", "Class 7", "Class 8",
    "Class 9 (Matric / O-Level)", "Class 10 (Matric / O-Level)",
    "First Year (11th / A-Level)", "Second Year (12th / A-Level)",
    "B.A / B.Sc / BS (Undergraduate)", "Masters (M.A / M.Sc / MS)"
]

# --- STREAMLIT UI CONFIGURATION ---
st.set_page_config(page_title="Rajput Book Depot", page_icon="📚", layout="wide")

st.title("📚 Rajput Book Depot")
st.subheader("Inventory, Sales, Purchase & Class-Wise School Group System")

# Sidebar Navigation
menu = ["Dashboard", "Inventory Management", "Point of Sale (POS)", "Purchase Stock", "Expense Tracker", "Reports & History"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- 1. DASHBOARD ---
if choice == "Dashboard":
    st.header("Store Financial & Stock Overview")
    
    cursor.execute("SELECT COUNT(*), SUM(stock_quantity), SUM(stock_quantity * selling_price) FROM books")
    total_titles, total_stock, total_value = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM sales")
    total_sales_count, total_revenue = cursor.fetchone()

    cursor.execute("SELECT SUM(total_amount) FROM purchases")
    total_purchases = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0]
    
    total_value = total_value if total_value else 0.0
    total_revenue = total_revenue if total_revenue else 0.0
    total_purchases = total_purchases if total_purchases else 0.0
    total_expenses = total_expenses if total_expenses else 0.0
    total_stock = total_stock if total_stock else 0
    total_titles = total_titles if total_titles else 0
    
    gross_profit = total_revenue - total_purchases
    net_profit = gross_profit - total_expenses

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Book Titles", total_titles)
    col2.metric("Total Units in Stock", total_stock)
    col3.metric("Inventory Asset Value", f"Rs. {total_value:,.2f}")
    col4.metric("Total Revenue", f"Rs. {total_revenue:,.2f}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Total Purchases Outflow", f"Rs. {total_purchases:,.2f}")
    col6.metric("Total Shop Expenses", f"Rs. {total_expenses:,.2f}")
    col7.metric("Estimated Net Profit", f"Rs. {net_profit:,.2f}", delta=f"Rs. {net_profit:,.2f}")
    
    st.markdown("---")
    st.subheader("⚠️ Low Stock Alert (Less than 5 items)")
    cursor.execute("SELECT title, author, school_group, academic_class, stock_quantity, selling_price FROM books WHERE stock_quantity < 5")
    low_stock_books = cursor.fetchall()
    if low_stock_books:
        df_low = pd.DataFrame(low_stock_books, columns=["Title", "Author", "School Group", "Class", "Stock Quantity", "Selling Price"])
        st.dataframe(df_low, use_container_width=True)
    else:
        st.success("All book stocks are at healthy levels!")

# --- 2. INVENTORY MANAGEMENT ---
elif choice == "Inventory Management":
    st.header("Inventory Management Catalog")
    
    tab1, tab2 = st.tabs(["Add New Book", "View / Filter Catalog (Class & Group)"])
    
    with tab1:
        st.subheader("Add a New Book with School Group & Class")
        with st.form("add_book_form"):
            col1, col2 = st.columns(2)
            with col1:
                isbn = st.text_input("ISBN / Barcode")
                title = st.text_input("Book Title")
                author = st.text_input("Author / Publisher Brand")
                school_group = st.selectbox("School Group System", SCHOOL_GROUPS)
                academic_class = st.selectbox("Academic Class Level", ACADEMIC_CLASSES)
            with col2:
                category = st.selectbox("Subject Type", ["Textbook", "Workbook / Guide", "Competitive Exam", "Novel / Literature", "Religious / Islamic", "General Knowledge"])
                purchase_price = st.number_input("Purchase Price (Rs.)", min_value=0.0, format="%.2f")
                selling_price = st.number_input("Selling Price (Rs.)", min_value=0.0, format="%.2f")
                stock_quantity = st.number_input("Initial Stock Quantity", min_value=0, step=1)
                
            submit_book = st.form_submit_button("Save Book to Inventory")
            
            if submit_book:
                if title and isbn:
                    try:
                        cursor.execute("""
                            INSERT INTO books (isbn, title, author, school_group, academic_class, category, purchase_price, selling_price, stock_quantity)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (isbn, title, author, school_group, academic_class, category, purchase_price, selling_price, stock_quantity))
                        conn.commit()
                        st.success(f"Successfully added '{title}' for {academic_class} ({school_group})!")
                    except sqlite3.IntegrityError:
                        st.error(f"Error: A book with ISBN {isbn} already exists.")
                else:
                    st.warning("Please fill in at least the Title and ISBN.")
                    
    with tab2:
        st.subheader("Browse Inventory by School Group & Class")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_group = st.selectbox("Filter by School Group", ["All Groups"] + SCHOOL_GROUPS)
        with col_f2:
            filter_class = st.selectbox("Filter by Academic Class", ["All Classes"] + ACADEMIC_CLASSES)
        
        query = "SELECT id, isbn, title, author, school_group, academic_class, category, purchase_price, selling_price, stock_quantity FROM books WHERE 1=1"
        params = []
        
        if filter_group != "All Groups":
            query += " AND school_group = ?"
            params.append(filter_group)
        if filter_class != "All Classes":
            query += " AND academic_class = ?"
            params.append(filter_class)
            
        cursor.execute(query, params)
        books_data = cursor.fetchall()
        
        if books_data:
            df_books = pd.DataFrame(books_data, columns=["ID", "ISBN", "Title", "Author", "School Group", "Class", "Subject", "Purchase Price", "Selling Price", "Stock"])
            st.dataframe(df_books, use_container_width=True)
        else:
            st.info("No books found matching the selected school group and class filter.")

# --- 3. POINT OF SALE (POS) ---
elif choice == "Point of Sale (POS)":
    st.header("Billing & Sales Counter")
    
    pos_group = st.selectbox("Quick Filter POS by School Group", ["All Groups"] + SCHOOL_GROUPS, key="pos_grp")
    
    if pos_group == "All Groups":
        cursor.execute("SELECT id, title, isbn, selling_price, stock_quantity, academic_class FROM books WHERE stock_quantity > 0")
    else:
        cursor.execute("SELECT id, title, isbn, selling_price, stock_quantity, academic_class FROM books WHERE stock_quantity > 0 AND school_group = ?", (pos_group,))
        
    available_books = cursor.fetchall()
    
    if not available_books:
        st.warning("No books available in stock for the selected criteria.")
    else:
        book_dict = {f"[{b[5]}] {b[1]} (ISBN: {b[2]}) - Stock: {b[4]} - Rs. {b[3]}": b for b in available_books}
        
        customer_name = st.text_input("Customer Name", value="Walk-in Customer")
        selected_book_label = st.selectbox("Select Book", options=list(book_dict.keys()))
        
        selected_book = book_dict[selected_book_label]
        book_id, title, isbn, price, max_stock, acad_class = selected_book
        
        quantity = st.number_input("Quantity", min_value=1, max_value=max_stock, step=1)
        discount = st.number_input("Extra Discount (Rs.)", min_value=0.0, value=0.0, format="%.2f")
        
        calculated_total = (price * quantity) - discount
        st.info(f"Class: {acad_class} | Subtotal: Rs. {(price * quantity):,.2f} | Discount: Rs. {discount:,.2f} | **Final Payable: Rs. {calculated_total:,.2f}**")
        
        if st.button("Complete Sale & Print Bill"):
            invoice_no = f"RBD-{int(datetime.now().timestamp())}"
            sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO sales (invoice_number, sale_date, customer_name, total_amount)
                VALUES (?, ?, ?, ?)
            """, (invoice_no, sale_date, customer_name, calculated_total))
            sale_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO sale_items (sale_id, book_id, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, book_id, quantity, price, calculated_total))
            
            cursor.execute("""
                UPDATE books SET stock_quantity = stock_quantity - ? WHERE id = ?
            """, (quantity, book_id))
            
            conn.commit()
            st.success(f"Sale completed successfully! Invoice Number: {invoice_no}")
            
            receipt_text = f"""
            ========================================
                       RAJPUT BOOK DEPOT
               Main Bazaar / Bookstore Counter Bill
            ========================================
            Invoice No : {invoice_no}
            Date/Time  : {sale_date}
            Customer   : {customer_name}
            ----------------------------------------
            Class/Level: {acad_class}
            Item       : {title}
            ISBN       : {isbn}
            Qty Sold   : {quantity}
            Unit Price : Rs. {price:,.2f}
            Discount   : Rs. {discount:,.2f}
            ----------------------------------------
            TOTAL PAID : Rs. {calculated_total:,.2f}
            ========================================
               Thank You! Please Visit Again.
            ========================================
            """
            st.text_area("Generated Receipt (Copy or Print)", value=receipt_text, height=250)

# --- 4. PURCHASE STOCK ---
elif choice == "Purchase Stock":
    st.header("Purchase Stock from Supplier/Publisher")
    
    cursor.execute("SELECT id, title, isbn, school_group, academic_class FROM books")
    all_books = cursor.fetchall()
    
    if not all_books:
        st.warning("Please add books to the inventory catalog before recording purchases.")
    else:
        book_dict_p = {f"[{b[4]} - {b[3]}] {b[1]} (ISBN: {b[2]})": b[0] for b in all_books}
        
        with st.form("purchase_form"):
            supplier_name = st.text_input("Supplier / Publisher Name")
            invoice_number = st.text_input("Supplier Bill / Invoice Number")
            selected_book_str = st.selectbox("Select Book", options=list(book_dict_p.keys()))
            purch_qty = st.number_input("Purchased Quantity", min_value=1, step=1)
            unit_cost = st.number_input("Unit Purchase Cost (Rs.)", min_value=0.0, format="%.2f")
            
            submit_purchase = st.form_submit_button("Record Purchase & Update Stock")
            
            if submit_purchase:
                book_id = book_dict_p[selected_book_str]
                purchase_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                total_cost = unit_cost * purch_qty
                
                cursor.execute("""
                    INSERT INTO purchases (invoice_number, purchase_date, supplier_name, total_amount)
                    VALUES (?, ?, ?, ?)
                """, (invoice_number, purchase_date, supplier_name, total_cost))
                
                cursor.execute("""
                    UPDATE books SET stock_quantity = stock_quantity + ?, purchase_price = ? WHERE id = ?
                """, (purch_qty, unit_cost, book_id))
                
                conn.commit()
                st.success(f"Stock updated successfully for {selected_book_str} (+{purch_qty} units).")

# --- 5. EXPENSE TRACKER ---
elif choice == "Expense Tracker":
    st.header("Shop Expense Management")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            exp_category = st.selectbox("Expense Category", ["Rent", "Electricity Bill", "Staff Salary", "Transport / Freight", "Packaging / Bags", "Miscellaneous"])
            exp_amount = st.number_input("Amount (Rs.)", min_value=0.0, format="%.2f")
        with col2:
            exp_desc = st.text_area("Expense Description / Notes")
            
        submit_exp = st.form_submit_button("Record Expense")
        if submit_exp:
            exp_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO expenses (expense_date, category, amount, description)
                VALUES (?, ?, ?, ?)
            """, (exp_date, exp_category, exp_amount, exp_desc))
            conn.commit()
            st.success("Expense recorded successfully!")
            
    st.subheader("Expense Log History")
    cursor.execute("SELECT id, expense_date, category, amount, description FROM expenses ORDER BY id DESC")
    expenses_data = cursor.fetchall()
    if expenses_data:
        df_exp = pd.DataFrame(expenses_data, columns=["ID", "Date", "Category", "Amount", "Description"])
        st.dataframe(df_exp, use_container_width=True)
    else:
        st.info("No expenses recorded yet.")

# --- 6. REPORTS & HISTORY ---
elif choice == "Reports & History":
    st.header("Comprehensive Business Records")
    
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["Sales History", "Purchase History", "Expense History"])
    
    with sub_tab1:
        cursor.execute("""
            SELECT s.invoice_number, s.sale_date, s.customer_name, b.title, b.academic_class, si.quantity, si.unit_price, s.total_amount
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN books b ON si.book_id = b.id
            ORDER BY s.id DESC
        """)
        sales_history = cursor.fetchall()
        if sales_history:
            df_sales = pd.DataFrame(sales_history, columns=["Invoice No", "Date & Time", "Customer", "Book Title", "Class", "Qty Sold", "Unit Price", "Total Amount"])
            st.dataframe(df_sales, use_container_width=True)
        else:
            st.info("No sales records found.")
            
    with sub_tab2:
        cursor.execute("SELECT id, invoice_number, purchase_date, supplier_name, total_amount FROM purchases ORDER BY id DESC")
        purch_history = cursor.fetchall()
        if purch_history:
            df_purch = pd.DataFrame(purch_history, columns=["ID", "Invoice No", "Date", "Supplier", "Total Cost"])
            st.dataframe(df_purch, use_container_width=True)
        else:
            st.info("No purchase records found.")
            
    with sub_tab3:
        cursor.execute("SELECT id, expense_date, category, amount, description FROM expenses ORDER BY id DESC")
        exp_history = cursor.fetchall()
        if exp_history:
            df_exp_rep = pd.DataFrame(exp_history, columns=["ID", "Date", "Category", "Amount", "Description"])
            st.dataframe(df_exp_rep, use_container_width=True)
        else:
            st.info("No expense records found.")
