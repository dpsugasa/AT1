# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 10:18:14 2018

Code to create AT1 tearsheets and post to plotly

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
reader = DictReader(open(r'C:\Users\dpsugasa\WorkFiles\AT1\Tearsheets\bonds.csv'))
for line in reader:
    IDs.append(line)


fin_IDs = ['EUR001M Index', 'US0001M Index']
price_fields = ['LAST PRICE', 'HIGH', 'LOW']
ref_data = ['ID_ISIN', 'CPN', 'CPN_FREQ', 'CRNCY', 'SECURITY_NAME',
            'NXT_CALL_DT', 'ISSUE_DT', 'COMPANY_CORP_TICKER']


d = {} #dict of original dataframes per ID
m = {} #reference data
n = {} #pnl data
z = {} #financing data
mtm = {} #dict for momentum calculation

for i in fin_IDs:
    z[i] = LocalTerminal.get_historical(i, 'LAST PRICE', start_date, end_date, period = 'DAILY').as_frame()
    z[i].columns = z[i].columns.droplevel(-1)
    z[i] = z[i].fillna(method = 'ffill')
    


names = [list(q.values())[0] for q in IDs]
#names.append(list(q.values())[0])
#    code = list(q.values())[0]


momo = LocalTerminal.get_historical(names, 'LAST PRICE', start_date, \
                                    end_date, period = 'DAILY').as_frame()

momo.columns = momo.columns.droplevel(-1)
momo = momo.fillna(method = 'ffill')
momo = momo.pct_change()
momo = momo.rolling(window=22).sum()

