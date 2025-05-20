import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import t, spearmanr
import streamlit as st
import pathlib

# Caminho para o arquivo de dados, foi convertido de csv para parquet para ser possível a leitura no sistema web
PARQUET_PATH = pathlib.Path("immunization-master-data.parquet")

# Carregamento dos dados
df = pd.read_parquet(PARQUET_PATH)

# Pré-processamento dos Dados
siglas_estados = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
                  'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO']

estado_para_regiao = {
    'AC': 'Norte', 'AP': 'Norte', 'AM': 'Norte', 'PA': 'Norte', 'RO': 'Norte', 'RR': 'Norte', 'TO': 'Norte',
    'AL': 'Nordeste', 'BA': 'Nordeste', 'CE': 'Nordeste', 'MA': 'Nordeste', 'PB': 'Nordeste',
    'PE': 'Nordeste', 'PI': 'Nordeste', 'RN': 'Nordeste', 'SE': 'Nordeste',
    'DF': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste',
    'ES': 'Sudeste', 'MG': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'RS': 'Sul', 'SC': 'Sul'
}

# Filtragem dos dados para incluir apenas estados válidos
df = df[df['LOCAL_NAME'].isin(siglas_estados)].copy()

# Adiciona a coluna de região com base no mapeamento
df['Região'] = df['LOCAL_NAME'].map(estado_para_regiao)

vacinas_basicas = [
    'FL_U1_BCG', 'FL_U1_POLIO', 'FL_U1_DTP', 'FL_U1_HepB',
    'FL_U1_Hib', 'FL_Y1_DTP', 'FL_Y1_POLIO', 'FL_Y1_MMR1'
]

# Filtragem dos dados para incluir apenas indicadores de vacinas básicas e valores não nulos
df = df[
    (df['INDICATOR'].isin(vacinas_basicas)) &
    (df['PC_COVERAGE'].notna())
]

# Agrupamento dos dados por estado, região e ano, calculando médias
df_agrupado = df.groupby(['LOCAL_NAME', 'Região', 'YEAR']).agg({
    # Média da cobertura vacinal
    'PC_COVERAGE': 'mean',  
    # Média do IDH renda
    'MHDI_I': 'mean',  
    # Média do IDH educação     
    'MHDI_E': 'mean'        
}).reset_index()

# Configuração da barra lateral no Streamlit
st.sidebar.title("Controle")

ano_selecionado = st.sidebar.slider("Ano", int(df_agrupado['YEAR'].min()), int(df_agrupado['YEAR'].max()), 2021)

mostrar_regressao = st.sidebar.checkbox("Mostrar linha de regressão", value=True)
mostrar_rotulos = st.sidebar.checkbox("Mostrar nomes dos estados", value=False)

metodo_correl = st.sidebar.radio("Método de correlação", ("Pearson", "Spearman"), index=0)
st.sidebar.caption(
    "**Spearman** é mais preciso, pois as variáveis não seguem distribuição normal. Como o coeficiente entre um e outro varia pouco, mantivemos o **Pearson** como padrão. A linha de regressão linear só serve para a correlação de Pearson."
)

# Seleção da variável de MHDI
variavel_idh_legenda = {'MHDI_I': 'MHDI_I (renda)', 'MHDI_E': 'MHDI_E (educação)'}
variavel_idh = st.sidebar.selectbox("Escolher variável de IDH", options=list(variavel_idh_legenda.keys()), index=0)

# Filtragem dos dados para o ano selecionado
df_ano = df_agrupado[df_agrupado['YEAR'] == ano_selecionado]

# Exibição dos estados com maior e menor cobertura na barra lateral
melhores_estados = df_ano.nlargest(3, 'PC_COVERAGE')[['LOCAL_NAME', 'PC_COVERAGE']]
piores_estados = df_ano.nsmallest(3, 'PC_COVERAGE')[['LOCAL_NAME', 'PC_COVERAGE']]

st.sidebar.markdown("#### Estados com maior cobertura")
st.sidebar.dataframe(melhores_estados.rename(columns={'LOCAL_NAME': 'Estado', 'PC_COVERAGE': 'Cobertura'}), hide_index=True)

st.sidebar.markdown("#### Estados com menor cobertura")
st.sidebar.dataframe(piores_estados.rename(columns={'LOCAL_NAME': 'Estado', 'PC_COVERAGE': 'Cobertura'}), hide_index=True)

st.sidebar.caption(
    ":small[Coberturas maiores que 100% são comuns quando a população-alvo está subestimada ou crianças de outros estados se vacinam ali.]"
)


# Cálculo do coeficiente de correlação e p-valor

