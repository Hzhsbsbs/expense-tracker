import streamlit as st
import sqlite3
from datetime import datetime

# ---------------- DATABASE SETUP ----------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    amount REAL,
    type TEXT,
    description TEXT,
    date TEXT,
    month TEXT
)
""")

# Insert default accounts
for acc in ["Bank", "Cash"]:
    cursor.execute("INSERT OR IGNORE INTO accounts (name) VALUES (?)", (acc,))
conn.commit()


# ---------------- FUNCTIONS ----------------
def get_account_id(name):
    cursor.execute("SELECT id FROM accounts WHERE name=?", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def add_transaction(account, amount, desc, t_type):
    acc_id = get_account_id(account)
    now = datetime.now()
    month = now.strftime("%Y-%m")

    # Convert expense to negative
    if t_type == "Expense":
        amount = -abs(amount)

    cursor.execute("""
    INSERT INTO transactions (account_id, amount, type, description, date, month)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (acc_id, amount, t_type, desc, now.strftime("%Y-%m-%d"), month))

    conn.commit()


def get_balance(account):
    acc_id = get_account_id(account)
    month = datetime.now().strftime("%Y-%m")

    cursor.execute("""
    SELECT SUM(amount) FROM transactions
    WHERE account_id=? AND month=?
    """, (acc_id, month))

    result = cursor.fetchone()[0]
    return result if result else 0


def transfer(from_acc, to_acc, amount):
    if from_acc == to_acc:
        return False

    add_transaction(from_acc, amount, f"Transfer to {to_acc}", "Expense")
    add_transaction(to_acc, amount, f"Transfer from {from_acc}", "Income")
    return True


def get_transactions():
    cursor.execute("""
    SELECT t.date, a.name, t.amount, t.description, t.type
    FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    ORDER BY t.date DESC
    LIMIT 50
    """)
    return cursor.fetchall()


# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="centered")

st.title("💸 Expense Tracker")

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["➕ Add", "🔄 Transfer", "📊 Dashboard"])


# ---------------- ADD TRANSACTION ----------------
with tab1:
    st.subheader("Add Transaction")

    account = st.selectbox("Select Account", ["Bank", "Cash"])
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    t_type = st.selectbox("Type", ["Income", "Expense"])
    desc = st.text_input("Description")

    if st.button("Add Transaction"):
        if amount > 0:
            add_transaction(account, amount, desc, t_type)
            st.success("✅ Transaction Added")
        else:
            st.error("Enter a valid amount")


# ---------------- TRANSFER ----------------
with tab2:
    st.subheader("Transfer Money")

    col1, col2 = st.columns(2)

    with col1:
        from_acc = st.selectbox("From Account", ["Bank", "Cash"])

    with col2:
        to_acc = st.selectbox("To Account", ["Cash", "Bank"])

    amount = st.number_input("Transfer Amount", min_value=0.0, step=1.0)

    if st.button("Transfer"):
        if amount <= 0:
            st.error("Enter valid amount")
        elif from_acc == to_acc:
            st.error("Accounts must be different")
        else:
            transfer(from_acc, to_acc, amount)
            st.success("✅ Transfer Successful")


# ---------------- DASHBOARD ----------------
with tab3:
    st.subheader("Monthly Overview")

    bank_balance = get_balance("Bank")
    cash_balance = get_balance("Cash")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("🏦 Bank Balance", f"₹{bank_balance:.2f}")

    with col2:
        st.metric("💵 Cash Balance", f"₹{cash_balance:.2f}")

    st.divider()

    st.subheader("Recent Transactions")

    transactions = get_transactions()

    if transactions:
        for t in transactions:
            date, acc, amt, desc, t_type = t
            st.write(f"📅 {date} | {acc} | ₹{amt:.2f} | {desc} ({t_type})")
    else:
        st.info("No transactions yet")