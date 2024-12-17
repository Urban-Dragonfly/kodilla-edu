import pandas as pd
import datetime as dt
import os
import dash
from dash import html, dcc
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import tab1
import tab2
import tab3

class db:
    def __init__(self):
        base_path = os.path.join(os.path.dirname(__file__), 'db')
        self.transactions = db.transation_init()
        self.cc = pd.read_csv(os.path.join(base_path, 'country_codes.csv'), index_col=0)
        self.customers = pd.read_csv(os.path.join(base_path, 'customers.csv'), index_col=0)
        self.prod_info = pd.read_csv(os.path.join(base_path, 'prod_cat_info.csv'))

    @staticmethod
    def transation_init():
        transactions = []
        src = os.path.join(os.path.dirname(__file__), 'db', 'transactions')
        for filename in os.listdir(src):
            transactions.append(pd.read_csv(os.path.join(src, filename), index_col=0))
        
        transactions = pd.concat(transactions)

        def convert_dates(x):
            try:
                return dt.datetime.strptime(x,'%d-%m-%Y')
            except:
                return dt.datetime.strptime(x,'%d/%m/%Y')

        transactions['tran_date'] = transactions['tran_date'].apply(lambda x: convert_dates(x))

        return transactions

    def merge(self):
        df = self.transactions.join(self.prod_info.drop_duplicates(subset=['prod_cat_code'])
        .set_index('prod_cat_code')['prod_cat'],on='prod_cat_code',how='left')

        df = df.join(self.prod_info.drop_duplicates(subset=['prod_sub_cat_code'])
        .set_index('prod_sub_cat_code')['prod_subcat'],on='prod_subcat_code',how='left')

        df = df.join(self.customers.join(self.cc,on='country_code')
        .set_index('customer_Id'),on='cust_id')

        # Calculate Age from DOB
        current_date = pd.Timestamp('2019-02-01')  # Valid until Feb 2019
        df['Age'] = df['DOB'].apply(lambda x: (current_date - pd.to_datetime(x, dayfirst=True)).days // 365)

        self.merged = df

df = db()
df.merge()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

app.layout = html.Div([html.Div([dcc.Tabs(id='tabs',value='tab-1',children=[
                            dcc.Tab(label='Sprzedaż globalna',value='tab-1'),
                            dcc.Tab(label='Produkty',value='tab-2'),
                            dcc.Tab(label='Kanały Sprzedaży', value='tab-3')
                            ]),
                            html.Div(id='tabs-content')
                    ],style={'width':'80%','margin':'auto'})],
                    style={'height':'100%'})

@app.callback(Output('tabs-content','children'),[Input('tabs','value')])
def render_content(tab):

    if tab == 'tab-1':
        return tab1.render_tab(df.merged)
    elif tab == 'tab-2':
        return tab2.render_tab(df.merged)
    elif tab == 'tab-3':
        return tab3.render_tab(df.merged)

## tab1 callbacks
@app.callback(Output('bar-sales','figure'),
    [Input('sales-range','start_date'),Input('sales-range','end_date')])
def tab1_bar_sales(start_date,end_date):

    truncated = df.merged[(df.merged['tran_date']>=start_date)&(df.merged['tran_date']<=end_date)]
    grouped = truncated[truncated['total_amt']>0].groupby([pd.Grouper(key='tran_date',freq='ME'),'Store_type'])['total_amt'].sum().round(2).unstack()

    traces = []
    for col in grouped.columns:
        traces.append(go.Bar(x=grouped.index,y=grouped[col],name=col,hoverinfo='text',
        hovertext=[f'{y/1e3:.2f}k' for y in grouped[col].values]))

    data = traces
    fig = go.Figure(data=data,layout=go.Layout(title='Przychody',barmode='stack',legend=dict(x=0,y=-0.5)))

    return fig

@app.callback(Output('choropleth-sales','figure'),
            [Input('sales-range','start_date'),Input('sales-range','end_date')])
def tab1_choropleth_sales(start_date,end_date):

    truncated = df.merged[(df.merged['tran_date']>=start_date)&(df.merged['tran_date']<=end_date)]
    grouped = truncated[truncated['total_amt']>0].groupby('country')['total_amt'].sum().round(2)

    trace0 = go.Choropleth(colorscale='Viridis',reversescale=True,
                            locations=grouped.index,locationmode='country names',
                            z = grouped.values, colorbar=dict(title='Sales'))
    data = [trace0]
    fig = go.Figure(data=data,layout=go.Layout(title='Mapa',geo=dict(showframe=False,projection={'type':'natural earth'})))

    return fig

## tab2 callbacks
@app.callback(Output('barh-prod-subcat','figure'),
            [Input('prod_dropdown','value')])
def tab2_barh_prod_subcat(chosen_cat):

    grouped = df.merged[(df.merged['total_amt']>0)&(df.merged['prod_cat']==chosen_cat)].pivot_table(index='prod_subcat',columns='Gender',values='total_amt',aggfunc='sum').assign(_sum=lambda x: x['F']+x['M']).sort_values(by='_sum').round(2)

    traces = []
    for col in ['F','M']:
        traces.append(go.Bar(x=grouped[col],y=grouped.index,orientation='h',name=col))

    data = traces
    fig = go.Figure(data=data,layout=go.Layout(barmode='stack',margin={'t':20,}))
    return fig

## tab3 callbacks
@app.callback(
    [Output('heatmap-sales', 'figure'),
     Output('bar-sales-by-day', 'figure')],
    [Input('tabs', 'value')]
)
def update_heatmap_and_bar(tab):
    if tab != 'tab-3':
        return go.Figure(), go.Figure()
    
    sales_by_day = df.merged[df.merged['total_amt'] > 0].groupby(['Day_of_Week', 'Store_type'])['total_amt'].sum().reset_index()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Heatmap
    heatmap_data = sales_by_day.pivot(index='Day_of_Week', columns='Store_type', values='total_amt').reindex(day_order)
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Viridis',
        colorbar=dict(title='Sales')
    ))
    heatmap_fig.update_layout(title="Sales Heatmap by Day of Week and Retail Channel")
    
    # Bar Plot
    bar_traces = []
    for store_type in sales_by_day['Store_type'].unique():
        filtered = sales_by_day[sales_by_day['Store_type'] == store_type]
        bar_traces.append(go.Bar(x=filtered['Day_of_Week'], y=filtered['total_amt'], name=store_type))
    
    bar_fig = go.Figure(data=bar_traces)
    bar_fig.update_layout(title="Sales by Day of Week and Retail Channel", barmode='group')
    
    return heatmap_fig, bar_fig

