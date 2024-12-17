import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State

app = dash.Dash()

app.layout = html.Div([html.H1('Kalkulator'),
                       html.Label('Czynnik #1'),
                       dcc.Input(id='product-1', placeholder='5',
                                 type='number', value=''),
                       html.Br(),
                       html.Label('Czynnik #2'),
                       dcc.Input(id='product-2', placeholder='2',
                                 type='number', value=''),
                       html.Div(id='output', style={'font-size': '30px', 'margin': '10px 10px'}),
                       html.Button('Oblicz!', id='submit-btn')])

@app.callback(Output('output', 'children'),
              [Input('submit-btn', 'n_clicks')],
              [State('product-1', 'value'), State('product-2', 'value')])
def multiply(n_clicks, prod_1, prod_2):
    return prod_1 * prod_2


if __name__ == '__main__':
    app.run_server(debug=True)