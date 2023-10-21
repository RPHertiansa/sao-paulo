import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import streamlit as st
from babel.numbers import format_currency
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

customers_data = pd.read_csv('data/customers_dataset.csv')
sellers_data = pd.read_csv('data/sellers_dataset.csv')
orders_data = pd.read_csv('data/orders_dataset.csv')
order_items_data = pd.read_csv('data/order_items_dataset.csv')
order_payments_data = pd.read_csv('data/order_payments_dataset.csv')
geolocation_data = pd.read_csv('data/geolocation_dataset.csv')

customers_data = customers_data.rename(columns={'customer_zip_code_prefix':'zipcode'})
sellers_data = sellers_data.rename(columns={'seller_zip_code_prefix':'zipcode'})
geolocation_data = geolocation_data.rename(columns={'geolocation_zip_code_prefix':'zipcode', 'geolocation_lat': 'lat', 'geolocation_lng': 'long'})

customer_city_top_5 = customers_data['customer_city'].value_counts().head(5)
seller_city_top_5 = sellers_data['seller_city'].value_counts().head(5)

customers_data_sao_paulo = customers_data[customers_data['customer_city'] == 'sao paulo']
sellers_data_sao_paulo = sellers_data[sellers_data['seller_city'] == 'sao paulo']
geolocation_data_sao_paulo = geolocation_data[geolocation_data['geolocation_city'] == 'sao paulo']


customer_count = customers_data_sao_paulo['customer_id'].nunique()
seller_count = sellers_data_sao_paulo['seller_id'].nunique()


st.header('E-Commerce Dashboard')
st.subheader('Demographic')

top_city, (customer, seller) = plt.subplots(1, 2, figsize=(15, 8))

customer_colors = ['r' if city == customer_city_top_5.values[0] else 'b' for city in customer_city_top_5]
customer_city_top_5.plot(kind="bar", color=customer_colors, ax=customer)
customer.set_title('Top 5 Cities Customer')
customer.set_xlabel('City')
customer.set_ylabel('Frequencyi')
customer.set_xticklabels(customer.get_xticklabels(), rotation=0)

seller_colors = ['r' if city == seller_city_top_5.values[0] else 'b' for city in seller_city_top_5]
seller_city_top_5.plot(kind="bar", color=seller_colors, ax=seller)
seller.set_title('Top 5 Cities Seller')
seller.set_xlabel('City')
seller.set_ylabel('Frequencyi')
seller.set_xticklabels(seller.get_xticklabels(), rotation=0)
st.pyplot(top_city)

cust_total, seller_total = st.columns(2)
with cust_total:
    st.metric("Customers", value=customer_count)

with seller_total:
    st.metric("Sellers", value=seller_count)


total_number = pd.DataFrame({'Customer': customer_count, 'Seller': seller_count}.items(), columns=['Category', 'Value'])
total_number_plot = total_number.plot(kind='bar', x='Category', y='Value', legend=False)
total_number_plot.set_xlabel('Customer/Seller')
total_number_plot.set_ylabel('Amount')
total_number_plot.set_title('Total Number of Customer/Seller in Sao Paulo')
total_number_plot.set_xticklabels(total_number_plot.get_xticklabels(), rotation=0)
st.pyplot(total_number_plot.figure)


st.subheader("Transaction Volume")


order_data_by_customer = orders_data[orders_data['customer_id'].isin(customers_data_sao_paulo['customer_id'])]
transaction_volume_of_customer = order_data_by_customer['order_id'].count()

order_items_by_seller = order_items_data[order_items_data['seller_id'].isin(sellers_data_sao_paulo['seller_id'])]
transaction_volume_of_seller = order_items_by_seller['order_id'].nunique()

cust_volume, seller_volume = st.columns(2)

with cust_volume:
    st.metric("Transaction Volume of Customer", value=transaction_volume_of_customer)
with seller_volume:
    st.metric("Transaction Volume of Seller", value=transaction_volume_of_seller)

transaction_volume = pd.DataFrame({'Customer': transaction_volume_of_customer, 'Seller': transaction_volume_of_seller}.items(), columns=['Category', 'Value'])
transaction_volume_plot = transaction_volume.plot(kind='bar', x='Category', y='Value', legend=False)
transaction_volume_plot.set_xlabel('Customer/Seller')
transaction_volume_plot.set_ylabel('Total number of transaction')
transaction_volume_plot.set_title('Transaction Volume')
transaction_volume_plot.set_xticklabels(transaction_volume_plot.get_xticklabels(), rotation=0)
st.pyplot(transaction_volume_plot.figure)


order_payments_by_customer = order_payments_data[order_payments_data['order_id'].isin(order_data_by_customer['order_id'])]
transaction_value_of_customer = np.round(order_payments_by_customer['payment_value'].sum(), 2)

