import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Vendas", layout="wide")

@st.cache_data
def load_data():
    df_vendas = pd.read_csv('relacao_vendedores_junho.csv', sep=';', encoding='latin-1')
    df_produtos = pd.read_excel('vendas_por_produto.xlsx')
    
    df_vendas['Valor Pedido'] = pd.to_numeric(df_vendas['Valor Pedido'], errors='coerce')
    df_vendas['Desconto'] = pd.to_numeric(df_vendas['Desconto'], errors='coerce')
    
    return df_vendas, df_produtos

df_vendas, df_produtos = load_data()

st.title("📊 Aurora Vendas - Junho 2026")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Vendido", f"R$ {df_vendas['Valor Pedido'].sum():,.0f}".replace(',', '.'))
col2.metric("Ticket Médio", f"R$ {df_vendas['Valor Pedido'].mean():,.0f}".replace(',', '.'))
col3.metric("Pedidos", f"{len(df_vendas):,}")
col4.metric("Clientes", f"{df_vendas['Cliente'].nunique():,}")

st.divider()

st.subheader("Top 10 Vendedores")
top_vendedores = df_vendas.groupby('Vendedor')['Valor Pedido'].sum().nlargest(10)
fig1 = px.bar(x=top_vendedores.index, y=top_vendedores.values, labels={'y': 'Faturamento (R$)', 'x': 'Vendedor'})
st.plotly_chart(fig1, use_container_width=True)

st.divider()

st.subheader("Top 10 Produtos")
top_prod = df_produtos.nlargest(10, 'Total Venda')[['Descrição', 'Total Venda', 'Lucro %']]
fig2 = px.bar(top_prod, x='Total Venda', y='Descrição', orientation='h', color='Lucro %', title="Faturamento por Produto")
st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("Dados das Vendas")
df_display = df_vendas[['Pedido', 'Cliente', 'Valor Pedido', 'Vendedor']].sort_values('Pedido', ascending=False)
st.dataframe(df_display, use_container_width=True)