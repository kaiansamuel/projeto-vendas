import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Aurora Vendas - Dashboard",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data():
    df_vendas = pd.read_csv('/mount/src/projeto-vendas/relacao_vendedores_junho.csv', sep=';')
    df_produtos = pd.read_excel('/mount/src/projeto-vendas/vendas_por_produto.xlsx')
    
    df_vendas['Data da Venda'] = pd.to_datetime(df_vendas['Data da Venda'], format='%d/%m/%Y')
    df_vendas['Valor Pedido'] = pd.to_numeric(df_vendas['Valor Pedido'], errors='coerce')
    df_vendas['Valor Bruto'] = pd.to_numeric(df_vendas['Valor Bruto'], errors='coerce')
    df_vendas['Desconto'] = pd.to_numeric(df_vendas['Desconto'], errors='coerce')
    
    return df_vendas, df_produtos

df_vendas, df_produtos = load_data()

st.title("📊 Aurora Vendas Dashboard")
st.markdown("**Análise de Performance - Junho 2026** | Grupo Tapeceiro")
st.divider()

st.subheader("🎯 Filtros")
col1, col2, col3 = st.columns(3)

with col1:
    data_min = st.date_input("Data Inicial", df_vendas['Data da Venda'].min())
with col2:
    data_max = st.date_input("Data Final", df_vendas['Data da Venda'].max())
with col3:
    vendedores = st.multiselect("Vendedores", 
                                options=sorted(df_vendas['Vendedor'].unique()),
                                default=sorted(df_vendas['Vendedor'].unique())[:5])

df_filtered = df_vendas[
    (df_vendas['Data da Venda'] >= pd.Timestamp(data_min)) &
    (df_vendas['Data da Venda'] <= pd.Timestamp(data_max)) &
    (df_vendas['Vendedor'].isin(vendedores))
]

st.subheader("💰 KPIs Executivos")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    total_vendas = df_filtered['Valor Pedido'].sum()
    st.metric("Total Vendido", f"R$ {total_vendas:,.2f}".replace(',', '.'), 
              delta=f"{len(df_filtered)} pedidos")

with kpi2:
    ticket_medio = df_filtered['Valor Pedido'].mean()
    st.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(',', '.'))

with kpi3:
    desc_total = df_filtered['Desconto'].sum()
    desc_pct = (desc_total / df_filtered['Valor Bruto'].sum() * 100) if df_filtered['Valor Bruto'].sum() > 0 else 0
    st.metric("Desconto Total", f"R$ {desc_total:,.2f}".replace(',', '.'))

with kpi4:
    num_pedidos = len(df_filtered)
    st.metric("Pedidos", f"{num_pedidos:,}")

with col5:
    top_vendedor = df_filtered.groupby('Vendedor')['Valor Pedido'].sum().idxmax()
    st.metric("Top Vendedor", top_vendedor.split()[0])

st.divider()

st.subheader("👥 Performance de Vendedores")
vendedores_perf = df_filtered.groupby('Vendedor').agg({
    'Valor Pedido': 'sum',
    'Pedido': 'count',
}).sort_values('Valor Pedido', ascending=False).head(10)

fig = px.bar(vendedores_perf, x=vendedores_perf.index, y='Valor Pedido', 
             title="Top 10 Vendedores", labels={'Valor Pedido': 'Faturamento (R$)'})
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("📦 Top 10 Produtos")
top_produtos = df_produtos.nlargest(10, 'Total Venda')[['Descrição', 'Total Venda', 'Lucro %']]
fig = px.bar(top_produtos, x='Total Venda', y='Descrição', orientation='h', 
             color='Lucro %', title="Produtos com Maior Faturamento")
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("📋 Dados Detalhados")
tab1, tab2 = st.tabs(["Pedidos", "Resumo Vendedores"])

with tab1:
    df_display = df_filtered[['Data da Venda', 'Pedido', 'Cliente', 'Valor Pedido', 'Vendedor']].sort_values('Data da Venda', ascending=False)
    st.dataframe(df_display, use_container_width=True)

with tab2:
    resumo = df_filtered.groupby('Vendedor')['Valor Pedido'].agg(['sum', 'count', 'mean']).round(2)
    resumo.columns = ['Total', 'Pedidos', 'Ticket Médio']
    st.dataframe(resumo.sort_values('Total', ascending=False), use_container_width=True)

st.caption(f"📅 Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
