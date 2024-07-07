# geo_epic/simulation/epic_model.py

class EpicModel:
    def __init__(self, path):
        """
        Initializes an EpicModel object with the given path.
        
        Parameters:
        path (str): Path to the EPIC model directory.
        """
        self.path = path
        self.start_year = None
        self.duration = None
        self.output_types = []

    def setup(self, start_year, duration):
        """
        Sets up the model with the given start year and duration.
        
        Parameters:
        start_year (int): The start year for the model simulation.
        duration (int): The duration of the model simulation in years.
        """
        self.start_year = start_year
        self.duration = duration

    def set_output_types(self, output_types):
        """
        Sets the types of output the model should generate.
        
        Parameters:
        output_types (list): A list of output types to generate.
        """
        self.output_types = output_types

    def get_model_info(self):
        """
        Returns the model configuration details.
        
        Returns:
        dict: A dictionary containing the model configuration details.
        """
        return {
            'path': self.path,
            'start_year': self.start_year,
            'duration': self.duration,
            'output_types': self.output_types
        }
    

# Example usage:
# model = EpicModel(path='./model/EPIC2301dt20230820')
# model.setup(start_year=2014, duration=10)
# model.set_output_types(['ACY', 'DGN'])
