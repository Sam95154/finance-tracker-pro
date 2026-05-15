import streamlit as st
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF

from database import load_data, save_data, init_db
from analytics import show_charts
from auth import login

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Finance Tracker Pro",
    page_icon="💰",
    layout="wide"
)

# ================= LOAD CSS =================
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ================= INIT DB =================
init_db()

# ================= LOGIN =================
logged_in = login()

# ================= SAFE TEXT FUNCTION =================
def clean(text):
    return str(text).encode("ascii", "ignore").decode()

# ================= PDF FUNCTION =================
def create_pdf(dataframe, username="User", budget=0):

    pdf = FPDF()
    pdf.add_page()

    # HEADER
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "BANK STATEMENT REPORT", ln=True, align="C")

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, clean(f"Account Holder: {username}"), ln=True, align="C")
    pdf.cell(0, 8, clean(f"Generated On: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"), ln=True, align="C")

    pdf.ln(10)

    # SUMMARY
    total = dataframe["Amount"].sum() if not dataframe.empty else 0
    transactions = len(dataframe)
    remaining = budget - total

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Account Summary", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, clean(f"Total Transactions: {transactions}"), ln=True)
    pdf.cell(0, 6, clean(f"Total Spent: INR {total}"), ln=True)
    pdf.cell(0, 6, clean(f"Budget Limit: INR {budget}"), ln=True)
    pdf.cell(0, 6, clean(f"Remaining Balance: INR {remaining}"), ln=True)

    pdf.ln(8)

    # TABLE HEADER
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(220, 220, 220)

    pdf.cell(40, 10, "Amount", 1, 0, "C", True)
    pdf.cell(80, 10, "Category", 1, 0, "C", True)
    pdf.cell(60, 10, "Date", 1, 1, "C", True)

    # TABLE DATA
    pdf.set_font("Arial", "", 10)

    for _, row in dataframe.iterrows():
        pdf.cell(40, 8, clean(f"INR {row['Amount']}"), 1, 0, "C")
        pdf.cell(80, 8, clean(row["Category"]), 1, 0, "C")
        pdf.cell(60, 8, clean(str(row["Date"])), 1, 1, "C")

    pdf.ln(5)

    # FOOTER
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 10, "System Generated Statement", ln=True, align="C")

    return pdf.output(dest="S").encode("latin-1")


# ================= MAIN APP =================
if logged_in:

    st.title("💰 Finance Tracker Pro")
    st.markdown("### Smart Expense Management Dashboard")

    username = st.session_state.username
    df = load_data(username)

    # ================= SIDEBAR =================
    st.sidebar.header("➕ Add Expense")

    budget = st.sidebar.number_input("💰 Monthly Budget", min_value=0, value=10000)
    amount = st.sidebar.number_input("Amount", min_value=0)

    categories = [
        "Food", "Travel", "Shopping", "Bills",
        "Entertainment", "Medical", "Education",
        "Fuel", "Gym", "Investment"
    ]

    selected_category = st.sidebar.selectbox("Choose Category", categories)
    custom_category = st.sidebar.text_input("Or Enter Custom Category")

    category = custom_category.strip() if custom_category.strip() != "" else selected_category

    expense_date = st.sidebar.date_input("Date", date.today())

    if st.sidebar.button("Add Expense"):
        new_data = pd.DataFrame({
            "Amount": [amount],
            "Category": [category],
            "Date": [expense_date]
        })

        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df, username)

        st.success("Expense Added Successfully ✅")
        st.rerun()

    # ================= METRICS =================
    total = df["Amount"].sum() if not df.empty else 0
    transactions = len(df)
    remaining = budget - total

    top_category = df.groupby("Category")["Amount"].sum().idxmax() if not df.empty else "None"

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("💵 Total Expense", f"INR {total}")
    c2.metric("📂 Top Category", top_category)
    c3.metric("🧾 Transactions", transactions)
    c4.metric("💳 Remaining Budget", f"INR {remaining}")

    if total > budget:
        st.error("⚠ Budget Exceeded!")
    elif total > budget * 0.8:
        st.warning("⚠ 80% Budget Used")
    else:
        st.success("✅ Budget OK")

    st.divider()

    # ================= FILTER =================
    st.subheader("🔍 Search & Filter")

    search = st.text_input("Search Category")
    min_amt, max_amt = st.slider("Amount Range", 0, 100000, (0, 100000))
    filter_date = st.date_input("Filter Date")

    filtered_df = df.copy()

    if search:
        filtered_df = filtered_df[
            filtered_df["Category"].astype(str).str.contains(search, case=False)
        ]

    filtered_df = filtered_df[
        (filtered_df["Amount"] >= min_amt) &
        (filtered_df["Amount"] <= max_amt)
    ]

    filtered_df = filtered_df[
        filtered_df["Date"].astype(str) == str(filter_date)
    ]

    st.divider()

    # ================= TABLE =================
    st.subheader("📋 Expenses")

    if not filtered_df.empty:

        for i, row in filtered_df.iterrows():
            c1, c2, c3, c4, c5 = st.columns(5)

            c1.write(f"INR {row['Amount']}")
            c2.write(row["Category"])
            c3.write(row["Date"])

            if c4.button("🗑 Delete", key=f"del_{i}"):
                df = df.drop(i)
                save_data(df, username)
                st.rerun()

            if c5.button("✏ Edit", key=f"edit_{i}"):
                st.session_state.edit_index = i

    else:
        st.info("No data found")

    # ================= EDIT =================
    if "edit_index" in st.session_state:

        idx = st.session_state.edit_index

        st.subheader("✏ Edit Expense")

        new_amt = st.number_input("Amount", value=int(df.loc[idx, "Amount"]))
        new_cat = st.text_input("Category", value=str(df.loc[idx, "Category"]))

        if st.button("Update"):
            df.loc[idx, "Amount"] = new_amt
            df.loc[idx, "Category"] = new_cat

            save_data(df, username)

            del st.session_state.edit_index
            st.success("Updated ✅")
            st.rerun()

    st.divider()

    # ================= ANALYTICS =================
    st.subheader("📊 Analytics")
    show_charts(filtered_df)

    st.divider()

    # ================= CSV DOWNLOAD =================
    csv = filtered_df.to_csv(index=False)

    st.download_button(
        "📄 Download CSV",
        csv,
        "expense.csv",
        "text/csv"
    )

    # ================= PDF DOWNLOAD =================
    pdf_file = create_pdf(filtered_df, username=username, budget=budget)

    st.download_button(
        "📑 Download Bank Statement PDF",
        data=pdf_file,
        file_name="bank_statement.pdf",
        mime="application/pdf"
    )