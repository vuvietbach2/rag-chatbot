import pyodbc  
from  source.core.config import Settings
class DBConnection:
    def __init__(self,setting:Settings):
        self.setting=setting
        
    def Get_DB_Connection(self):
        conn = pyodbc.connect(
            f'DRIVER={self.setting.DRIVER};'
            f'SERVER={self.setting.DB_HOST};'
            f'DATABASE={self.setting.DB_NAME};'
            'Trusted_Connection=yes;'
        )

        return conn



    