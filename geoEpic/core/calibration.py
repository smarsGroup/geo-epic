import os
import numpy as np
import pandas as pd

class PygmoProblem:
    """
    A class designed to define an optimization problem for use with the PyGMO library, 
    
    Attributes:
        workspace (Workspace): The workspace object managing the environment in which the model runs.
        dfs (tuple): A tuple of DataFrame-like objects that hold constraints and parameters for the problem.
        bounds (np.ndarray): An array of parameter bounds, each specified as (min, max).
        lens (np.ndarray): An array of cumulative lengths that help in splitting parameters for each DataFrame.
    """

    def __init__(self, workspace, *dfs):
        """
        Initializes the PygmoProblem with a workspace and one or more parameter data frames.

        Args:
            workspace (Workspace): An instance of a Workspace used to run models and evaluate fitness.
            *dfs (DataFrame-like): Variable number of parameter objects with constraints.
        
        Raises:
            Exception: If no fitness function is set in the workspace.
        """
        self.workspace = workspace
        if not hasattr(self.workspace, 'fitness') or self.workspace.fitness is None:
            raise Exception("Fitness function is not set in the workspace")

        self.dfs = dfs
        cons, lens = [], []
        for df in dfs:
            cons += list(df.constraints())  # Assuming each df has a constraints() method returning tuples (min, max)
            lens.append(len(df.constraints()))
        self.bounds = np.array(cons)
        self.lens = np.cumsum(lens)

    def fitness(self, x):
        """
        Evaluate the fitness of a solution vector 'x'.

        Args:
            x (np.array): A solution vector containing parameter values for all data frames.

        Returns:
            float: The fitness value as determined by the workspace's fitness function.
        """
        # Split the parameters according to self.lens, excluding the last cumulative length
        split_x = np.split(x, self.lens[:-1])
        
        # Update parameters in each dataframe and save
        for df, vals in zip(self.dfs, split_x):
            df.edit(vals)
            df.save(self.workspace.model.path)

        # Execute the model and return the fitness value
        return self.workspace.run(progress_bar = False)
    
    @property
    def current(self):
        """
        Retrieve the current parameter values from all data frames.

        Returns:
            np.array: A concatenated array of current parameter values from all data frames.
        """
        return np.concatenate([df.current for df in self.dfs])

    def get_bounds(self):
        """
        Get the bounds for parameters as tuples of (min, max) values for each parameter across all data frames.

        Returns:
            tuple: Two numpy arrays representing the lower and upper bounds of the parameters.
        """
        return self.bounds[:, 0], self.bounds[:, 1]