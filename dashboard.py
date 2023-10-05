from dash import Dash, html, dcc, dash_table
import plotly.express as px
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta

# Calcular datas da última semana útil
now = datetime.now()
days_until_last_friday = (now.weekday() - 4) % 7
last_friday = now - timedelta(days=days_until_last_friday)
last_monday = last_friday - timedelta(days=4)
last_friday_str = last_friday.strftime('%Y-%m-%d')
last_monday_str = last_monday.strftime('%Y-%m-%d')

# Parâmetros
organization = 'k8bank'
project = 'Suporte K8'
pat = '5ajovh4ztlgcvvkh3zoswfc3z6vj5fzfoewyakw3txkl5ak5uxna'  # Substitua pela sua Personal Access Token.

# URL da API
url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/wiql?api-version=7.0"

# Query em WIQL ajustada para a última semana útil
query = f"""
SELECT [System.Id], [System.WorkItemType], [System.Title], [System.AssignedTo], [System.State], [System.CreatedDate] 
FROM workitems 
WHERE [System.TeamProject] = 'Suporte K8' 
AND [System.WorkItemType] <> 'Bug' 
AND [System.State] <> 'Active'
AND [System.CreatedDate] >= '{last_monday_str}'
AND [System.CreatedDate] <= '{last_friday_str}'
"""

# Headers para a requisição
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + base64.b64encode((f":{pat}").encode('ascii')).decode('ascii')
}

# Payload
payload = {"query": query}

# Inicializar o app Dash
app = Dash(__name__)
fig_api = px.bar()  # Gráfico vazio como padrão

# Fazer a requisição
response = requests.post(url, json=payload, headers=headers)

# Verificar o resultado e criar DataFrame
df_api = pd.DataFrame()

if response.status_code == 200:
    result = response.json()
    work_items = result.get('workItems', [])
    
    if work_items:
        ids = [str(item['id']) for item in work_items[:200]]
        details_url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems?ids={','.join(ids)}&api-version=7.0"
        
        details_response = requests.get(details_url, headers=headers)
        
        if details_response.status_code == 200:
            details_result = details_response.json()
            try:
                df_api = pd.DataFrame([item['fields'] for item in details_result['value']])
                
                # Convertendo valores não primitivos para string e lidando com valores nulos
                for column in df_api.columns:
                    df_api[column] = df_api[column].apply(lambda x: str(x) if (x is not None and not isinstance(x, (str, int, float, bool))) else x)
                df_api = df_api.fillna("N/A")
                
                # Certifique-se de que a coluna de data está no formato datetime
                df_api['System.CreatedDate'] = pd.to_datetime(df_api['System.CreatedDate'])
                
                # Agrupe os dados por data de criação e conte o número de itens por data
                data_last_week = df_api.groupby(df_api['System.CreatedDate'].dt.date).size().reset_index(name='count')
                
                # Crie o gráfico
                fig_api = px.bar(data_last_week, x='System.CreatedDate', y='count', title='Itens de Trabalho Criados na Última Semana')
                fig_api.update_layout(
                    title={
                        'text': "Itens de Trabalho Criados na Última Semana",
                        'y':0.9,
                        'x':0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    title_font=dict(
                         size=16,
                         color="RebeccaPurple",
                         family="Arial Black, Arial, sans-serif",
                    )
                )
                
                # Lista de colunas indesejadas
                columns_to_drop = [
                    'Microsoft.VSTS.Common.ClosedBy',
                    'Microsoft.VSTS.Common.ActivatedDate',
                    'Microsoft.VSTS.Common.ActivatedBy',
                    'Microsoft.VSTS.Common.StateChangeDate',
                    'Microsoft.VSTS.Common.ClosedDate',
                    'Microsoft.VSTS.Common.Priority',
                    'Microsoft.VSTS.Common.StackRank',
                    'WEF_03D2ED238E7E4131961EB8F5B49757A6_Kanban.Column',
                    'WEF_03D2ED238E7E4131961EB8F5B49757A6_Kanban.Column.Done',
                    'System.History',
                    'System.BoardColumnDone',
                    'System.CommentCount'
                ]

                # Remover colunas indesejadas do DataFrame
                df_api = df_api.drop(columns=columns_to_drop, errors='ignore')
                
                # Processar a coluna System.CreatedBy para obter apenas o displayName
                df_api['System.CreatedBy'] = df_api['System.CreatedBy'].apply(
                    lambda x: x.split('<')[0].strip() if ('<' in x and '>' in x) else x
                )
                
            except KeyError as e:
                print("Erro ao acessar a chave:", e)
        else:
            print("Erro ao obter detalhes dos itens de trabalho:", details_response.status_code)
    else:
        print("Sem dados após o filtro de ID.")
else:
    print("Erro:", response.status_code)
    print(response.text)

# Estrutura da página
app.layout = html.Div(
    children=[
        dcc.Graph(
            id='api-graph',
            figure=fig_api
        ),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df_api.columns],
            data=df_api.to_dict('records'),
        ),
    ]
)

# Iniciar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)
         
