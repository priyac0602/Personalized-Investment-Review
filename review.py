import streamlit as st
import pandas as pd
import altair as alt
import snowflake.connector

#connect to snowflake account using secrets.toml 
conn=snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse=st.secrets["snowflake"]["warehouse"],
    database=st.secrets["snowflake"]["database"],
    schema=st.secrets["snowflake"]["schema"]
)

#query to fetch cleaned customer data
query="SELECT * FROM wealth_sch.customer_clean"
df=pd.read_sql(query,conn)

st.title("Wealth Management Dashboard")
st.write("""Explore customer insights including credit scores, investments, transactions and more.""")

#sidebar filters to dynamically filter the dashboard
st.sidebar.header("Filters")
country=st.sidebar.multiselect("Select Country", options=df["COUNTRY"].unique(), default=df["COUNTRY"].unique().tolist())
gender=st.sidebar.multiselect("Select Gender", options=df["GENDER"].unique(), default=df["GENDER"].unique())
filtered_df=df[(df["COUNTRY"].isin(country)) & (df["GENDER"].isin(gender))]

#summary metrics
col1,col2,col3=st.columns(3)
col1.metric("Total Customers",filtered_df.shape[0])
col2.metric("Avg Credit Score",round(filtered_df["CREDITSCORE"].mean(),2))
col3.metric("Avg Portfolio Return", round(filtered_df["PORTFOLIORETURN"].mean(),4))


#credit score and risk profile charts
st.header("Customer Overview")
col1,col2=st.columns(2)
with col1:
    st.subheader("Credit Score Distribution")
    credit_rounded=filtered_df["CREDITSCORE"].round(-1)
    credit_counts=credit_rounded.value_counts().sort_index()
    st.bar_chart(credit_counts,x_label="Credit Score", y_label="Number of Customers",color="#088f8f")

with col2:
    st.subheader("Risk Profile Breakdown")
    risk_counts=filtered_df["RISKPROFILE"].value_counts().sort_index()
    st.bar_chart(risk_counts, x_label="Risk Profile",y_label="Number of Customers",color="#f88379")

#churn analysis
st.header("Churn Analysis")
col3,col4,col5=st.columns(3)
with col3:
    st.subheader("Churn Rate by Country")
    churn_by_country=filtered_df[filtered_df["CHURN"]==1]["COUNTRY"].value_counts().sort_index().reset_index()
    churn_by_country.columns=["Country","Churn Count"]
    churn_by_country.set_index("Country",inplace=True)
    if not churn_by_country.empty:
        st.bar_chart(churn_by_country,color="#d22b2b",x_label="Country",y_label="Number of Customers")
    else:
        st.warning("No churned customers")

with col4:
    st.subheader("Churn vs Age")
    churn_age=filtered_df[filtered_df["CHURN"]==1]["AGE"].value_counts().sort_index()
    st.line_chart(churn_age,x_label="Age",color="#1f77b4",y_label="Number of customers who churned")


with col5:
    st.subheader("Churn Rate by Country and Age Group")
    churned=filtered_df[filtered_df["CHURN"]==1]
    churned["AGEGROUP"]=pd.cut(churned["AGE"],bins=[18,30,40,50,60,100],labels=["18-30","31-40","41-50","51-60","60+"])
    churn_grouped=churned.groupby(["COUNTRY","AGEGROUP"]).size().unstack(fill_value=0)
    churn_grouped.reset_index(inplace=True)
    st.bar_chart(churn_grouped,x="COUNTRY",y=churn_grouped.columns[1:].tolist(),y_label="Number of Customers")


#investment preferences
st.header("Investment Preferences")
col6,col7=st.columns(2)
with col6:
    st.subheader("ETF Tech Investments")
    etf_stacked_df=(filtered_df.groupby("ETFTECH")[["ETFHEALTH","ETFMED"]].sum().reset_index())
    etf_stacked_df["ETFTECH"]=etf_stacked_df["ETFTECH"].astype(str)
    st.bar_chart(etf_stacked_df.set_index("ETFTECH"),color=["#1f77b4","#ff7f0e"],x_label="ETF Tech(0=No,1=Yes)",y_label="Number of Customers")
   

with col7:
    st.subheader("Investment Preferences by Risk Profile")
    filtered_df["ROUNDEDRISK"]=filtered_df["RISKPROFILE"].round(1)
    investment_cols=["ETFTECH","ETFHEALTH","ETFMED","REALESTATE","PRIVATEEQUITY"]
    risk_invest_df=filtered_df[["ROUNDEDRISK"]+investment_cols].copy()
    melted_risk_df=risk_invest_df.melt(
        id_vars="ROUNDEDRISK",
        value_vars=investment_cols,
        var_name="Investment Type",
        value_name="Invested"
    )
    melted_risk_df=melted_risk_df[melted_risk_df["Invested"]==1]
    grouped=(
        melted_risk_df.groupby(["ROUNDEDRISK","Investment Type"])
        .size()
        .reset_index(name="Count")
    )
    stacked_chart=alt.Chart(grouped).mark_bar().encode(
        x=alt.X("ROUNDEDRISK:O",title="Risk Profile"),
        y=alt.Y("Count:Q",title="Number of Customers"),
        color=alt.Color("Investment Type:N",title="Investment Type"),
        tooltip=["ROUNDEDRISK","Investment Type","Count"]
    ).properties(
        width=650,
        height=400
    )
    st.altair_chart(stacked_chart,use_container_width=True)

