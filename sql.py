import mysql.connector
import config
log_in = config.log_in_mysql

class TelbotDatabase:
    def __init__(self):
        self.my_bd = mysql.connector.connect(
            host=log_in['host'], 
            user=log_in['user'], 
            passwd=log_in['passwd'],
            database=log_in['database']
            )

        self.mycursor = self.my_bd.cursor()      

    def data_answer(self,query):
        self.mycursor.execute(query)
        q = query.lower()
        if 'show' not in q and 'select' not in q:
            self.my_bd.commit()
        return self.mycursor