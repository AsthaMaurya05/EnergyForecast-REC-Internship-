import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
import bcrypt
import json
import os   
from datetime import datetime



def load_user_db():
    if os.path.exists("users.json"):
        try:
            with open("users.json", "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}  # Return empty if JSON is invalid
    else:
        return {}

def save_user_db(user_db):
    with open("users.json", "w") as file:
        json.dump(user_db, file,indent = 4)  


def record_login(username):
    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {"username": username, "login_time": login_time}

    log_file = "login_logs.json"

    # Load existing logins
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    # Append new login
    data.append(log_entry)

    # Save back to file
    with open(log_file, "w") as file:
        json.dump(data, file, indent=4)
          

# --- Persistent History Load/Save ---
def load_forecast_history(username):
    path = f"user_history_{username}.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []


def save_forecast_history(history, username):
    with open(f"user_history_{username}.json", "w") as file:
        json.dump(history, file, indent = 4)

CURRENT_USER_FILE = "current_user.json"


# --- Session State Initialization ---

if "user_db" not in st.session_state:
    st.session_state.user_db = load_user_db()

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "show_signup" not in st.session_state:
    st.session_state.show_signup = False




# Load forecast history once the user is logged in
if st.session_state.logged_in and "forecast_history" not in st.session_state:
    st.session_state.forecast_history = load_forecast_history(st.session_state.current_user)


# --- Helper functions ---
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- Sign Up Page ---
def signup_page():
    st.title("📝 Sign Up")

    new_username = st.text_input("Create a username")
    new_password = st.text_input("Create a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")

    if st.button("Sign Up"):
        if new_username in st.session_state.user_db:
            st.warning("Username already exists. Please login.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_username.strip()) < 3 or len(new_password.strip()) < 4:
            st.error("Username or password too short.")
        else:
            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            st.session_state.user_db[new_username] = hashed_pw

            save_user_db(st.session_state.user_db)  # 💾 Save updated user DB
            st.success("✅ Account created successfully. Please login.")
            st.session_state.show_signup = False
            st.rerun()

    if st.button("⬅️ Back to Login"):
        st.session_state.show_signup = False
        st.rerun()


# --- Login Page ---
def login_page():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    login_clicked = st.button("Login")
    signup_clicked = st.button("Go to Sign Up")

    if login_clicked:
        if username in st.session_state.user_db:
            hashed = st.session_state.user_db[username]
            if check_password(password, hashed):
                st.success("Login successful ✅")
                st.session_state.logged_in = True
                st.session_state.current_user = username
                

                # Record the login with time
                record_login(username)
    
                with open(CURRENT_USER_FILE, "w") as f:
                    json.dump({"username": username}, f)

                st.rerun()

            else:
                st.error("Incorrect password ❌")
        else:
            st.warning("Username not found.")

    if signup_clicked:
        st.session_state.show_signup = True
        st.rerun()

# --- Main App (After Login) ---
def main_app():
    st.set_page_config(page_title="Energy Forecast Dashboard", page_icon="🔌", layout="wide")
    st.title("⚡ Energy Forecast Dashboard")
    st.success(f"Welcome, {st.session_state.current_user}!")

    df = pd.read_csv("data/All_states (version 1).csv")

    df['Month'] = pd.to_datetime(df['Month'])

      # Sidebar Filters
    st.sidebar.title("Power Consumption Forecast")
    selected_reg = st.sidebar.selectbox("🌍 Select Region", sorted(df['Region'].dropna().unique()))
    # selected_reg = st.sidebar.selectbox("🌍 Select Region", options=sorted(df['Region'].unique()), index=0, key="selected_reg")
    filter_states = df[df['Region'] == selected_reg]['State'].dropna().unique()
    selected_state = st.sidebar.selectbox("🏙️ Select State", sorted(filter_states))
    # selected_state = st.sidebar.selectbox("📌 Select State", options=sorted(df[df["Region"] == st.session_state.selected_reg]["State"].unique()), key="selected_state")
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    # Forecast period slider 
    forecast_months = st.slider("📅 Select forecast period (months):", min_value=3, max_value=12, value=6) 

    # ⏺️ Log current forecast selection automatically (no button)
    new_entry = {"region": selected_reg, "state": selected_state}
    if new_entry not in st.session_state.forecast_history:
        st.session_state.forecast_history.append(new_entry)
        save_forecast_history(st.session_state.forecast_history, st.session_state.current_user)
            
    st.sidebar.markdown("## 📄 Forecast History")

    if st.session_state.forecast_history:
        for item in reversed(st.session_state.forecast_history):
            st.sidebar.markdown(f"- {item['region']} - {item['state']}")
    else:
        st.sidebar.caption("No forecast history yet.")
        



    # Energy Met Lineplot
    def plot_energy_met(df, state):
        state_data = df[df['State'] == state]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(state_data['Month'], state_data['Energy met'], marker='o', color='teal')
        ax.set_title(f'Energy Met Over Time - {state}')
        ax.set_xlabel('Month')
        ax.set_ylabel('Energy Met (MU)')
        ax.grid(True)
        st.pyplot(fig)
           
        st.markdown("""
    <h4 style='font-size:18px; margin-bottom: 5px;'>📌 What this shows:</h4>
    <p style='font-size:16px; color:#333;'>This line graph shows the actual monthly electricity <b>supplied to the selected state</b> over time, measured in Million Units (MU).<br>
    An upward trend means growing power delivery; a downward trend may indicate reduced supply or lower demand.</p>
    """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    # Requirement vs Met
    def plot_requirement_vs_met(df, state):
        state_data = df[df['State'] == state]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(state_data['Month'], state_data['Energy Requirement'], marker='o', label='Requirement', color='orange')
        ax.plot(state_data['Month'], state_data['Energy met'], marker='o', label='Met', color='green')
        ax.set_title(f'Energy Requirement vs Met - {state}')
        ax.set_xlabel('Month')
        ax.set_ylabel('Energy (Million Units)')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
        
        st.markdown("""
    <h4 style='font-size:18px; margin-bottom: 5px;'>📌 What this shows:</h4>
    <p style='font-size:16px; color:#333;'>The <b>orange line</b> represents the total electricity required by the state each month.<br>
    The <b>green line</b> shows how much was actually supplied (met).<br>
    If the green line consistently falls below the orange, it indicates an <b>energy deficit</b> in meeting demand.</p>
    """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    # Deficit Trend
    def plot_deficit_trend(df, state):
        state_data = df[df['State'] == state].copy()
        state_data['Deficit'] = state_data['Energy Requirement'] - state_data['Energy met']
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(state_data['Month'], state_data['Deficit'], marker='o', color='red')
        ax.set_title(f'Deficit Trend - {state}')
        ax.set_xlabel('Month')
        ax.set_ylabel('Deficit (MU)')
        ax.grid(True)
        st.pyplot(fig)
            
        
        st.markdown("""
    <h4 style='font-size:18px; margin-bottom: 8px;'>📌 What this shows:</h4>
    <p style='font-size:16px; color:#333;'>
    This graph shows the monthly <b>energy shortfall</b> in the state — calculated as:<br>
    Deficit = Energy Requirement - Energy Met<br>
    </p>

    <ul style='font-size:16px; color:#333;'>
    <li>If the line stays near zero, it means the supply has been meeting demand well.</li>
    </ul>
    """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    # Prophet Forecast
    def prophet_forecast(df, state, periods=6):
        state_data = df[df['State'] == state][['Month', 'Energy met']].copy()
        state_data.rename(columns={'Month': 'ds', 'Energy met': 'y'}, inplace=True)
        m = Prophet()
        m.fit(state_data)
        future = m.make_future_dataframe(periods=periods, freq='M')
        forecast = m.predict(future)
        return forecast, state_data

    
    
    # Clean Actual vs Forecast Plot
    def plot_actual_vs_forecast_clean(df, forecast_df, state):
        state_data = df[df['State'] == state][['Month', 'Energy met']].copy()
        last_date = state_data['Month'].max()
        future_forecast = forecast_df[forecast_df['ds'] > last_date]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(state_data['Month'], state_data['Energy met'], marker='o', label='Actual', color='teal')
        ax.plot(future_forecast['ds'], future_forecast['yhat'], marker='o', label='Forecast', color='orange')
        ax.fill_between(future_forecast['ds'], future_forecast['yhat_lower'], future_forecast['yhat_upper'], color='orange', alpha=0.2)
        ax.axvline(x=last_date, color='black', linestyle='--', label='Forecast Start')
        ax.set_title(f'Actual vs {forecast_months}-Month Forecast - {state}')
        ax.set_xlabel('Month')
        ax.set_ylabel('Energy (MU)')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
        st.caption("🟠 Shaded region shows 80% confidence interval for future predictions.")
        
        st.markdown("""
                    
    <h4 style='font-size:18px; margin-bottom: 5px;'>📌 What this shows:</h4>
    <p style='font-size:16px; color:#333;'>
    - The <b>blue line</b> represents actual electricity supplied in the past.<br>
    - The <b>orange line</b> is the </b>forecasted energy supply</b> for the furtue months.<br>
    - The <b>shaded orange area</b> is the model’s <b>confidence interval</b> — a range within which future values are likely to fall.<br>
    This helps stakeholders plan for expected changes in power consumption.</p>
    """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    # Forecast Data Table
    def show_forecast_table(forecast_df, df):
        last_date = df['Month'].max()
        future_forecast = forecast_df[forecast_df['ds'] > last_date].copy()
        future_forecast['Month'] = future_forecast['ds'].dt.strftime('%B %Y')

        # Rename columns for user-friendly display
        display_df = future_forecast.rename(columns={
            'yhat': 'Forecasted Energy Met (MU)',
            'yhat_lower': 'Lower Estimate (MU)',
            'yhat_upper': 'Upper Estimate (MU)'
        })

        st.subheader(f"📋 Next {forecast_months}-Month Forecast Table")
        st.dataframe(display_df[['Month', 'Forecasted Energy Met (MU)', 'Lower Estimate (MU)', 'Upper Estimate (MU)']].round(2))
     
        st.markdown("""
    <h4 style='font-size:18px; margin-bottom: 5px;'>📌 Table explanation:</h4>
    <p style='font-size:16px; color:#333;'>
    -This table shows the <b>forecasted electricity supply (Energy Met)</b> for the next selected months.<br>
    - The <b>lower and upper estimates</b> define the uncertainty range, which means actual values may vary slightly within this band.</p>
    """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    # Text Summary of Forecast
    def forecast_summary(forecast_df, state_data):
        last_date = state_data['ds'].max()
        future_data = forecast_df[forecast_df['ds'] > last_date]
        #  Picks the last row of the future forecast 
        latest = future_data.iloc[-1]
        
        #  Gets the latest actual Energy Met value from historical data (last value of y).
        start_val = state_data['y'].iloc[-1]
        
        #  Gets the predicted Energy Met value for the last forecasted month (yhat is Prophet’s prediction column).
        end_val = latest['yhat']
        
        # Calculates percentage change between forecasted value and last actual value.
        growth = ((end_val - start_val) / start_val) * 100

        st.markdown(f"""
        ### 📢 Forecast Summary for **{selected_state}**:
        - Current Energy Met: **{start_val:.2f} MU**
        - Expected in {forecast_months} months: **{end_val:.2f} MU**
        - 📈 Forecast shows a **{growth:+.1f}%** change in energy met
        """) 

        if growth > 10:
            st.info("⚡️ Energy demand is forecasted to **increase significantly**. Planning needed!")
        elif growth < -10:
            st.warning("📉 Energy demand may **decrease**, possibly due to seasonal or economic factors.")
        else:
            st.success("✅ Energy demand is expected to stay relatively **stable**.")

    # Export CSV Utility 
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    # Run all components
    plot_energy_met(df, selected_state)
    plot_requirement_vs_met(df, selected_state)
    plot_deficit_trend(df, selected_state)


    forecast_df, state_data = prophet_forecast(df, selected_state, periods=forecast_months)
    plot_actual_vs_forecast_clean(df, forecast_df, selected_state)
    show_forecast_table(forecast_df, df[df['State'] == selected_state])
    forecast_summary(forecast_df, state_data)


    # Download Button
    # Extracts only relevant columns from forecasted DataFrame.

    # Converts that into a downloadable CSV using convert_df.
    # Creates a button on the Streamlit app

    # When clicked, it downloads the forecast CSV (containing columns: ds, yhat, yhat_lower, yhat_upper)
    # Filename will be like: Uttar Pradesh_forecast.csv

    # Filter only future forecast
    future_forecast = forecast_df[forecast_df['ds'] > df['Month'].max()].copy()

    # Rename columns for clarity
    future_forecast.rename(columns={
        'ds': 'Month',
        'yhat': 'Forecasted Energy Met (MU)',
        'yhat_lower': 'Lower Estimate (MU)',
        'yhat_upper': 'Upper Estimate (MU)'
    }, inplace=True)

    # Convert to CSV
    # csv = convert_df(future_forecast[['Month', 'Forecasted Energy Met (MU)', 'Lower Estimate (MU)', 'Upper Estimate (MU)']])
    # Download button
    # st.download_button(
    #     label="📥 Download Forecast as CSV",
    #     data=csv,
    #     file_name=f"{selected_state}_forecast.csv",
    #     mime='text/csv',
    # )

    # Explanatory Note
    with st.expander("ℹ️ What Do These Terms Mean?"):
        st.markdown("""
        **Energy Met** = Electricity actually supplied to the state.  
        **Energy Requirement** = Total demand for electricity.  
        **Forecast** = AI-predicted value based on historical trends using Facebook Prophet. 
        **MU** = Million Units 
        """)

    # footer
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
   
    st.markdown("""
    ---
    📊 **Data Source**: Grid India  """
    )
    st.success("✅ Dashboard Loaded Successfully")
    # Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""

        # Delete user session file
        if os.path.exists(CURRENT_USER_FILE):
            os.remove(CURRENT_USER_FILE) 

        st.rerun()



# --- Routing ---

if not st.session_state.logged_in:
    if st.session_state.show_signup:
        signup_page()
    else:
        login_page()
else:
    main_app()
