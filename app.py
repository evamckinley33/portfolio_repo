import streamlit as st
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CIBI",
    page_icon="💸",
    layout="centered"
)

# --- STYLING ---
st.markdown("""
    <style>
    .big-font { font-size:30px !important; font-weight: bold; }
    .verdict-box { padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center; }
    .green { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .yellow { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
    .red { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("Can I buy it?")
st.markdown("**Know Before You Buy**")

# --- SIDEBAR: USER PROFILE ---
with st.sidebar:
    st.header("1. Your Monthly Expenses")
    st.info("Fill this out first to get accurate advice!")
    
    monthly_income = st.number_input("Monthly Income (After Tax)", min_value=0, value=2500, step=100)
    
    st.subheader("Fixed Expenses")
    rent = st.number_input("Rent/Housing", min_value=0, value=800, step=50)
    utilities = st.number_input("Utilities/Wifi", min_value=0, value=100, step=50)
    groceries = st.number_input("Groceries", min_value=0, value=300, step=50)
    healthcare = st.number_input("Healthcare", min_value=0, value=50, step=10)
    personal_care = st.number_input("Personal Care", min_value=0, value=50, step=10)
    gym = groceries = st.number_input("Gym/Workout Classes", min_value=0, value=100, step=50)
    transit = st.number_input("Commuting Costs", min_value=0, value=50, step=50)
    loans = st.number_input("Student/Car Loan Payments", min_value=0, value=400, step=50)
    subscriptions = st.number_input("Streaming Subscriptions", min_value=0, value=50, step=10)
    other = st.number_input("Other Expenses", min_value=0, value=50, step=10)
    
    st.subheader("Variable Expenses")
    investments = st.number_input("Investments", min_value=0, value=50, step=10)
    takeout = st.number_input("Take-Out", min_value=0, value=100, step=50)
    drinks = st.number_input("Drinks", min_value=0, value=100, step=50)
    shopping = st.number_input("Shopping", min_value=0, value=200, step=50)
    entertainment = st.number_input("Entertainment", min_value=0, value=200, step=50)
    travel = st.number_input("Travel", min_value=0, value=400, step=50)
    other_2 = st.number_input("Other", min_value=0, value=50, step=10)
    
    current_savings = st.number_input("Emergency Fund", min_value=0, value=1000, step=100)

    # Calculation
    fixed_expenses = rent + utilities + groceries + healthcare + personal_care + gym + transit + loans + subscriptions + other
    discretionary_income = monthly_income - fixed_expenses
    variable_expenses = investments + takeout + drinks + shopping + entertainment + travel + other_2
    fun_money = discretionary_income - variable_expenses
    

    st.markdown("---")
    st.metric(label="Discretionary Income", value=f"${discretionary_income}", delta_color="normal")
    
    if discretionary_income < 0:
        st.error("⚠️ You are already spending more than you earn just on bills!")

    st.metric(label="Fun Money", value=f"${fun_money}", delta_color="normal")
    
    if fun_money < 0:
        st.error("⚠️ You are already spending more than you earn just on bills!")

# --- MAIN: THE PURCHASE ---
st.header("2. What are you thinking of buying?")

col1, col2 = st.columns(2)
with col1:
    item_name = st.text_input("Name of Item/Experience", placeholder="e.g., Concert Tickets")
with col2:
    item_cost = st.number_input("Total Cost ($)", min_value=0.0, value=100.0, step=10.0)

# --- LOGIC & QUESTIONNAIRE ---
if item_name and item_cost > 0:
    st.markdown("---")
    st.header("3. The Vibe Check")
    
    col_q1, col_q2 = st.columns(2)
    
    with col_q1:
        is_need = st.radio("Is this a WANT or a NEED?", ["Want (Be honest)", "Need (Survival/Work requirement)"])
        time_waited = st.radio("How long have you wanted this?", ["Just saw it (Impulse)", "24+ Hours", "1+ Month", "1+ Year"])
    
    with col_q2:
        peer_pressure = st.checkbox("Is this largely because friends are doing it?")
        debt_funding = st.checkbox("Will you put this on a Credit Card you can't pay off immediately?")

    # --- CALCULATIONS ---
    wants_budget = monthly_income * 0.30
    
    if discretionary_income > 0:
        percent_of_free_cash = (item_cost / discretionary_income) * 100
    else:
        percent_of_free_cash = 1000 
    
    # Ramen Math
    coffee_cost = 4.45 
    coffee_equivalent = int(item_cost / coffee_cost)
    
    # Work Hours Math
    implied_hourly = monthly_income / 160 
    if implied_hourly < 10: implied_hourly = 10 
    hours_to_work = item_cost / implied_hourly

    # --- VERDICT LOGIC ---
    score = 100
    reasons = []

    if debt_funding:
        score -= 50
        reasons.append("🚩 Using debt for a non-emergency is a trap.")
    
    if is_need == "Want (Be honest)":
        if percent_of_free_cash > 50:
            score -= 30
            reasons.append("🚩 This single item eats over 50% of your disposable income.")
        if item_cost > wants_budget:
            score -= 20
            reasons.append(f"⚠️ This exceeds your monthly 'Wants' budget of ${wants_budget:.0f}.")
    
    if peer_pressure:
        score -= 15
        reasons.append("⚠️ FOMO detected.")
        
    if time_waited == "Just saw it (Impulse)":
        score -= 10
        reasons.append("⏳ Impulse buy. Wait 24 hours.")
        
    if current_savings < (fixed_expenses * 3):
        score -= 10
        reasons.append("⚠️ Emergency fund is low (< 3 months).")

    # --- DISPLAY RESULTS ---
    st.markdown("---")
    st.header("4. The Verdict")
    
    if st.button("Analyze Decision"):
        
        # Color Logic
        if score >= 80:
            status_class = "green"
            verdict_text = "DO IT (Responsibly)"
            msg = "Your finances look solid enough to handle this."
        elif 50 <= score < 80:
            status_class = "yellow"
            verdict_text = "PROCEED WITH CAUTION"
            msg = "You can afford it, but it's tight."
        else:
            status_class = "red"
            verdict_text = "BAD IDEA"
            msg = "This purchase puts you in the danger zone."

        # Render Text Box
        st.markdown(f"""
        <div class="verdict-box {status_class}">
            <h2 style="margin:0;">{verdict_text}</h2>
            <p style="font-size:18px;">{msg}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if reasons:
            st.subheader("Why?")
            for reason in reasons:
                st.write(reason)
        
        st.subheader("The Reality Check")
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.markdown(f"**Opportunity Cost:**")
            st.write(f"🍜 Equal to **{coffee_equivalent} medium iced coffees**.")
            st.write(f"💼 Requires **{hours_to_work:.1f} hours of work**.")
            
        with col_res2:
            st.markdown("**Monthly Income Breakdown**")
            
            # --- NUMPY REPLACEMENT ---
            # We create a simple DataFrame for the built-in bar chart
            remaining_cash = max(0, discretionary_income - item_cost)
            
            # Create data using NumPy array
            chart_data = pd.DataFrame(
                np.array([
                    [fixed_expenses], 
                    [item_cost], 
                    [remaining_cash]
                ]),
                index=['Fixed Bills', 'This Purchase', 'Leftover Cash'],
                columns=['Amount ($)']
            )
            
            # Use Streamlit's built-in chart (no Plotly required)
            st.bar_chart(chart_data)

else:
    st.info("Enter an item and cost above to see the magic.")
