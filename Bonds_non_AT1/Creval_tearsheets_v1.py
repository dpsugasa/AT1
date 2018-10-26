# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 10:18:14 2018

Creval price action with equity post to plotly

@author: dsugasa
"""

import pandas as pd
from tia.bbg import LocalTerminal
import numpy as np
from datetime import datetime, timedelta
from operator import itemgetter
from csv import DictReader
from collections import OrderedDict
import plotly
import plotly.plotly as py #for plotting
import plotly.graph_objs as go
import plotly.dashboard_objs as dashboard
import plotly.tools as tls
import plotly.figure_factory as ff
#import cufflinks as cf
import credentials

#set the script start time
start_time = datetime.now()

'''
Create Functions
'''

#create financing function

def sharpe_ratio(returns, n=252):
    return np.round(np.sqrt(n) * (returns.mean()/returns.std()), 3)

def max_DD(prices):
    #takes cumulative returns
    max2here = prices.expanding(min_periods=1).max()
    dd2here = prices - max2here
    return np.round(dd2here.min(), 3)

# set dates, securities, and fields
start_date = '01/01/2005'
end_date = "{:%m/%d/%Y}".format(datetime.now())

IDs = ['CVALIM 8.25 CORP', 'CVAL IM EQUITY']

price_fields = ['LAST PRICE', 'HIGH', 'LOW']
ref_data = ['ID_ISIN', 'CPN', 'CPN_FREQ', 'CRNCY', 'SECURITY_NAME',
            'NXT_CALL_DT', 'ISSUE_DT', 'COMPANY_CORP_TICKER']



df = LocalTerminal.get_historical(IDs, 'LAST PRICE', start_date, end_date,
                                  period = 'DAILY').as_frame()
df.columns = df.columns.droplevel(-1)
df = df.fillna(method = 'ffill')
df = df.dropna()
    

#for q in IDs:
#    name = list(q.values())[1]
#    code = list(q.values())[0]
#    
#    d[name] = LocalTerminal.get_historical(code, price_fields, start_date, end_date, period = 'DAILY').as_frame()
#    d[name].columns = d[name].columns.droplevel()
#    d[name] = d[name].append(pd.DataFrame(data = {'LAST PRICE':100, 'HIGH':100, 'LOW':100}, index=[(d[name].index[0] + timedelta(days = -1))])).sort_index()
#    d[name] = d[name].fillna(method = 'ffill')
#    
#    m[name] = LocalTerminal.get_reference_data(code, ref_data).as_frame()
#    
#    n[name] = d[name]['LAST PRICE'].pct_change().dropna().to_frame()
#    n[name] = n[name].rename(columns = {'LAST PRICE': 'p_ret'})
#    n[name]['c_ret'] = (m[name]['CPN'].item()/100)/252
#    n[name]['cum_cpn'] = n[name]['c_ret'].expanding().sum()
#    n[name]['f_ret'] = apply_fin((m[name]['CRNCY'].item()), 0.50)
#    n[name]['f_ret'] = n[name]['f_ret'].fillna(method='ffill')
#    n[name]['cum_f'] = n[name]['f_ret'].expanding().sum()
#    n[name]['t_ret'] = n[name]['c_ret'] + n[name]['f_ret'] + n[name]['p_ret']
#    n[name]['cum_ret'] = n[name]['t_ret'].expanding().sum()
        
#date_now =  "{:%m_%d_%Y}".format(end_date)
corp_tkr = 'CVALIM'
trace1 = go.Scatter(
            x = df['CVALIM 8.25 CORP'].index,
            y = df['CVALIM 8.25 CORP'].values,
            xaxis = 'x1',
            yaxis = 'y1',
            mode = 'lines',
            line = dict(width=2, color= 'blue'),
            name = 'CVALIM 8.25 Price Return',
            )
    
trace2 = go.Scatter(
            x = df['CVAL IM EQUITY'].index,
            y = df['CVAL IM EQUITY'].values,
            xaxis = 'x1',
            yaxis = 'y2',
            mode = 'lines',
            name = 'CVAL Price Return',
            marker = dict(color = 'rgb(65, 244, 103)',
                          line = dict(color='green', width=1.25))
            )
        
#layout = go.Layout(
#    title='Creval Bond vs. Equity',
#    yaxis=dict(
#        title='Bond Price'
#    ),
#    yaxis2=dict(
#        title='Equity Price',
#        titlefont=dict(
#            color='rgb(148, 103, 189)'
#        ),
#        tickfont=dict(
#            color='rgb(148, 103, 189)'
#        ),
#        overlaying='y',
#        side='right'
#    )
#) 

layout = {
    'title': 'Creval 8.25 T2 Bond vs. Equity',
    'yaxis': {'title': 'Bond Price'},
    'yaxis2': {'title': 'Equity Price',              
               'overlaying' : 'y',
               'side': 'right'},
    'shapes': [{'type':'line',
        'x0': '2017-09-01', 'x1': '2017-11-07',
        'y0': 0.35, 'y1': 0.5, 'xref': 'x', 'yref': 'paper',
        'line': {'color': 'rgb(30,30,30)', 'width': 2}
    },
    {'type':'line',
        'x0': '2018-05-01', 'x1': '2018-02-14',
        'y0': 0.40, 'y1': 0.55, 'xref': 'x', 'yref': 'paper',
        'line': {'color': 'rgb(30,30,30)', 'width': 2}
    },
    {
            'type': 'rect',
            'xref': 'x',
            'yref': 'paper',
            'x0': '2018-02-19',
            'y0': 0,
            'x1': '2018-03-8',
            'y1': 1,
            'fillcolor': '#d3d3d3',
            'opacity': 0.4,
            'line': {
                'width': 0,
            }
        }
    ],
    'annotations': [{
        'x': '2017-6-25', 'y': 0.30, 'xref': 'x', 'yref': 'paper',
        'showarrow': False, 'xanchor': 'left',
        'text': 'Capital Increase Announced',
        'font' : {'size': 14}
    },
    {'x': '2018-4-05', 'y': 0.38, 'xref': 'x', 'yref': 'paper',
        'showarrow': False, 'xanchor': 'left',
        'text': 'Rights Priced',
        'font' : {'size': 14}
    },
    {'x': '2018-3-10', 'y': 0.60, 'xref': 'x', 'yref': 'paper',
        'showarrow': False, 'xanchor': 'left',
        'text': 'Rights Trading Period',
        'font' : {'size': 14}
    }
    ]
}                           
data = [trace1, trace2]
fig1 = go.Figure(data=data, layout=layout)

py.iplot(fig1, filename='Creval/Bond/Bond vs. Equity')



#layout1 = dict(
#            width=1800,
#            height=750,
#            autosize=True,
#            title=f'{i} Tear Sheet - {date_now}',
#            margin = dict(t=50),
#            showlegend=False,   
#            xaxis1=dict(axis, **dict(domain=[0.55, 1], anchor='y1', showticklabels=True)),
#            xaxis2=dict(axis, **dict(domain=[0.55, 1], anchor='y2', showticklabels=True)),        
#            xaxis3=dict(axis, **dict(domain=[0, 0.5], anchor='y3')), 
#            yaxis1=dict(axis, **dict(domain=[0.55, 1.0], anchor='x1', hoverformat='.3f', title='Return')),  
#            yaxis2=dict(axis, **dict(domain=[0, 0.5], anchor='x2', hoverformat='.3f', title = 'Return')),
#            yaxis3=dict(axis, **dict(domain=[0.0, 0.5], anchor='x3', hoverformat='.3f', title = 'Return')),
#            plot_bgcolor='rgba(228, 222, 249, 0.65)')
#    
#fig1 = dict(data = [table, cum_ret, ann_ret, mon_ret], layout=layout1)
#py.iplot(fig1, filename = f'AT1/Outright/{corp_tkr}/{i}_Tear Sheet')
                    
print ("Time to complete:", datetime.now() - start_time)