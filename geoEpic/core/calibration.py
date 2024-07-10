import os
import numpy as np
import pandas as pd
from epic_lib.dispatcher import dispatch
from epic_lib.misc import ConfigParser

curr_dir = os.getcwd()

config = ConfigParser('./config.yml')
model_path = os.path.dirname(config['EPICModel'])

class MakeProblem:

    def __init__(self, fitness, *dfs):
        self.dfs = dfs
        self.obj = fitness
        cons, lens = [], []
        for df in dfs:
            cons += list(df.constraints())
            lens.append(len(df.constraints()))
        self.bounds = np.array(cons)
        self.lens = np.cumsum(lens)

    def fitness(self, x):
        """
        Evaluate the fitness of a set of parameters 'x'.
        """
        # Split the parameters according to self.lens, excluding the last cumulative length
        split_x = np.split(x, self.lens[:-1])
        
        # Update parameters in each dataframe and save
        for df, vals in zip(self.dfs, split_x):
            df.edit(vals)
            df.save(model_path)

        # Execute the model and capture output
        # command = 'epic_pkg workspace run'
        dispatch('workspace', 'run', '-b False', wait = True)
        ret = self.obj()
        return ret
    
    @property
    def current(self):
        all = []
        for df in self.dfs:
            all.append(df.current)
        return np.concatenate(all)

    def get_bounds(self):
        """
        Get the bounds for parameters as tuples of (min, max) values.
        """
        return self.bounds[:, 0], self.bounds[:, 1]
