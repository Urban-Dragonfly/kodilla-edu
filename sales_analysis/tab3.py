from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd

def render_tab(df):
    # Prepare data for days of the week heatmap and bar plot
    df['Day_of_Week'] = df['tran_date'].dt.day_name()
    sales_by_day = df[df['total_amt'] > 0].groupby(['Day_of_Week', 'Store_type'])['total_amt'].sum().reset_index()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    layout = html.Div([
        html.H1("Kanały sprzedaży", style={'text-align': 'center'}),

        # Heatmap and Bar Plot
        html.Div([
            html.Div([dcc.Graph(id='heatmap-sales')], style={'width': '50%'}),
            html.Div([dcc.Graph(id='bar-sales-by-day')], style={'width': '50%'})
        ], style={'display': 'flex'}),

        html.H3("Klientela względem kanału zakupowego", style={'text-align': 'center'}),

        # Dropdown menu for retail channels
        html.Div([
            dcc.Dropdown(
                id='retail-channel-dropdown',
                options=[{'label': st, 'value': st} for st in df['Store_type'].unique()],
                value=df['Store_type'].unique()[0],
                style={'width': '50%', 'margin': 'auto'}
            )
        ]),

        # Pie Charts
        html.Div([
            html.Div([dcc.Graph(id='pie-gender')], style={'width': '50%', 'height': '50%'}),
            html.Div([dcc.Graph(id='pie-age')], style={'width': '50%', 'height': '50%'}),
        ], style={'display': 'flex'}),
        html.Div([
            html.Div([dcc.Graph(id='pie-country')], style={'width': '50%', 'height': '50%'}),
            html.Div([dcc.Graph(id='pie-product')], style={'width': '50%', 'height': '50%'}),
        ], style={'display': 'flex'})
    ])

    return layout
