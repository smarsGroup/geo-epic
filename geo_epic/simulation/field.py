import os

class Field:
    def __init__(self, opc, dly, sol, sit, monthly ):
        self.opc = opc  # management file
        self.dly = dly  # daily weather file
        self.sol = sol  # soil file
        self.sit = sit  # site file
        self.monthly = monthly  # Monthly file
        
        self.check_files_exist()

    def check_files_exist(self):
        files_to_check = [self.opc, self.dly, self.sol, self.sit, self.monthly]
        missing_files = [f for f in files_to_check if not os.path.exists(f)]

        if missing_files:
            raise FileNotFoundError(f"The following required files do not exist: {', '.join(missing_files)}")

    def __str__(self):
        return f"Field(opc='{self.opc}', dly='{self.dly}', sol='{self.sol}', sit='{self.sit}')"
