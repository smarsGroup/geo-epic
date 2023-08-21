def daily2monthly(idx):
    df = pd.read_fwf(os.path.join('daily', flist[idx]), widths=[6, 4, 4, 6,6,6,6,6,6], header=None)
    df = df[df[0] < 2022]

    new_order = [4,5,6,3,7,8,0,1,2]
    cols = df.columns.tolist()
    cols_new = [cols[index] for index in new_order]
    df = df[cols_new]
    df.columns = ['tmax', 'tmin', 'precip', 'short', 'rh', 'wind', 'year', 'month', 'day']

    temp = [g for _, g in df.groupby('month')] # group by month

    ss = [t.apply(np.mean, axis=0) for t in temp] # apply mean by month
    ss = pd.concat(ss, axis=1).T # convert back into dataframe

    dayinmonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ss.precip = dayinmonth*ss.precip
    ss['sdtmx'] = [np.std(t.tmax) for t in temp]
    ss['sdtmn'] = [np.std(t.tmin) for t in temp]
    ss['sdrf'] = [np.std(t.precip) for t in temp]

    num_total_years = len(temp[0])/31
    ss['dayp'] = [np.sum(t.precip >0.5)/num_total_years for t in temp]
    ss['skrf'] = [3*np.abs(np.mean(t.precip) - np.median(t.precip))/np.std(t.precip) for t in temp] 

    prw1 = []
    for t in temp:
        dd = (t.precip>0.5).astype(int)
        tt = dd.diff()
        prw1.append(np.sum(tt == -1)/len(tt))
    ss['prw1'] = prw1

    prw2 = []
    for t in temp:
        dd = (t.precip>0.5).astype(int)
        tt = [1 if(dd.iloc[i] and dd.iloc[i+1]) else 0 for i in range(len(dd)-1)]
        prw2.append(np.sum(tt)/len(tt))
    ss['prw2'] = prw2

    ss['wi'] = [0]*len(ss)
    ss = ss.drop(['month', 'day'], axis=1)

    new_order = [6,0,1,2,3,4,5,7,8,9,10,11,12,13,14]
    cols = ss.columns.tolist()
    cols_new = [cols[index] for index in new_order]
    ss = ss[cols_new]
    ss = ss.T

    names = ['a', 'OBMX', 'OBMN', 'RMO', 'OBSL', 'RH','UAVO', 'SDTMX', 'SDTMN','RST2', 'DAYP', 'RST3', 'PRW1', 'PRW2', 'WI']

    text = ["%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%5s"%(
        ss.loc[cols_new[cur_row]][0], 
        ss.loc[cols_new[cur_row]][1], 
        ss.loc[cols_new[cur_row]][2], 
        ss.loc[cols_new[cur_row]][3],
        ss.loc[cols_new[cur_row]][4], 
        ss.loc[cols_new[cur_row]][5], 
        ss.loc[cols_new[cur_row]][6],
        ss.loc[cols_new[cur_row]][7], 
        ss.loc[cols_new[cur_row]][8], 
        ss.loc[cols_new[cur_row]][9],
        ss.loc[cols_new[cur_row]][10], 
        ss.loc[cols_new[cur_row]][11], 
        names[cur_row]) for cur_row in [1,2,7,8,3,9,11,12,13,10,14,4,5,6]]
    text = ['Month'+pids[idx], '   '] + text

    with open(os.path.join('monthly',pids[idx]+'.INP'), 'w') as f:
        f.write('\n'.join(text))