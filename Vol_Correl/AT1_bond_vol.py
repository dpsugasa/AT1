# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 11:25:50 2018

AT1 vs. Equity Beta

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
import cufflinks as cf
import credentials

#set the script start time
start_time = datetime.now()

'''
Create Functions
'''

#create financing function

def apply_fin(currency, spread):
    if currency == 'USD':
        return ((((z['US0001M Index']) + spread)/100)/252)*-1
    else:
        return ((((z['EUR001M Index']) + spread)/100)/252)*-1

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

IDs = []
reader = DictReader(open(r'C:\Users\dpsugasa\WorkFiles\AT1\Vol_Correl\bonds_w_equity_mini.csv'))
for line in reader:
    IDs.append(line)


fin_IDs = ['EUR001M Index', 'US0001M Index']
price_fields = ['LAST PRICE', 'HIGH', 'LOW']
ref_data = ['ID_ISIN', 'CPN', 'CPN_FREQ', 'CRNCY', 'SECURITY_NAME',
            'NXT_CALL_DT', 'ISSUE_DT', 'BOND_TO_EQY_TICKER', 'COMPANY_CORP_TICKER']


d = {} #dict of original dataframes per ID
eq = {} #dict of equity data
m = {} #reference data
n = {} #pnl data
z = {} #financing data
x = {} #correlation, beta, volatility
v = {} #variables

for i in fin_IDs:
    z[i] = LocalTerminal.get_historical(i, 'LAST PRICE', start_date, end_date, period = 'DAILY').as_frame()
    z[i].columns = z[i].columns.droplevel(-1)
    z[i] = z[i].fillna(method = 'ffill')

short_window = 30
long_window = 252

for q in IDs:
    name = list(q.values())[1]
    code = list(q.values())[0]
    equity = list(q.values())[2]
    
    d[name] = LocalTerminal.get_historical(code, price_fields, start_date, end_date, period = 'DAILY').as_frame()
    d[name].columns = d[name].columns.droplevel()
    d[name] = d[name].append(pd.DataFrame(data = {'LAST PRICE':100, 'HIGH':100, 'LOW':100}, index=[(d[name].index[0] + timedelta(days = -1))])).sort_index()
    d[name] = d[name].fillna(method = 'ffill')
    d[name] = d[name].dropna()
    
    eq[name] = LocalTerminal.get_historical(equity, price_fields, start_date, end_date, period = 'DAILY').as_frame()
    eq[name].columns = eq[name].columns.droplevel()
    eq[name] = eq[name].fillna(method = 'ffill')
    eq[name] = eq[name].dropna()
    
    
    m[name] = LocalTerminal.get_reference_data(code, ref_data).as_frame()
    
    n[name] = d[name]['LAST PRICE'].pct_change().dropna().to_frame()
    n[name] = n[name].rename(columns = {'LAST PRICE': 'p_ret'})
    n[name]['eq_ret'] = eq[name]['LAST PRICE'].pct_change().dropna().to_frame()
    n[name]['c_ret'] = (m[name]['CPN'].item()/100)/252
    n[name]['cum_cpn'] = n[name]['c_ret'].expanding().sum()
    n[name]['f_ret'] = apply_fin((m[name]['CRNCY'].item()), 0.50)
    n[name]['f_ret'] = n[name]['f_ret'].fillna(method='ffill')
    n[name]['cum_f'] = n[name]['f_ret'].expanding().sum()
    n[name]['t_ret'] = n[name]['c_ret'] + n[name]['f_ret'] + n[name]['p_ret']
    n[name]['cum_ret'] = n[name]['t_ret'].expanding().sum()
    
    x[name] = n[name]['p_ret'].to_frame()
    x[name]['eq_ret'] = n[name]['eq_ret']
    x[name] = x[name].fillna(method = 'ffill')
    x[name]['bond_vol'] = x[name]['p_ret'].rolling(window=short_window).std()*(np.sqrt(252))
    x[name]['eq_vol'] = x[name]['eq_ret'].rolling(window=short_window).std()*(np.sqrt(252))
    x[name]['bond_eq_corr'] = x[name]['p_ret'].rolling(window=short_window).corr(other=x[name]['eq_ret'])
    x[name]['bond_eq_beta'] = x[name]['bond_eq_corr']*(x[name]['bond_vol']/x[name]['eq_vol']) 
    
    v[name +'_bond_vol'] =  np.round(x[name]['p_ret'].std()*(np.sqrt(252)),3)
    v[name + '_eq_vol'] = np.round(x[name]['eq_ret'].std()*(np.sqrt(252)),3)
    v[name + '_bond_eq_corr'] = np.round(x[name]['p_ret'].corr(x[name]['eq_ret']),3)
    v[name + '_bond_eq_beta'] = (v[name + '_bond_eq_corr'])*((v[name +'_bond_vol'])/(v[name + '_eq_vol']))
    
    
    
