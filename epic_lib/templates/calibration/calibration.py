


dfs = []


def fitness():
    ret = pd.read_csv('yield.csv')
    err = np.mean(ret['err'])
    return [err]

