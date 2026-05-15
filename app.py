import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF

from database import (
    load_data,
    save_data,
    init_db
)
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
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

# LOGIN
logged_in = login()
init_db()

if logged_in:

    st.title("💰 Finance Tracker Pro")
    st.markdown(
        "### Smart Expense Management Dashboard"
    )

    # USERNAME
    username = st.session_state.username

    # LOAD USER DATA
    df = load_data(username)

    # SIDEBAR
    st.sidebar.header("➕ Add Expense")

    # BUDGET
    budget = st.sidebar.number_input(
        "💰 Set Monthly Budget",
        min_value=0,
        value=10000
    )

    # AMOUNT
    amount = st.sidebar.number_input(
        "Amount",
        min_value=0
    )

    # CATEGORY SUGGESTIONS
    default_categories = [
        "Food",
        "Travel",
        "Shopping",
        "Bills",
        "Entertainment",
        "Medical",
        "Education",
        "Fuel",
        "Gym",
        "Investment"
    ]

    selected_category = st.sidebar.selectbox(
        "Choose Suggested Category",
        default_categories
    )

    custom_category = st.sidebar.text_input(
        "Or Enter Custom Category"
    )

    # FINAL CATEGORY
    category = (
        custom_category.strip()
        if custom_category.strip() != ""
        else selected_category
    )

    st.sidebar.caption(
        "💡 You can type your own category"
    )

    # DATE
    expense_date = st.sidebar.date_input(
        "Date",
        date.today()
    )

    # ADD EXPENSE
    if st.sidebar.button("Add Expense"):

        new_data = pd.DataFrame({
            "Amount": [amount],
            "Category": [category],
            "Date": [expense_date]
        })

        df = pd.concat(
            [df, new_data],
            ignore_index=True
        )

        save_data(df, username)

        st.success(
            "Expense Added Successfully ✅"
        )

        st.rerun()

    # METRICS
    total = (
        df["Amount"].sum()
        if not df.empty else 0
    )

    transactions = len(df)

    remaining_budget = budget - total

    top_category = (
        df.groupby("Category")["Amount"]
        .sum()
        .idxmax()
        if not df.empty else "None"
    )

    # DASHBOARD CARDS
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "💵 Total Expense",
        f"₹{total}"
    )

    col2.metric(
        "📂 Top Category",
        top_category
    )

    col3.metric(
        "🧾 Transactions",
        transactions
    )

    col4.metric(
        "💳 Remaining Budget",
        f"₹{remaining_budget}"
    )

    # BUDGET ALERTS
    if total > budget:

        st.error(
            "⚠ You have exceeded your monthly budget!"
        )

    elif total > budget * 0.8:

        st.warning(
            "⚠ You have used more than 80% of your budget."
        )

    else:

        st.success(
            "✅ Budget is under control."
        )

    st.divider()

    # SEARCH & FILTER
    st.subheader(
        "🔍 Search & Filter Expenses"
    )

    search_category = st.text_input(
        "Search Category"
    )

    min_amount, max_amount = st.slider(
        "Filter By Amount Range",
        0,
        100000,
        (0, 100000)
    )

    filter_date = st.date_input(
        "Filter By Date",
        value=None
    )

    # FILTERED DATA
    filtered_df = df.copy()

    # CATEGORY FILTER
    if search_category:

        filtered_df = filtered_df[
            filtered_df["Category"]
            .astype(str)
            .str.contains(
                search_category,
                case=False,
                na=False
            )
        ]

    # AMOUNT FILTER
    filtered_df = filtered_df[
        (filtered_df["Amount"] >= min_amount)
        &
        (filtered_df["Amount"] <= max_amount)
    ]

    # DATE FILTER
    if filter_date:

        filtered_df = filtered_df[
            filtered_df["Date"].astype(str)
            ==
            str(filter_date)
        ]

    st.divider()

    # EXPENSE TABLE
    st.subheader("📋 Expense Records")

    if not filtered_df.empty:

        for index, row in filtered_df.iterrows():

            col1, col2, col3, col4, col5 = st.columns(5)

            col1.write(
                f"₹{row['Amount']}"
            )

            col2.write(
                row["Category"]
            )

            col3.write(
                row["Date"]
            )

            # DELETE BUTTON
            if col4.button(
                "🗑 Delete",
                key=f"delete_{index}"
            ):

                df = df.drop(index)

                save_data(df, username)

                st.rerun()

            # EDIT BUTTON
            if col5.button(
                "✏ Edit",
                key=f"edit_{index}"
            ):

                st.session_state.edit_index = index

        # EDIT SECTION
        if "edit_index" in st.session_state:

            edit_index = st.session_state.edit_index

            st.subheader(
                "✏ Edit Expense"
            )

            new_amount = st.number_input(
                "New Amount",
                value=int(
                    df.loc[
                        edit_index,
                        "Amount"
                    ]
                )
            )

            new_category = st.text_input(
                "New Category",
                value=str(
                    df.loc[
                        edit_index,
                        "Category"
                    ]
                )
            )

            if st.button(
                "Update Expense"
            ):

                df.loc[
                    edit_index,
                    "Amount"
                ] = new_amount

                df.loc[
                    edit_index,
                    "Category"
                ] = new_category

                save_data(df, username)

                del st.session_state.edit_index

                st.success(
                    "Expense Updated Successfully ✅"
                )

                st.rerun()

    else:

        st.info(
            "No matching expenses found."
        )

    st.divider()

    # CHARTS
    st.subheader(
        "📊 Expense Analytics"
    )

    show_charts(filtered_df)

    st.divider()

    # DOWNLOAD REPORTS
    st.subheader(
        "📥 Download Reports"
    )

    # CSV DOWNLOAD
    csv = filtered_df.to_csv(
        index=False
    )

    st.download_button(
        label="📄 Download CSV Report",
        data=csv,
        file_name="expense_report.csv",
        mime="text/csv"
    )

    # PDF FUNCTION
from fpdf import FPDF
import io

def create_pdf(dataframe):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Finance Tracker Report", ln=True, align="C")
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

    # IMPORTANT FIX → convert to bytes
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    return pdf_bytes