import streamlit as st

def login():

    st.sidebar.title("🔐 Login")

    username = st.sidebar.text_input(
        "Username"
    )

    password = st.sidebar.text_input(
        "Password",
        type="password"
    )

    users = {
        "sameer": "sameer123",
        "admin": "admin123",
        "guest": "guest123",
        "fahad": "fahad123",
    }

    if username in users and users[username] == password:

        st.session_state.username = username

        st.sidebar.success(
            f"Welcome {username} ✅"
        )

        return True

    else:

        st.sidebar.warning(
            "Enter Correct Credentials"
        )

        return False