import plotly.express as px
import streamlit as st

def show_charts(df):

    if not df.empty:

        col1, col2 = st.columns(2)

        with col1:

            pie = px.pie(
                df,
                names="Category",
                values="Amount",
                title="Expense Distribution"
            )

            st.plotly_chart(
                pie,
                use_container_width=True
            )

        with col2:

            bar = px.bar(
                df,
                x="Category",
                y="Amount",
                color="Category",
                title="Category Wise Expenses"
            )

            st.plotly_chart(
                bar,
                use_container_width=True
            )

        line = px.line(
            df,
            x="Date",
            y="Amount",
            title="Expense Trend",
            markers=True
        )

        st.plotly_chart(
            line,
            use_container_width=True
        )