# Verifica se há dados suficientes para calcular a correlação (mínimo de 3 pontos)
if len(df_ano[variavel_idh]) >= 3 and len(df_ano['PC_COVERAGE']) >= 3:

    # Correlação de Pearson e p-valor, usando os códigos dos scripts providos
    if metodo_correl == "Pearson":
        correlacao = np.corrcoef(df_ano[variavel_idh], df_ano['PC_COVERAGE'])[0, 1]
        n = len(df_ano)
        if correlacao**2 < 1:
            t_obs = correlacao * np.sqrt((n - 2) / (1 - correlacao**2))
            p_valor = 2 * (1 - t.cdf(abs(t_obs), df=n - 2))
        else:
            p_valor = 0.0
            
    # Correlação de Spearman, usando o scipy.stats
    else:
        correlacao, p_valor = spearmanr(
            df_ano[variavel_idh],
            df_ano['PC_COVERAGE'],
            nan_policy="omit"
        )

    subtitulo = (
        f"{metodo_correl}: coeficiente = <span style='color:tomato;'>{correlacao:.3f}</span> | p-valor = <span style='color:tomato;'>{p_valor:.3f}</span>"
    )
else:
    subtitulo = "Dados insuficientes para calcular correlação"



# Plot do gráfico de dispersão
fig = px.scatter(
    df_ano,
    x=variavel_idh,
    y='PC_COVERAGE',
    color='Região',
    hover_data=['LOCAL_NAME'],
    text='LOCAL_NAME' if mostrar_rotulos else None,
    labels={
        variavel_idh: variavel_idh_legenda[variavel_idh],
        'PC_COVERAGE': 'Cobertura De Vacinação Infantil Média (%)'
    },
    title=f'Cobertura De Vacinação Infantil Média vs {variavel_idh_legenda[variavel_idh]} — {ano_selecionado}<br>{subtitulo}',
    height=600
)

# Mostrar nome dos estados
if mostrar_rotulos:
    fig.update_traces(textposition='top center')

# Mostrar de linha de regressão, se tiver com o coeficiente de pearson e habilitada
if mostrar_regressao and not df_ano.empty and len(df_ano[variavel_idh]) >= 2 and metodo_correl == "Pearson":
    coeficientes = np.polyfit(df_ano[variavel_idh], df_ano['PC_COVERAGE'], 1)
    valores_x = np.linspace(df_ano[variavel_idh].min(), df_ano[variavel_idh].max(), 100)
    valores_y = coeficientes[0] * valores_x + coeficientes[1]
    fig.add_scatter(x=valores_x, y=valores_y, mode='lines', name='Regressão Linear')

# Exibição do gráfico no Streamlit
st.plotly_chart(fig, use_container_width=True)

# Adição de texto explicativo e análise no Streamlit
st.markdown(
    "<h3 style='font-size: 20px;'>Tendências Temporais e Transições</h3><br>" +
    "<p style='font-size: 18px;'>A relação entre o desenvolvimento humano e a cobertura vacinal infantil no Brasil revelou-se complexa e não linear ao longo dos anos analisados. A análise temporal demonstrou variações importantes na correlação entre MHDI_I (renda)/ MHDI_E (educação) e PC_COVERAGE (cobertura vacinal infantil), com destaque para as seguintes transições:</p>" +
    "<ul style='font-size: 18px;'>" +
    "<li><strong>1996–1999:</strong> tendência de aumento na correlação positiva, com queda nos p-valores e aumento do coeficiente de correlação, sugerindo uma relação estatisticamente significativa nesse período.</li>" +
    "<li><strong>2000–2001:</strong> queda acentuada na correlação em 2001, com aumento dos p-valores.</li>" +
    "<li><strong>2002–2005:</strong> correlações fracas e estatisticamente não significativas.</li>" +
    "<li><strong>2006–2011:</strong> tendência de correlação negativa, com oscilações de significância, caracterizado pelos estados do norte mais acima, possivelmente devido a políticas públicas.</li>" +
    "<li><strong>2016–2021:</strong> retomada da correlação positiva em alguns anos (especialmente 2016, 2020 e 2021), novamente com significância estatística, possivelmente com influência da crise da pandemia do COVID-19.</li>" +
    "</ul>" +
    "<p style='font-size: 18px;'>As transições suaves observadas nos gráficos reforçam a importância de uma abordagem longitudinal. As mudanças graduais indicam que os fatores que afetam tanto o desenvolvimento quanto a vacinação evoluem lentamente, exigindo análises que captem essas dinâmicas de longo prazo e evitem conclusões baseadas em recortes curtos.</p>" +
    "<p style='font-size: 18px;'>Apesar das correlações encontradas, elas devem ser interpretadas como indícios de associação, e não como prova de causa e efeito. Para isso, seriam necessários modelos estatísticos mais robustos ou estudos experimentais/longitudinais com controle de variáveis intervenientes.</p>",
    unsafe_allow_html=True
)