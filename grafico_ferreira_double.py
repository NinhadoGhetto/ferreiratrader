import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import os
import numpy as np

app = Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='grafico-linhas'),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    dcc.Slider(id='range-slider', min=0, max=0, step=1, value=0)
])

@app.callback(
    Output('grafico-linhas', 'figure'),
    Output('range-slider', 'max'),
    Output('range-slider', 'value'),
    Input('interval-component', 'n_intervals'),
    Input('range-slider', 'value'),
    prevent_initial_call=False
)
def atualizar_grafico(n, slider_valor):
    try:
        df = pd.read_csv("registro_pedras.csv")
    except FileNotFoundError:
        return go.Figure(), 0, 0

    df['valor'] = df['cor'].map({'P': 1, 'V': -1, 'B': 0})
    df['anotacao'] = df['cor'].apply(lambda x: 'B' if x == 'B' else '')
    df['rodada'] = range(1, len(df) + 1)

    df['direcao'] = df['valor'].cumsum()

    # Médias móveis
    df['EMA_8'] = df['direcao'].ewm(span=8, adjust=False).mean()
    df['EMA_80'] = df['direcao'].ewm(span=80, adjust=False).mean()
    df['EMA_200'] = df['direcao'].ewm(span=200, adjust=False).mean()
    df['SMA_20'] = df['direcao'].rolling(window=20).mean()

    # Média dos últimos 80 pontos onde houve branco
    df['EMA_B'] = np.nan
    brancos = df[df['cor'] == 'B'].index
    for i in brancos:
        start = max(0, i - 79)
        valores_b = df.loc[start:i]
        valores_b = valores_b[valores_b['cor'] == 'B']
        if not valores_b.empty:
            df.at[i, 'EMA_B'] = valores_b['direcao'].mean()
    df['EMA_B'] = df['EMA_B'].ffill()

    inicio = max(0, len(df) - 300)
    fim = inicio + 300

    ultimos_80 = df.iloc[max(0, len(df) - 80):]
    max_80 = ultimos_80['direcao'].max()
    min_80 = ultimos_80['direcao'].min()

    ultimos_200 = df.iloc[max(0, len(df) - 200):]
    max_200 = ultimos_200['direcao'].max()
    min_200 = ultimos_200['direcao'].min()

    fig = go.Figure()

    # Traçado principal (linhas e pontos)
    for i in range(inicio + 1, min(fim, len(df))):
        fig.add_trace(go.Scatter(
            x=[df['rodada'][i-1], df['rodada'][i]],
            y=[df['direcao'][i-1], df['direcao'][i]],
            mode='lines+markers+text',
            line=dict(color='black', width=1),
            marker=dict(size=3, color='black'),
            text=[df['anotacao'][i-1], df['anotacao'][i]],
            textposition='top center',
            textfont=dict(color='red'),
            showlegend=False
        ))

    # EMA 8 - vermelha lisa fina
    fig.add_trace(go.Scatter(
        x=df['rodada'][inicio:fim],
        y=df['EMA_8'][inicio:fim],
        mode='lines',
        line=dict(color='red', width=1),
        name='EMA 8'
    ))

    # EMA 80 - azul espessa
    fig.add_trace(go.Scatter(
        x=df['rodada'][inicio:fim],
        y=df['EMA_80'][inicio:fim],
        mode='lines',
        line=dict(color='blue', width=3),
        name='EMA 80'
    ))

    # EMA 200 - amarela espessa
    fig.add_trace(go.Scatter(
        x=df['rodada'][inicio:fim],
        y=df['EMA_200'][inicio:fim],
        mode='lines',
        line=dict(color='yellow', width=3),
        name='EMA 200'
    ))

    # SMA 20 - preta contínua
    fig.add_trace(go.Scatter(
        x=df['rodada'][inicio:fim],
        y=df['SMA_20'][inicio:fim],
        mode='lines',
        line=dict(color='black', width=1.5),
        name='Média 20'
    ))

    # EMA dos Brancos - verde fina
    fig.add_trace(go.Scatter(
        x=df['rodada'][inicio:fim],
        y=df['EMA_B'][inicio:fim],
        mode='lines',
        line=dict(color='green', width=1),
        name='EMA B (últimos 80 brancos)'
    ))

    # Linha de máxima (violeta)
    fig.add_trace(go.Scatter(
        x=[df['rodada'][inicio], df['rodada'][fim - 1]],
        y=[max_80, max_80],
        mode='lines',
        line=dict(color='violet', width=1.5, dash='dot'),
        name='Máxima 80'
    ))

    # Linha de mínima (violeta)
    fig.add_trace(go.Scatter(
        x=[df['rodada'][inicio], df['rodada'][fim - 1]],
        y=[min_80, min_80],
        mode='lines',
        line=dict(color='violet', width=1.5, dash='dot'),
        name='Mínima 80'
    ))

    # Linha de máxima 200 (amarela tracejada)
    fig.add_trace(go.Scatter(
        x=[df['rodada'][inicio], df['rodada'][fim - 1]],
        y=[max_200, max_200],
        mode='lines',
        line=dict(color='yellow', width=1.5, dash='dot'),
        name='Máxima 200'
    ))

    # Linha de mínima 200 (amarela tracejada)
    fig.add_trace(go.Scatter(
        x=[df['rodada'][inicio], df['rodada'][fim - 1]],
        y=[min_200, min_200],
        mode='lines',
        line=dict(color='yellow', width=1.5, dash='dot'),
        name='Mínima 200'
    ))

    # Calcular range do eixo Y para marcar linha a linha
    y_min = int(df['direcao'][inicio:fim].min()) - 1
    y_max = int(df['direcao'][inicio:fim].max()) + 1

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            title=None
        ),
        yaxis=dict(
            title="Direção",
            tickmode='linear',
            tick0=y_min,
            dtick=1,
            range=[y_min, y_max]
        ),
        height=600
    )

    return fig, max(0, len(df) - 200), inicio

if __name__ == '__main__':
    app.run(debug=True)