order_payments_by_seller = order_payments_data[order_payments_data['order_id'].isin(order_items_by_seller['order_id'])]
transaction_value_of_seller = np.round(order_payments_by_seller['payment_value'].sum(), 2)


def toReal(number):
    return format_currency(number, "R$ ", locale='es_CO')


cust_value, seller_value = st.columns(2)

with cust_value:
    st.metric("Transaction Value of Customer", value=toReal(transaction_value_of_customer))
with seller_value:
    st.metric("Transaction Value of Seller", value=toReal(transaction_value_of_seller))

transaction_value = pd.DataFrame({'Customer': transaction_value_of_customer, 'Seller': transaction_value_of_seller}.items(), columns=['Category', 'Value'])

transaction_value_plot = transaction_value.plot(kind='bar', x='Category', y='Value', legend=False)
transaction_value_plot.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, pos: f'{x/1e6:.1f}'))

transaction_value_plot.set_xlabel('Customer/Seller')
transaction_value_plot.set_ylabel('Transaction Value in Million R$')
transaction_value_plot.set_title('Transaction Value')
transaction_value_plot.set_xticklabels(transaction_value_plot.get_xticklabels(), rotation=0)
st.pyplot(transaction_value_plot.figure)


sao_paulo_centroid = geolocation_data_sao_paulo.groupby(by="zipcode")[['lat', 'long']].mean().reset_index()

customer_orders_temp = pd.merge(customers_data_sao_paulo, order_data_by_customer, on='customer_id')
customer_payment_merged = pd.merge(customer_orders_temp, order_payments_by_customer, on='order_id')

customer_location = pd.merge(sao_paulo_centroid, customer_payment_merged, on='zipcode')
customer_location_plot = customer_location.groupby(['zipcode', 'lat', 'long']).agg({'payment_value': 'sum', 'customer_id': 'nunique'}).reset_index()
customer_location_plot = customer_location_plot.rename(columns={'customer_id': 'number_of_customer'})


seller_orders_temp = pd.merge(sellers_data_sao_paulo, order_items_by_seller, on='seller_id')
seller_payment_merged = pd.merge(seller_orders_temp, order_payments_by_seller, on='order_id')

seller_location = pd.merge(sao_paulo_centroid, seller_payment_merged, on='zipcode')
seller_location_plot = seller_location.groupby(['zipcode', 'lat', 'long']).agg({'payment_value': 'sum','seller_id': 'nunique', 'order_id':'nunique'}).reset_index()
seller_location_plot = seller_location_plot.rename(columns={'seller_id': 'seller_frequency'})

st.subheader('Contour Map')

location_cust, location_seller = st.columns(2)

with location_cust:
    st.text('Customer Location Distribution')

    customer_location_map = folium.Map(location=[sao_paulo_centroid.lat.mean(), sao_paulo_centroid.long.mean()], zoom_start=13, control_scale=True)
    cust_heatmap_data = []
    for index, customer in customer_location_plot.iterrows():
        cust_heatmap_data.append([customer['lat'], customer['long'], customer['number_of_customer']])

    HeatMap(cust_heatmap_data).add_to(customer_location_map)
    st_folium(customer_location_map, width=800, height=400)

with location_seller:
    st.text('Seller Location Distribution')

    seller_location_map = folium.Map(location=[sao_paulo_centroid.lat.mean(), sao_paulo_centroid.long.mean()], zoom_start=13, control_scale=True)

    seller_heatmap_data = []
    for index, seller in seller_location_plot.iterrows():
        seller_heatmap_data.append([seller['lat'], seller['long'], seller['seller_frequency']])

    HeatMap(seller_heatmap_data).add_to(seller_location_map)
    st_folium(seller_location_map, width=800, height=400)


nominal_cust, nominal_seller = st.columns(2)

with nominal_cust:
    st.text('Customer Transaction Volume Distribution')

    customer_payment_map = folium.Map(location=[sao_paulo_centroid.lat.mean(), sao_paulo_centroid.long.mean()], zoom_start=13, control_scale=True)
    cust_pay_data = []
    for index, customer in customer_location_plot.iterrows():
        cust_pay_data.append([customer['lat'], customer['long'], customer['payment_value']])

    HeatMap(cust_pay_data, ).add_to(customer_payment_map)
    st_folium(customer_payment_map, width=800, height=400)

with nominal_seller:
    st.text('Seller Transaction Volume Distribution')

    seller_payment_map = folium.Map(location=[sao_paulo_centroid.lat.mean(), sao_paulo_centroid.long.mean()], zoom_start=13, control_scale=True)

    seller_pay_data = []
    for index, seller in seller_location_plot.iterrows():
        seller_pay_data.append([seller['lat'], seller['long'], seller['payment_value']])

    HeatMap(seller_pay_data).add_to(seller_payment_map)
    st_folium(seller_payment_map, width=800, height=400)