#product usage and transaction behaviour
st.header("Product Usage & Transactions")
col8,col9=st.columns(2)
with col8:
    st.subheader("Number of Products Used")
    product_counts=filtered_df["NUMPRODUCTS"].value_counts().sort_index()
    st.scatter_chart(product_counts,color="#1f77b4",x_label="Number of Products",y_label="Number of Customers")

with col9:
    st.subheader("Transaction Amount by Investment Type")
    investment_cols=['ETFTECH','ETFHEALTH','ETFMED','REALESTATE','PRIVATEEQUITY']
    melted_df=filtered_df.melt(
        id_vars=["LASTTRANSACTIONAMT"],
        value_vars=investment_cols,
        var_name="Investment Type",
        value_name="Invested"
    )
    invested_df=melted_df[melted_df["Invested"]==1]
    box_investment=alt.Chart(invested_df).mark_boxplot(extent='min-max').encode(
        x=alt.X("Investment Type:N",title="Investment Type"),
        y=alt.Y("LASTTRANSACTIONAMT:Q",title="Transaction Amount"),
        color=alt.Color("Investment Type:N",legend=None,scale=alt.Scale(scheme="category10"))
    ).properties(width=650,
                height=400
    )
    st.altair_chart(box_investment,use_container_width=True)

#customer demographics
st.header("Customer Demographics")
col10,col11=st.columns(2)
with col10:
    st.subheader("Age Distribution")
    age_hist=alt.Chart(filtered_df).mark_bar(color='#00b4d8').encode(
        alt.X("AGE:Q",bin=alt.Bin(maxbins=20),title="Customer Age"),
        alt.Y("count():Q", title="Number of Customers")
    ).properties(
        width=350,
        height=350
    ).configure_view(
        stroke=None
    ).configure_axis(
        labelColor='white',
        titleColor='white'
    )
    st.altair_chart(age_hist,use_container_width=True)

with col11:
    st.subheader("Dependents vs Age")
    st.line_chart(filtered_df.groupby("AGE")["DEPENDENTS"].mean(),x_label="Age",y_label="Average Number of Dependents",color="#00a36c")



#smart suggestions
def investment_suggestions(row):
    suggestions = []

    if row["REALESTATE"] == 0 and row["NETASSETS"] > 75000 and row["AGE"] > 35:
        suggestions.append("🏠 Consider investing in Real Estate for long-term asset growth.")

    if row["PRIVATEEQUITY"] == 0 and row["RISKPROFILE"] >= 0.7:
        suggestions.append("🚀 Explore Private Equity to align with your high-risk profile.")

    if row["ETFTECH"] == 0 and row["CREDITSCORE"] > 700 and row["RISKPROFILE"] >= 0.5:
        suggestions.append("💻 Add ETF Tech for diversified yet growth-oriented exposure.")

    if row["RISKPROFILE"] <= 0.3 and row["REALESTATE"] == 0:
        suggestions.append("🛡️ As a low-risk customer, Real Estate or bonds might suit you.")

    invested = sum([row[col] for col in ["ETFTECH", "ETFHEALTH", "ETFMED", "REALESTATE", "PRIVATEEQUITY"]])
    if invested <= 1:
        suggestions.append("📊 Your investments are highly concentrated. Diversify more.")

    return "\n\n".join(suggestions) if suggestions else "✅ Portfolio looks balanced."

#red flag detection
def detect_red_flags(row):
    flags = []

    if row["RISKPROFILE"] > 0.7 and row["CREDITSCORE"] < 600:
        flags.append("⚠️ High risk profile with poor credit score — possible default risk.")

    if row["NETASSETS"] < 10000 and row["PORTFOLIORETURN"] < 0.05:
        flags.append("📉 Low assets and low return — consider reevaluating financial plan.")

    if row["AGE"] > 55 and invested_products(row) == 0:
        flags.append("🔻 Older customer with no investments — missed wealth opportunities.")

    if row["AGE"] < 25 and has_high_risk(row):
        flags.append("🧨 Young customer taking high risk — consider financial literacy programs.")

    return "\n\n".join(flags) if flags else "🟢 No critical red flags detected."

def invested_products(row):
    return sum([row[col] for col in ["ETFTECH", "ETFHEALTH", "ETFMED", "REALESTATE", "PRIVATEEQUITY"]])

def has_high_risk(row):
    return row["RISKPROFILE"] > 0.6

# ----------------- Dashboard UI Section --------------------

st.subheader("📌 Personalized Investment Review")

# Select Customer
selected_id = st.selectbox("Select Customer ID", df["CUSTOMERID"].unique())
customer = df[df["CUSTOMERID"] == selected_id].iloc[0]

# Display Basic Info
st.markdown("### 🧾 Customer Profile")
st.write({
    "Age": customer["AGE"].item(),
    "Gender": customer["GENDER"],
    "Country": customer["COUNTRY"],
    "Credit Score": customer["CREDITSCORE"].item(),
    "Risk Profile": customer["RISKPROFILE"],
    "Portfolio Return": customer["PORTFOLIORETURN"],
    "Net Assets": customer["NETASSETS"].item()
})

# Display Investment Status
st.markdown("### 💼 Current Investment Holdings")
st.write({
    "ETF Tech": customer["ETFTECH"].item(),
    "ETF Health": customer["ETFHEALTH"].item(),
    "ETF Med": customer["ETFMED"].item(),
    "Real Estate": customer["REALESTATE"].item(),
    "Private Equity": customer["PRIVATEEQUITY"].item()
})

# Show Smart Suggestions
st.markdown("### ✅ Suggestions Based on Profile")
st.success(investment_suggestions(customer))

# Show Red Flags
st.markdown("### 🛑 Red Flag Warnings")
st.warning(detect_red_flags(customer))
