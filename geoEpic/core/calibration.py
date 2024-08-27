import os
import numpy as np
import pandas as pd

class PygmoProblem:
    def __init__(self, workspace, *dfs):
        self.workspace = workspace
        if self.workspace.fitness is None:
            raise Exception("Fitness function is not set")
        self.dfs = dfs
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
            df.save(self.workspace.model.path)

        # Execute the model and capture output
        ret = self.workspace.run()
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