@app.callback(
    [Output('pie-gender', 'figure'),
     Output('pie-age', 'figure'),
     Output('pie-country', 'figure'),
     Output('pie-product', 'figure')],
    Input('retail-channel-dropdown', 'value')
)
def update_pie_charts(selected_channel):
    filtered = df.merged[(df.merged['Store_type'] == selected_channel) & (df.merged['total_amt'] > 0)]
    
    # Gender Pie Chart
    gender_counts = filtered['Gender'].value_counts()
    fig_gender = go.Figure(data=[go.Pie(labels=gender_counts.index, values=gender_counts.values, title="Gender Distribution")])
    
    # Age Pie Chart
    age_groups = pd.cut(filtered['Age'], bins=[0, 25, 30, 35, 40, 45, 100], labels=['<25', '26-30', '31-35', '36-40', '41-45', '46+'])
    age_counts = age_groups.value_counts()
    fig_age = go.Figure(data=[go.Pie(labels=age_counts.index, values=age_counts.values, title="Age Distribution")])
    
    # Country Pie Chart
    country_counts = filtered['country'].value_counts()
    fig_country = go.Figure(data=[go.Pie(labels=country_counts.index, values=country_counts.values, title="Country Distribution")])
    
    # Product Type Pie Chart
    product_counts = filtered['prod_cat'].value_counts()
    fig_product = go.Figure(data=[go.Pie(labels=product_counts.index, values=product_counts.values, title="Product Type Distribution")])
    
    return fig_gender, fig_age, fig_country, fig_product

if __name__ == '__main__':
    app.run_server(debug=True)