import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF

from database import load_data, save_data, init_db
from analytics import show_charts
from auth import login

# PAGE CONFIG
st.set_page_config(
    page_title="Finance Tracker Pro",
    page_icon="💰",
    layout="wide"
)

# LOAD CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# INIT DB
init_db()

# LOGIN
logged_in = login()

if logged_in:

    st.title("💰 Finance Tracker Pro")
    st.markdown("### Smart Expense Management Dashboard")

    username = st.session_state.username
    df = load_data(username)

    # ================= SIDEBAR =================
    st.sidebar.header("➕ Add Expense")

    budget = st.sidebar.number_input("💰 Monthly Budget", min_value=0, value=10000)
    amount = st.sidebar.number_input("Amount", min_value=0)

    default_categories = [
        "Food", "Travel", "Shopping", "Bills",
        "Entertainment", "Medical", "Education",
        "Fuel", "Gym", "Investment"
    ]

    selected_category = st.sidebar.selectbox("Choose Category", default_categories)
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

    top_category = (
        df.groupby("Category")["Amount"].sum().idxmax()
        if not df.empty else "None"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💵 Total Expense", f"₹{total}")
    col2.metric("📂 Top Category", top_category)
    col3.metric("🧾 Transactions", transactions)
    col4.metric("💳 Remaining Budget", f"₹{remaining}")

    if total > budget:
        st.error("⚠ Budget Exceeded!")
    elif total > budget * 0.8:
        st.warning("⚠ 80% Budget Used")
    else:
        st.success("✅ Budget OK")

    st.divider()

    # ================= SEARCH FILTER =================
    st.subheader("🔍 Search & Filter")

    search = st.text_input("Search Category")

    min_amt, max_amt = st.slider(
        "Amount Range", 0, 100000, (0, 100000)
    )

    filter_date = st.date_input("Filter Date", value=None)

    filtered_df = df.copy()

    if search:
        filtered_df = filtered_df[
            filtered_df["Category"].astype(str).str.contains(search, case=False)
        ]

    filtered_df = filtered_df[
        (filtered_df["Amount"] >= min_amt) &
        (filtered_df["Amount"] <= max_amt)
    ]

    if filter_date:
        filtered_df = filtered_df[
            filtered_df["Date"].astype(str) == str(filter_date)
        ]

    st.divider()

    # ================= TABLE =================
    st.subheader("📋 Expenses")

    if not filtered_df.empty:

        for i, row in filtered_df.iterrows():
            c1, c2, c3, c4, c5 = st.columns(5)

            c1.write(f"₹{row['Amount']}")
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

        new_amt = st.number_input(
            "Amount",
            value=int(df.loc[idx, "Amount"])
        )

        new_cat = st.text_input(
            "Category",
            value=str(df.loc[idx, "Category"])
        )

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

    # ================= DOWNLOAD CSV =================
    csv = filtered_df.to_csv(index=False)

    st.download_button(
        "📄 Download CSV",
        csv,
        "expense.csv",
        "text/csv"
    )

    # ================= FIXED PDF FUNCTION =================
    def create_pdf(dataframe):

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, "Finance Tracker Report", ln=True, align="C")
        pdf.ln(10)

        pdf.cell(40, 10, "Amount", 1)
        pdf.cell(70, 10, "Category", 1)
        pdf.cell(60, 10, "Date", 1)
        pdf.ln()

        for _, row in dataframe.iterrows():
            pdf.cell(40, 10, str(row["Amount"]), 1)
            pdf.cell(70, 10, str(row["Category"]), 1)
            pdf.cell(60, 10, str(row["Date"]), 1)
            pdf.ln()

        # ✅ IMPORTANT FIX (NO ERROR IN STREAMLIT CLOUD)
        pdf_output = pdf.output(dest="S")

        if isinstance(pdf_output, str):
            pdf_output = pdf_output.encode("latin-1")

        return pdf_output

    # ================= PDF DOWNLOAD =================
    pdf_file = create_pdf(filtered_df)

    st.download_button(
        "📑 Download PDF",
        data=pdf_file,
        file_name="expense_report.pdf",
        mime="application/pdf"
    )