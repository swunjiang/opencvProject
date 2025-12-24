import mysql.connector

class Database:
    def __init__(self):
        # 直接在程序中设置数据库连接参数
        self.host = 'localhost'
        self.user = 'root'
        self.password = '9194'  # 使用.env文件中的密码
        self.database = 'attendance_system'
        self.port = 3306
    
    def get_connection(self):
        connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port
        )
        # 增加排序缓冲区大小以避免"Out of sort memory"错误
        cursor = connection.cursor()
        cursor.execute("SET SESSION sort_buffer_size = 2097152")  # 设置为2MB
        cursor.execute("SET SESSION read_rnd_buffer_size = 2097152")  # 设置为2MB
        cursor.close()
        return connection