date_now =  "{:%m_%d_%Y}".format(d[name].last_valid_index())
for i in x.keys():
    corp_tkr = m[i]['COMPANY_CORP_TICKER'].item()
    bond_eq_corr = go.Scatter(
            x = x[i]['bond_eq_corr'].index,
            y = x[i]['bond_eq_corr'].values,
            xaxis = 'x1',
            yaxis = 'y1',
            mode = 'lines',
            line = dict(width=2, color= 'blue'),
            name = 'Bond vs Equity Correlation',
            showlegend = True
            )
    
    bond_eq_beta = go.Scatter(
            x = x[i]['bond_eq_beta'].index,
            y = x[i]['bond_eq_beta'].values,
            xaxis = 'x2',
            yaxis = 'y2',
            name = 'Bond vs. Equity Beta',
            marker = dict(color = 'rgb(65, 244, 103)',
                          line = dict(color='green', width=1.25))
            )
    
    bond_vol = go.Scatter(
            x = x[i]['bond_vol'].index,
            y = x[i]['bond_vol'].values,
            xaxis = 'x3',
            yaxis = 'y3',
            name = 'Bond Volatility',
            marker  = dict(color = 'gray',
                           line = dict(color='green', width=1.25)))
    
    equity_vol = go.Scatter(
            x = x[i]['eq_vol'].index,
            y = x[i]['eq_vol'].values,
            xaxis = 'x4',
            yaxis = 'y4',
            name = 'Equity Volatility',
            marker  = dict(color = 'rgb(66, 179, 244)',
                           line = dict(color='green', width=1.25)))
   
#    table = go.Table(
#            domain = dict(x=[0,0.5],
#                          y = [0.55,1.0]),
#            columnwidth = [30] +[33,35,33],
#            columnorder = [0,1],
#            header=dict(height = 0,
#                        values = ['', ''],
#                        line = dict(color='#7D7F80'),
#                        fill = dict(color='#a1c3d1'),
#                        align = ['left'] * 5),
#                        cells = dict(values= [['ISIN',
#                                               'Coupon',
#                                               'Currency',
#                                               'Issue Date',
#                                               'Next Call',
#                                               'Cumulative Return',
#                                               'Carry Return',
#                                               'Financing Cost',
#                                               'Current Price',
#                                               'Max Price',
#                                               'Min Price',
#                                               'Mean Price',
#                                               'Sharpe Ratio',
#                                               'Max Drawdown'],
#    
#                                    [m[i]['ID_ISIN'].item(),
#                                     m[i]['CPN'].item(),
#                                     m[i]['CRNCY'].item(),
#                                     m[i]['ISSUE_DT'],
#                                     m[i]['NXT_CALL_DT'],
#                                     np.round(n[i]['cum_ret'].tail(1).item(),3),
#                                     np.round(n[i]['cum_cpn'].tail(1).item(),3),
#                                     np.round(n[i]['cum_f'].tail(1).item(),3),
#                                     np.round(d[i]['LAST PRICE'].tail(1),3),
#                                     np.round(d[i]['LAST PRICE'].max(),3),
#                                     np.round(d[i]['LAST PRICE'].min(),3),
#                                     np.round(d[i]['LAST PRICE'].mean(),3),
#                                     sharpe_ratio(n[i]['t_ret']),
#                                     max_DD(n[i]['cum_ret'])]],
#                            line = dict(color='#7D7F80'),
#                            fill = dict(color='#EDFAFF'),
#                            align = ['left'] * 5))
    axis=dict(
            showline=True,
            zeroline=False,
            showgrid=True,
            mirror=True,
            ticklen=4, 
            gridcolor='#ffffff',
            tickfont=dict(size=10)
            )                        
                            
    layout1 = dict(
            width=1800,
            height=750,
            autosize=True,
            title=f'{i} Bond vs. Equity - {date_now}',
            margin = dict(t=50),
            showlegend=False,   
            xaxis1=dict(axis, **dict(domain=[0.55, 1], anchor='y1', showticklabels=True)),
            xaxis2=dict(axis, **dict(domain=[0.55, 1], anchor='y2', showticklabels=True)),        
            xaxis3=dict(axis, **dict(domain=[0, 0.5], anchor='y3', showticklabels=True)), 
            xaxis4=dict(axis, **dict(domain=[0, 0.5], anchor='y4', showticklabels=True)),
            yaxis1=dict(axis, **dict(domain=[0.55, 1.0], anchor='x1', hoverformat='.3f', title='Correl')),  
            yaxis2=dict(axis, **dict(domain=[0, 0.5], anchor='x2', hoverformat='.3f', title = 'Beta')),
            yaxis3=dict(axis, **dict(domain=[0.0, 0.5], anchor='x3', hoverformat='.3f', title = 'Bond Volatility')),
            yaxis4=dict(axis, **dict(domain=[0.55, 1], anchor='x4', hoverformat='.3f', title = 'Equity Volatility')),
            plot_bgcolor='rgba(228, 222, 249, 0.65)')
    
    fig1 = dict(data = [equity_vol, bond_eq_corr, bond_eq_beta, bond_vol], layout=layout1)
    py.iplot(fig1, filename = f'AT1/Vol_Correl/{corp_tkr}/{i}_Bond vs. Equity')
                    
print ("Time to complete:", datetime.now() - start_time)