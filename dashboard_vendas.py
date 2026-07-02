import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Config
st.set_page_config(
    page_title="Aurora Vendas - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Custom - Design System Aurora
st.markdown("""
<style>
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%);
        color: white;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #06b6d4;
    }
    
    [data-testid="stMetricLabel"] {
        color: #e0f2fe;
        font-size: 0.9rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.05) 0%, rgba(14, 165, 233, 0.05) 100%);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.1);
    }
    
    .section-header {
        color: #06b6d4;
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid rgba(6, 182, 212, 0.3);
        padding-bottom: 0.5rem;
    }
    
    .stSelectbox, .stDateInput {
        border-color: rgba(6, 182, 212, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# Cache de dados
@st.cache_data
def load_data():
    df_vendas = pd.read_csv('/mnt/user-data/uploads/relacao_vendedores_junho.csv', sep=';')
    df_produtos = pd.read_excel('/mnt/user-data/uploads/vendas_por_produto.xlsx')
    
    # Limpar e processar
    df_vendas['Data da Venda'] = pd.to_datetime(df_vendas['Data da Venda'], format='%d/%m/%Y')
    df_vendas['Valor Pedido'] = pd.to_numeric(df_vendas['Valor Pedido'], errors='coerce')
    df_vendas['Valor Bruto'] = pd.to_numeric(df_vendas['Valor Bruto'], errors='coerce')
    df_vendas['Desconto'] = pd.to_numeric(df_vendas['Desconto'], errors='coerce')
    
    return df_vendas, df_produtos

df_vendas, df_produtos = load_data()

# Header
col1, col2 = st.columns([0.2, 0.8])
with col1:
    st.markdown("📊")
with col2:
    st.markdown("# Aurora Vendas Dashboard")
    st.markdown("**Análise de Performance - Junho 2026** | Grupo Tapeceiro")

st.markdown("---")

# FILTROS
st.markdown('<div class="section-header">🎯 Filtros</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    data_min = st.date_input("Data Inicial", df_vendas['Data da Venda'].min())
with col2:
    data_max = st.date_input("Data Final", df_vendas['Data da Venda'].max())
with col3:
    vendedores = st.multiselect("Vendedores", 
                                options=sorted(df_vendas['Vendedor'].unique()),
                                default=sorted(df_vendas['Vendedor'].unique())[:5])

# Filtrar dados
df_filtered = df_vendas[
    (df_vendas['Data da Venda'] >= pd.Timestamp(data_min)) &
    (df_vendas['Data da Venda'] <= pd.Timestamp(data_max)) &
    (df_vendas['Vendedor'].isin(vendedores))
]

# KPIs
st.markdown('<div class="section-header">💰 KPIs Executivos</div>', unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    total_vendas = df_filtered['Valor Pedido'].sum()
    st.metric("Total Vendido", f"R$ {total_vendas:,.2f}".replace(',', '.'), 
              delta=f"{len(df_filtered)} pedidos")

with kpi2:
    ticket_medio = df_filtered['Valor Pedido'].mean()
    st.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(',', '.'),
              delta=f"{ticket_medio/df_vendas['Valor Pedido'].mean()*100:.1f}% vs geral")

with kpi3:
    desc_total = df_filtered['Desconto'].sum()
    desc_pct = (desc_total / df_filtered['Valor Bruto'].sum() * 100) if df_filtered['Valor Bruto'].sum() > 0 else 0
    st.metric("Desconto Total", f"R$ {desc_total:,.2f}".replace(',', '.'),
              delta=f"{desc_pct:.2f}%")

with kpi4:
    num_pedidos = len(df_filtered)
    st.metric("Pedidos", f"{num_pedidos:,}", delta=f"{df_filtered['Cliente'].nunique()} clientes")

with kpi5:
    top_vendedor = df_filtered.groupby('Vendedor')['Valor Pedido'].sum().idxmax()
    top_valor = df_filtered.groupby('Vendedor')['Valor Pedido'].sum().max()
    st.metric("Top Vendedor", top_vendedor.split()[0], delta=f"R$ {top_valor:,.0f}".replace(',', '.'))

st.markdown("---")

# ANÁLISE DE VENDEDORES
st.markdown('<div class="section-header">👥 Performance de Vendedores</div>', unsafe_allow_html=True)

col1, col2 = st.columns([0.6, 0.4])

with col1:
    # Top Vendedores
    vendedores_perf = df_filtered.groupby('Vendedor').agg({
        'Valor Pedido': 'sum',
        'Pedido': 'count',
        'Cliente': 'nunique',
        'Desconto': 'sum'
    }).sort_values('Valor Pedido', ascending=False).head(10)
    
    vendedores_perf.columns = ['Valor Vendido', 'Qtd Pedidos', 'Qtd Clientes', 'Desconto']
    vendedores_perf['Ticket Médio'] = vendedores_perf['Valor Vendido'] / vendedores_perf['Qtd Pedidos']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=vendedores_perf.index,
        x=vendedores_perf['Valor Vendido'],
        orientation='h',
        marker=dict(
            color=vendedores_perf['Valor Vendido'],
            colorscale=[[0, '#0ea5e9'], [1, '#06b6d4']],
            showscale=False
        ),
        text=[f"R$ {v:,.0f}" for v in vendedores_perf['Valor Vendido']],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Vendido: R$ %{x:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Top 10 Vendedores",
        xaxis_title="Valor Vendido (R$)",
        yaxis_title="",
        height=400,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.5)',
        plot_bgcolor='rgba(15, 23, 42, 0.3)',
        font=dict(family='Poppins', color='#e0f2fe'),
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**Estatísticas de Vendedores**")
    st.dataframe(
        vendedores_perf[['Valor Vendido', 'Qtd Pedidos', 'Ticket Médio']].round(2),
        use_container_width=True,
        height=400
    )

st.markdown("---")

# ANÁLISE DE PRODUTOS
st.markdown('<div class="section-header">📦 Análise de Produtos</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Top Produtos por Faturamento
    top_produtos = df_produtos.nlargest(10, 'Total Venda')[['Descrição', 'Total Venda', 'Lucro %', 'Qtde']]
    
    fig = px.bar(
        top_produtos,
        x='Total Venda',
        y='Descrição',
        orientation='h',
        title="Top 10 Produtos por Faturamento",
        labels={'Total Venda': 'Faturamento (R$)', 'Descrição': ''},
        color='Lucro %',
        color_continuous_scale=[[0, '#ef4444'], [0.5, '#eab308'], [1, '#22c55e']],
    )
    
    fig.update_layout(
        height=400,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.5)',
        plot_bgcolor='rgba(15, 23, 42, 0.3)',
        font=dict(family='Poppins', color='#e0f2fe'),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Distribuição de Lucro
    df_prod_lucro = df_produtos[df_produtos['Lucro %'].notna()].copy()
    df_prod_lucro['Faixa Lucro'] = pd.cut(df_prod_lucro['Lucro %'], 
                                          bins=[0, 0.1, 0.2, 0.3, 0.5, 1.0],
                                          labels=['0-10%', '10-20%', '20-30%', '30-50%', '+50%'])
    
    lucro_dist = df_prod_lucro['Faixa Lucro'].value_counts().sort_index()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=lucro_dist.index,
            values=lucro_dist.values,
            hole=0.4,
            marker=dict(colors=['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e']),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Produtos: %{value}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Distribuição de Lucratividade",
        height=400,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.5)',
        font=dict(family='Poppins', color='#e0f2fe')
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# INSIGHTS & ANÁLISES
st.markdown('<div class="section-header">🔍 Insights Operacionais</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Impacto de Descontos**")
    desc_impact = df_filtered.copy()
    desc_impact['Com Desconto'] = desc_impact['Desconto'] > 0
    
    fig = px.box(
        desc_impact,
        x='Com Desconto',
        y='Valor Pedido',
        title="Ticket por Estratégia de Desconto",
        color='Com Desconto',
        color_discrete_map={True: '#06b6d4', False: '#0ea5e9'},
        labels={'Com Desconto': 'Com Desconto?', 'Valor Pedido': 'Valor (R$)'}
    )
    
    fig.update_layout(
        height=350,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.5)',
        plot_bgcolor='rgba(15, 23, 42, 0.3)',
        font=dict(family='Poppins', color='#e0f2fe'),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**Sazonalidade de Vendas**")
    venda_diaria = df_filtered.groupby(df_filtered['Data da Venda'].dt.date)['Valor Pedido'].agg(['sum', 'count'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=venda_diaria.index,
        y=venda_diaria['sum'],
        fill='tozeroy',
        name='Faturamento',
        line=dict(color='#06b6d4', width=3),
        hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Faturamento Diário",
        xaxis_title="Data",
        yaxis_title="Faturamento (R$)",
        height=350,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.5)',
        plot_bgcolor='rgba(15, 23, 42, 0.3)',
        font=dict(family='Poppins', color='#e0f2fe'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("**Clientes vs Pedidos**")
    cliente_stats = df_filtered.groupby('Cliente').size()
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=cliente_stats,
        nbinsx=15,
        marker=dict(color='#0ea5e9', line=dict(color='#06b6d4', width=1)),
        hovertemplate='Pedidos: %{x}<br>Clientes: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribuição de Pedidos por Cliente",
        xaxis_title="Qtd Pedidos",
        yaxis_title="Qtd Clientes",
        height=350,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.5)',
        plot_bgcolor='rgba(15, 23, 42, 0.3)',
        font=dict(family='Poppins', color='#e0f2fe'),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# TABELA DE DADOS DETALHADA
st.markdown('<div class="section-header">📋 Detalhamento de Vendas</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Pedidos", "Produtos", "Resumo por Vendedor"])

with tab1:
    df_display = df_filtered[['Data da Venda', 'Pedido', 'Cliente', 'Valor Bruto', 'Desconto', 'Valor Pedido', 'Vendedor']].copy()
    df_display = df_display.sort_values('Data da Venda', ascending=False)
    st.dataframe(df_display, use_container_width=True, height=400)

with tab2:
    st.dataframe(df_produtos[['Ranking', 'Descrição', 'Qtde', 'Total Venda', 'Vl. Custo', 'Lucro %']].head(50), 
                 use_container_width=True, height=400)

with tab3:
    resumo = df_filtered.groupby('Vendedor').agg({
        'Valor Pedido': ['sum', 'mean', 'count'],
        'Cliente': 'nunique',
        'Desconto': 'sum'
    }).round(2)
    resumo.columns = ['Total', 'Ticket Médio', 'Pedidos', 'Clientes', 'Desconto']
    st.dataframe(resumo.sort_values('Total', ascending=False), use_container_width=True)

st.markdown("---")

# Footer
col1, col2 = st.columns(2)
with col1:
    st.caption(f"📅 Período: {df_filtered['Data da Venda'].min().date()} a {df_filtered['Data da Venda'].max().date()}")
with col2:
    st.caption(f"✨ Dashboard Aurora Vendas | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
