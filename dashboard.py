from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.read_excel("ticketsabertos.xlsx")

# criando o gráfico
fig = px.bar(df, x="ANALISTA DO SUPORTE", y="TEMPO DE ATENDIMENTO", color="SETOR", barmode="group")

#Layout da página
app.layout = html.Div(children=[
    html.H1(children='Relatório Semanal de Chamados Suporte Sistemas'),
    html.H2(children='Chamados Abertos no Período de 18 à 22 de Setembro de 2023'),
    
    html.Div(children='''
        Obs: Este gráfico é somente sobre os dados coletados durante a semana.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run(debug=True)

