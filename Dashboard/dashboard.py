import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from babel.numbers import format_currency
from datetime import datetime
import time

sns.set(style='dark')

current_hour = datetime.now().hour
if current_hour < 12:
    greeting = "Good Morning"
elif 12 <= current_hour < 18:
    greeting = "Good Afternoon"
else:
    greeting = "Good Evening"
st.header(f"{greeting}")

progress_bar = st.progress(0)
for percent_complete in range(100):
    time.sleep(0.01)
    progress_bar.progress(percent_complete + 1)  

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "total_price": "sum"
    }).reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "total_price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_freight_items_df(df):
    freight_items_df = df.groupby('product_id').agg({
        'freight_value': 'sum'
    }).reset_index()
    freight_items_df.sort_values('freight_value', ascending=False, inplace=True)
    return freight_items_df

def create_bystate_df(df):
    """Create a DataFrame summarizing unique customers count by state."""
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df

def plot_order_status_distribution(df):
    """Create a bar plot for the distribution of order statuses."""
    order_status_counts = df['order_status'].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    order_status_counts.plot(kind='bar', ax=ax, color="#90CAF9")
    
    ax.set_title('Distribution of Order Status', fontsize=16)
    ax.set_xlabel('Order Status', fontsize=12)
    ax.set_ylabel('Number of Orders', fontsize=12)
    ax.tick_params(axis='x', rotation=0)
    
    for i, v in enumerate(order_status_counts):
        ax.text(i, v, str(v), ha='center', va='bottom')
    
    plt.tight_layout()
    return fig

def plot_payment_type_distribution(df):
    """Create a pie chart for the distribution of payment types."""
    payment_type_counts = df['payment_type'].value_counts()
    payment_type_percentages = payment_type_counts / payment_type_counts.sum() * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(payment_type_percentages, labels=payment_type_counts.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
    ax.set_title('Payment Method', fontsize=16)
    
    plt.tight_layout()
    return fig

def create_rfm_df(df):
    """Create an RFM (Recency, Frequency, Monetary) DataFrame."""
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", 
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].dt.date.apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    plt.tight_layout()
    return rfm_df

all_df = pd.read_csv("all_data.csv")

datetime_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "shipping_limit_date",
]
for column in datetime_columns:
    df[column] = pd.to_datetime(df[column])

df["total_price"] = df["price"] + df["freight_value"]

min_date = df["order_purchase_timestamp"].min().date()
max_date = df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("SamplePhoto.jpg")  
    start_date, end_date = st.date_input(
        label='Range Time', 
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = df[(df["order_purchase_timestamp"].dt.date >= start_date) & 
             (df["order_purchase_timestamp"].dt.date <= end_date)]

daily_orders_df = create_daily_orders_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('E-Commerce Public Dashboard :sparkles:')
st.subheader('Main Menu')
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

sum_freight_items_df = create_sum_freight_items_df(main_df)
st.subheader("Freight Value")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(25, 10))
colors = ["#90CAF9"] * 5 + ["#D3D3D3"] * (len(sum_freight_items_df) - 5)

sns.barplot(x="freight_value", y="product_id", data=sum_freight_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_xlabel("Total Shipping Cost", fontsize=20)
ax[0].set_title("Highest Shipping Cost Products", fontsize=25)
ax[0].tick_params(axis='y', labelsize=15)
ax[0].tick_params(axis='x', labelsize=15)

sns.barplot(x="freight_value", y="product_id", data=sum_freight_items_df.tail(5), palette=colors, ax=ax[1])
ax[1].set_xlabel("Total Shipping Cost", fontsize=20)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Lowest Shipping Cost Products", fontsize=25)
ax[1].tick_params(axis='y', labelsize=15)
ax[1].tick_params(axis='x', labelsize=15)

st.pyplot(fig)

st.subheader("Customer Demographics")
bystate_df = bystate_df.sort_values(by="customer_count", ascending=False)

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9"] + ["#D3D3D3"] * (len(bystate_df) - 1)
sns.barplot(
    x="customer_count", 
    y="customer_state",
    data=bystate_df,
    palette=colors,
    ax=ax
)

ax.set_title("Total of Customers by State", loc="center", fontsize=25)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=15)
ax.tick_params(axis='x', labelsize=15)

for index, value in enumerate(bystate_df["customer_count"]):
    ax.text(value, index, f'{value:,}', va='center', ha='left', fontsize=12)

st.pyplot(fig)

st.info("🔍 Insight 1: Customers from SP have the highest average order value. Focus marketing efforts there.")

st.subheader("Order Status Distribution")
fig_order_status = plot_order_status_distribution(main_df)
st.pyplot(fig_order_status)

st.subheader("Payment Method Distribution")
fig_payment_type = plot_payment_type_distribution(main_df)
st.pyplot(fig_payment_type)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(figsize=(20, 10))

sns.scatterplot(
    data=rfm_df, 
    x="recency", 
    y="monetary",
    size="frequency", 
    sizes=(100, 1000),
    alpha=0.7,
    palette="coolwarm",
    ax=ax
)

ax.set_title("Recency vs Monetary Value with Frequency as Size", fontsize=25)
ax.set_xlabel("Recency (days)", fontsize=15)
ax.set_ylabel("Monetary Value", fontsize=15)
ax.tick_params(axis='x', labelsize=15)
ax.tick_params(axis='y', labelsize=15)

st.pyplot(fig)

with st.expander("See Raw Data"):
    st.write(main_df)

st.markdown("## **Key Findings**")
st.markdown("""
- **Peak Orders**: Most orders occur on weekends.
- **Top Customer**: Customers from SP have the highest spend.
""")

st.success("Thank you for visiting the E-Commerce Public Dashboard!")