'''
for q in IDs:
    name = list(q.values())[1]
    code = list(q.values())[0]
    
    d[name] = LocalTerminal.get_historical(code, price_fields, start_date, end_date, period = 'DAILY').as_frame()
    d[name].columns = d[name].columns.droplevel()
    d[name] = d[name].append(pd.DataFrame(data = {'LAST PRICE':100, 'HIGH':100, 'LOW':100}, index=[(d[name].index[0] + timedelta(days = -1))])).sort_index()
    d[name] = d[name].fillna(method = 'ffill')
    
    m[name] = LocalTerminal.get_reference_data(code, ref_data).as_frame()
    
    n[name] = d[name]['LAST PRICE'].pct_change().dropna().to_frame()
    n[name] = n[name].rename(columns = {'LAST PRICE': 'p_ret'})
    n[name]['c_ret'] = (m[name]['CPN'].item()/100)/252
    n[name]['cum_cpn'] = n[name]['c_ret'].expanding().sum()
    n[name]['f_ret'] = apply_fin((m[name]['CRNCY'].item()), 0.50)
    n[name]['f_ret'] = n[name]['f_ret'].fillna(method='ffill')
    n[name]['cum_f'] = n[name]['f_ret'].expanding().sum()
    n[name]['t_ret'] = n[name]['c_ret'] + n[name]['f_ret'] + n[name]['p_ret']
    n[name]['cum_ret'] = n[name]['t_ret'].expanding().sum()
    
    mtm[name] = n[name][['p_ret', 'c_ret', 'f_ret']]
    mtm[name]['t_ret'] = mtm[name]['c_ret'] + mtm[name]['f_ret'] + mtm[name]['p_ret']
    mtm[name]['p_ret_22d'] = mtm[name]['p_ret'].rolling(window=22).sum()
    mtm[name]['t_ret_22d'] = mtm[name]['t_ret'].rolling(window=22).sum()
    
frames = [mtm['SANTAN 6.25']['p_ret_22d'], mtm['BACR 6.625']['p_ret_22d']]
momo = pd.concat(frames, join='outer', axis=1)

        


date_now =  "{:%m_%d_%Y}".format(d[name].last_valid_index())
for i in n.keys():
    corp_tkr = m[i]['COMPANY_CORP_TICKER'].item()
    cum_ret = go.Scatter(
            x = n[i]['cum_ret'].index,
            y = n[i]['cum_ret'].values,
            xaxis = 'x1',
            yaxis = 'y1',
            mode = 'lines',
            line = dict(width=2, color= 'blue'),
            name = 'Cumulative Return',
            )
    
    ann_ret = go.Bar(
            x = n[i]['t_ret'].resample('A').sum().index,
            y = n[i]['t_ret'].resample('A').sum().values,
            xaxis = 'x2',
            yaxis = 'y2',
            name = 'Annual Returns',
            marker = dict(color = 'rgb(65, 244, 103)',
                          line = dict(color='green', width=1.25))
            )
    
    mon_ret = go.Bar(
            x = n[i]['t_ret'].resample('BM').sum().index,
            y = n[i]['t_ret'].resample('BM').sum().values,
            xaxis = 'x3',
            yaxis = 'y3',
            name = 'Annual Returns',
            marker  = dict(color = 'rgb(65, 244, 103)',
                           line = dict(color='green', width=1.25)))
   
    table = go.Table(
            domain = dict(x=[0,0.5],
                          y = [0.55,1.0]),
            columnwidth = [30] +[33,35,33],
            columnorder = [0,1],
            header=dict(height = 15,
                        values = ['', ''],
                        line = dict(color='#7D7F80'),
                        fill = dict(color='#a1c3d1'),
                        align = ['left'] * 5),
                        cells = dict(values= [['ISIN',
                                               'Coupon',
                                               'Currency',
                                               'Issue Date',
                                               'Next Call',
                                               'Cumulative Return',
                                               'Carry Return',
                                               'Financing Cost',
                                               'Current Price',
                                               'Max Price',
                                               'Min Price',
                                               'Mean Price',
                                               'Sharpe Ratio',
                                               'Max Drawdown'],
    
                                    [m[i]['ID_ISIN'].item(),
                                     m[i]['CPN'].item(),
                                     m[i]['CRNCY'].item(),
                                     m[i]['ISSUE_DT'],
                                     m[i]['NXT_CALL_DT'],
                                     np.round(n[i]['cum_ret'].tail(1).item(),3),
                                     np.round(n[i]['cum_cpn'].tail(1).item(),3),
                                     np.round(n[i]['cum_f'].tail(1).item(),3),
                                     np.round(d[i]['LAST PRICE'].tail(1),3),
                                     np.round(d[i]['LAST PRICE'].max(),3),
                                     np.round(d[i]['LAST PRICE'].min(),3),
                                     np.round(d[i]['LAST PRICE'].mean(),3),
                                     sharpe_ratio(n[i]['t_ret']),
                                     max_DD(n[i]['cum_ret'])]],
                            line = dict(color='#7D7F80'),
                            fill = dict(color='#EDFAFF'),
                            align = ['left'] * 5))
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
            title=f'{i} Tear Sheet - {date_now}',
            margin = dict(t=50),
            showlegend=False,   
            xaxis1=dict(axis, **dict(domain=[0.55, 1], anchor='y1', showticklabels=True)),
            xaxis2=dict(axis, **dict(domain=[0.55, 1], anchor='y2', showticklabels=True)),        
            xaxis3=dict(axis, **dict(domain=[0, 0.5], anchor='y3')), 
            yaxis1=dict(axis, **dict(domain=[0.55, 1.0], anchor='x1', hoverformat='.3f', title='Return')),  
            yaxis2=dict(axis, **dict(domain=[0, 0.5], anchor='x2', hoverformat='.3f', title = 'Return')),
            yaxis3=dict(axis, **dict(domain=[0.0, 0.5], anchor='x3', hoverformat='.3f', title = 'Return')),
            plot_bgcolor='rgba(228, 222, 249, 0.65)')
    
    fig1 = dict(data = [table, cum_ret, ann_ret, mon_ret], layout=layout1)
    py.iplot(fig1, filename = f'AT1/Outright/{corp_tkr}/{i}_Tear Sheet')

'''
                    
print ("Time to complete:", datetime.now() - start_time)