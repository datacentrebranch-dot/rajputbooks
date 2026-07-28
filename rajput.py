import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- STREAMLIT UI CONFIGURATION ---
st.set_page_config(page_title="Rajput Book Depot", page_icon="📚", layout="wide")

# --- CUSTOM CSS FOR SIDEBAR & STYLING ---
st.markdown("""
    <style>
        /* Force centering on all image containers inside the sidebar */
        [data-testid="stSidebar"] [data-testid="stImage"] {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0 auto;
        }
        [data-testid="stSidebar"] img {
            display: block;
            margin-left: auto;
            margin-right: auto;
            border-radius: 50%;
        }
    </style>
""", unsafe_allow_html=True)

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
            school_group TEXT,
            academic_class TEXT,
            category TEXT,
            purchase_price REAL,
            selling_price REAL,
            stock_quantity INTEGER
        )
    """)
    
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
    
    # Users Table for Login Management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "Administrator"))
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("cashier", "cashier123", "Cashier"))
        conn.commit()

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

# --- SESSION STATE MANAGEMENT FOR AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        # Perfectly centering the logo by using identical column weights inside the container layout
        img_col1, img_col2, img_col3 = st.columns([1.3, 2, 1.3])
        with img_col2:
            try:
                st.image("logo.png", width=180)
            except Exception:
                st.title("📚")
        
        st.markdown("<h2 style='text-align: center; margin-top: 0px;'>🔒 Welcome to Rajput Books</h2>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username_input = st.text_input("Username").strip()
            password_input = st.text_input("Password", type="password").strip()
            submit_login = st.form_submit_button("Login to System", use_container_width=True)
            
            if submit_login:
                cursor.execute("SELECT role FROM users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?)) AND TRIM(password) = TRIM(?)", (username_input, password_input))
                user_record = cursor.fetchone()
                if user_record:
                    st.session_state.authenticated = True
                    st.session_state.username = username_input
                    st.session_state.role = user_record[0]
                    st.success("Login successful! Loading application...")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. Please try again.")
        
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray; font-size: 14px;'>Powered By <b>Tahir Shafi +923008320000</b></div>", unsafe_allow_html=True)
    st.stop()

# --- APP HEADER BANNER ---
try:
    st.image("banner.png", use_container_width=True)
except Exception:
    st.title("📚 Rajput Book Depot")

# --- SIDEBAR LOGO & USER PROFILE (CENTERED VIA COLUMNS) ---
with st.sidebar:
    # Using symmetrical columns to center-align the logo natively in Streamlit layout
    col_empty1, col_logo, col_empty2 = st.columns([1, 2, 1])
    with col_logo:
        try:
            st.image("logo.png", width=130)
        except Exception:
            st.subheader("📚")

    st.markdown(f"<div style='text-align: center;'>👤 <b>{st.session_state.username}</b><br>🛡️ <code>{st.session_state.role}</code></div>", unsafe_allow_html=True)
    st.markdown("")

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

    st.markdown("---")
    st.markdown("### 🧭 Navigation Menu")

# --- SIDEBAR NAVIGATION BUTTONS ---
if "nav_choice" not in st.session_state:
    st.session_state.nav_choice = "Dashboard"

menu_items = {
    "Dashboard": "📊 Dashboard & Impact",
    "Inventory Management": "📚 Inventory Management",
    "Point of Sale (POS)": "🛒 Point of Sale (POS)",
    "Purchase Stock": "📦 Purchase Stock",
    "Expense Tracker": "💸 Expense Tracker",
    "Reports & History": "📈 Reports & History",
    "Data Migration": "⚡ Data Migration",
    "User Administration": "👥 User Administration"
}

for key, label in menu_items.items():
    btn_type = "primary" if st.session_state.nav_choice == key else "secondary"
    if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
        st.session_state.nav_choice = key
        st.rerun()

choice = st.session_state.nav_choice

# --- 1. DASHBOARD ---
if choice == "Dashboard":
    st.header("Store Financial & Impact Analysis Dashboard")
    
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
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Book Titles", f"{total_titles:,}")
    col2.metric("Total Units in Stock", f"{total_stock:,}")
    col3.metric("Inventory Asset Value", f"Rs. {total_value:,.2f}")
    col4.metric("Total Revenue", f"Rs. {total_revenue:,.2f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Total Purchases Outflow", f"Rs. {total_purchases:,.2f}")
    col6.metric("Total Shop Expenses", f"Rs. {total_expenses:,.2f}")
    col7.metric("Net Profit", f"Rs. {net_profit:,.2f}", delta=f"Rs. {net_profit:,.2f}")
    col8.metric("Net Profit Margin", f"{profit_margin:.2f}%")
    
    st.markdown("---")
    st.subheader("📊 Visual Impact & Financial Breakdown")
    
    tab_chart1, tab_chart2, tab_chart3 = st.tabs(["Financial Cashflow Impact", "Sales by School Group", "Stock Distribution by Category"])
    
    with tab_chart1:
        st.write("### Cashflow & Profitability Impact Breakdown")
        df_cashflow = pd.DataFrame({
            "Metric": ["Revenue Inflow", "Purchase Outflow", "Shop Expenses", "Net Profit"],
            "Amount (Rs.)": [total_revenue, total_purchases, total_expenses, net_profit]
        })
        st.bar_chart(df_cashflow.set_index("Metric"))
        
    with tab_chart2:
        st.write("### Sales Performance Across School Groups")
        cursor.execute("""
            SELECT b.school_group, SUM(si.subtotal) as revenue
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN books b ON si.book_id = b.id
            GROUP BY b.school_group
        """)
        group_sales = cursor.fetchall()
        if group_sales:
            df_group_sales = pd.DataFrame(group_sales, columns=["School Group", "Revenue"])
            st.bar_chart(df_group_sales.set_index("School Group"))
        else:
            st.info("No sales breakdown available by school group yet.")
            
    with tab_chart3:
        st.write("### Stock Distribution Volume by Subject Category")
        cursor.execute("SELECT category, SUM(stock_quantity) FROM books GROUP BY category")
        cat_data = cursor.fetchall()
        if cat_data:
            df_cat = pd.DataFrame(cat_data, columns=["Category", "Stock Quantity"])
            st.bar_chart(df_cat.set_index("Category"))
        else:
            st.info("No category data found.")

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
            Cashier    : {st.session_state.username}
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
    st.header("Supervisor Reports & Date-Filtered Analytics")
    
    report_type = st.selectbox("Select Supervisor Report", [
        "Sales & Revenue Summary", 
        "Class & School Group Sales Breakdown", 
        "Purchase Outflow Report", 
        "Expense Summary Report",
        "Comprehensive Financial Statement (P&L)"
    ])
    
    st.markdown("---")
    st.subheader("📅 Date Range Filters")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Start Date", value=pd.to_datetime("2026-01-01"))
    with col_d2:
        end_date = st.date_input("End Date", value=pd.to_datetime("2026-12-31"))
        
    start_str = start_date.strftime("%Y-%m-%d 00:00:00")
    end_str = end_date.strftime("%Y-%m-%d 23:59:59")
    
    if report_type == "Sales & Revenue Summary":
        st.subheader("Sales History & Revenue")
        cursor.execute("""
            SELECT s.invoice_number, s.sale_date, s.customer_name, b.title, b.school_group, b.academic_class, si.quantity, si.unit_price, s.total_amount
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN books b ON si.book_id = b.id
            WHERE s.sale_date BETWEEN ? AND ?
            ORDER BY s.id DESC
        """, (start_str, end_str))
        sales_history = cursor.fetchall()
        
        if sales_history:
            df_sales = pd.DataFrame(sales_history, columns=["Invoice No", "Date & Time", "Customer", "Book Title", "School Group", "Class", "Qty Sold", "Unit Price", "Total Amount"])
            st.dataframe(df_sales, use_container_width=True)
            total_rev_filtered = df_sales["Total Amount"].sum()
            st.metric("Total Revenue for Selected Period", f"Rs. {total_rev_filtered:,.2f}")
        else:
            st.info("No sales records found for the selected date range.")
            
    elif report_type == "Class & School Group Sales Breakdown":
        st.subheader("Sales Volume by Academic Class & Group")
        cursor.execute("""
            SELECT b.school_group, b.academic_class, SUM(si.quantity) as total_qty, SUM(si.subtotal) as total_sales
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN books b ON si.book_id = b.id
            WHERE s.sale_date BETWEEN ? AND ?
            GROUP BY b.school_group, b.academic_class
            ORDER BY total_sales DESC
        """, (start_str, end_str))
        breakdown_data = cursor.fetchall()
        
        if breakdown_data:
            df_breakdown = pd.DataFrame(breakdown_data, columns=["School Group", "Academic Class", "Total Units Sold", "Total Revenue"])
            st.dataframe(df_breakdown, use_container_width=True)
        else:
            st.info("No class-wise sales recorded within this date range.")
            
    elif report_type == "Purchase Outflow Report":
        st.subheader("Supplier Purchases & Stock Investment")
        cursor.execute("""
            SELECT id, invoice_number, purchase_date, supplier_name, total_amount
            FROM purchases
            WHERE purchase_date BETWEEN ? AND ?
            ORDER BY id DESC
        """, (start_str, end_str))
        purch_history = cursor.fetchall()
        
        if purch_history:
            df_purch = pd.DataFrame(purch_history, columns=["ID", "Invoice No", "Date", "Supplier", "Total Cost"])
            st.dataframe(df_purch, use_container_width=True)
            total_purch_filtered = df_purch["Total Cost"].sum()
            st.metric("Total Purchase Outflow for Selected Period", f"Rs. {total_purch_filtered:,.2f}")
        else:
            st.info("No purchase records found for the selected date range.")
            
    elif report_type == "Expense Summary Report":
        st.subheader("Shop Operational Expenses")
        cursor.execute("""
            SELECT id, expense_date, category, amount, description
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
            ORDER BY id DESC
        """, (start_str, end_str))
        exp_history = cursor.fetchall()
        
        if exp_history:
            df_exp = pd.DataFrame(exp_history, columns=["ID", "Date", "Category", "Amount", "Description"])
            st.dataframe(df_exp, use_container_width=True)
            total_exp_filtered = df_exp["Amount"].sum()
            st.metric("Total Expenses for Selected Period", f"Rs. {total_exp_filtered:,.2f}")
        else:
            st.info("No expense records found for the selected date range.")
            
    elif report_type == "Comprehensive Financial Statement (P&L)":
        st.subheader("Period Profit & Loss Statement")
        
        cursor.execute("SELECT SUM(total_amount) FROM sales WHERE sale_date BETWEEN ? AND ?", (start_str, end_str))
        rev_res = cursor.fetchone()[0]
        period_revenue = rev_res if rev_res else 0.0
        
        cursor.execute("SELECT SUM(total_amount) FROM purchases WHERE purchase_date BETWEEN ? AND ?", (start_str, end_str))
        purch_res = cursor.fetchone()[0]
        period_purchases = purch_res if purch_res else 0.0
        
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE expense_date BETWEEN ? AND ?", (start_str, end_str))
        exp_res = cursor.fetchone()[0]
        period_expenses = exp_res if exp_res else 0.0
        
        period_gross_profit = period_revenue - period_purchases
        period_net_profit = period_gross_profit - period_expenses
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric("Total Revenue Inflow", f"Rs. {period_revenue:,.2f}")
            st.metric("Total Purchase Outflow", f"Rs. {period_purchases:,.2f}")
        with col_p2:
            st.metric("Total Shop Expenses", f"Rs. {period_expenses:,.2f}")
            st.metric("Net Period Profit", f"Rs. {period_net_profit:,.2f}", delta=f"Rs. {period_net_profit:,.2f}")
            
        st.markdown("---")
        if period_net_profit >= 0:
            st.success("The business is operating at a net profit for this selected duration.")
        else:
            st.error("The business has a net deficit for this selected duration.")

# --- 7. DATA MIGRATION ---
elif choice == "Data Migration":
    st.header("Bulk Data Migration & Template Download")
    st.write("Download the template CSV file below, fill in your old software's inventory data according to the columns, and upload it back here to import everything instantly.")
    
    sample_data = [{
        "isbn": "978-969000001",
        "title": "Sample English Textbook",
        "author": "Publisher Name",
        "school_group": "Oxford / Cambridge System",
        "academic_class": "Class 1",
        "category": "Textbook",
        "purchase_price": 350.0,
        "selling_price": 450.0,
        "stock_quantity": 50
    }]
    df_template = pd.DataFrame(sample_data)
    
    csv_data = df_template.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download Inventory CSV Template",
        data=csv_data,
        file_name="rajput_book_depot_inventory_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.subheader("Upload Filled CSV / Excel File")
    uploaded_file = st.file_uploader("Upload your completed file (.csv or .xlsx)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
                
            st.write("Preview of Uploaded Data:")
            st.dataframe(df_upload.head(), use_container_width=True)
            
            if st.button("Confirm & Import Data into Database"):
                success_count = 0
                error_count = 0
                
                for _, row in df_upload.iterrows():
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO books (isbn, title, author, school_group, academic_class, category, purchase_price, selling_price, stock_quantity)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(row["isbn"]),
                            str(row["title"]),
                            str(row.get("author", "")),
                            str(row.get("school_group", "General / Public Board")),
                            str(row.get("academic_class", "Class 1")),
                            str(row.get("category", "Textbook")),
                            float(row.get("purchase_price", 0.0)),
                            float(row.get("selling_price", 0.0)),
                            int(row.get("stock_quantity", 0))
                        ))
                        if cursor.rowcount > 0:
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception:
                        error_count += 1
                        
                conn.commit()
                st.success(f"Migration completed! Successfully imported {success_count} books. (Skipped/Duplicates: {error_count})")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- 8. USER ADMINISTRATION ---
elif choice == "User Administration":
    st.header("👥 User Administration Panel")
    
    if st.session_state.role != "Administrator":
        st.error("Access Denied: You must be logged in as an Administrator to manage system users.")
    else:
        admin_tab1, admin_tab2, admin_tab3 = st.tabs(["List Existing Users", "Create New User", "Edit User & Modify Password"])
        
        with admin_tab1:
            st.subheader("Existing System Users")
            cursor.execute("SELECT id, username, role FROM users")
            users_list = cursor.fetchall()
            if users_list:
                df_users = pd.DataFrame(users_list, columns=["ID", "Username", "Role"])
                st.dataframe(df_users, use_container_width=True)
            else:
                st.info("No users found.")
                
        with admin_tab2:
            st.subheader("Create a New User Account")
            with st.form("create_user_form", clear_on_submit=True):
                new_username = st.text_input("New Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("User Role", ["Administrator", "Cashier"])
                submit_new_user = st.form_submit_button("Create User")
                
                if submit_new_user:
                    if new_username and new_password:
                        try:
                            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (new_username.strip(), new_password.strip(), new_role))
                            conn.commit()
                            st.success(f"User '{new_username.strip()}' created successfully with role '{new_role}'!")
                        except sqlite3.IntegrityError:
                            st.error(f"Username '{new_username}' already exists. Please choose a different username.")
                    else:
                        st.warning("Please enter both username and password.")
                        
        with admin_tab3:
            st.subheader("Edit User Role / Modify Password")
            cursor.execute("SELECT id, username, role FROM users")
            all_users = cursor.fetchall()
            
            if not all_users:
                st.info("No users available to edit.")
            else:
                user_dict = {u[1]: u for u in all_users}
                selected_edit_username = st.selectbox("Select User to Edit", options=list(user_dict.keys()), key="select_edit_user_box")
                
                selected_user_data = user_dict[selected_edit_username]
                u_id, u_name, u_role = selected_user_data
                
                with st.form("edit_user_form"):
                    edit_role = st.selectbox("Modify Role", ["Administrator", "Cashier"], index=0 if u_role=="Administrator" else 1, key="edit_role_box")
                    modify_password = st.text_input("New Password (Leave blank to keep unchanged)", type="password", key="edit_pass_box")
                    
                    submit_edit = st.form_submit_button("Update User Details")
                    
                    if submit_edit:
                        if modify_password.strip() != "":
                            cursor.execute("UPDATE users SET role = ?, password = ? WHERE id = ?", (edit_role, modify_password.strip(), u_id))
                            st.success(f"Successfully updated role and password for '{u_name}'!")
                        else:
                            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (edit_role, u_id))
                            st.success(f"Successfully updated role for '{u_name}'!")
                        conn.commit()
                        st.rerun()

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 14px;'>Powered By <b>Tahir Shafi +923008320000</b></div>", unsafe_allow_html=True)
