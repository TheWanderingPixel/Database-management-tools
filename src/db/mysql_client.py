import pymysql

class MySQLClient:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    def connect(self):
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4'
        )
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def test_connection(self):
        try:
            conn = self.connect()
            self.close()
            return True, '连接成功'
        except Exception as e:
            return False, f'连接失败: {e}'

    def get_tables(self):
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
            self.close()
            return tables
        except Exception as e:
            return []

    def get_table_schema(self, table_name):
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW FULL COLUMNS FROM `{table_name}`")
                columns = cursor.fetchall()
                desc = [desc[0] for desc in cursor.description]
            self.close()
            # 返回字段名、类型、主键、可空、默认值、注释等
            return [dict(zip(desc, col)) for col in columns]
        except Exception as e:
            return []

    def get_databases(self):
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                dbs = [row[0] for row in cursor.fetchall()]
            self.close()
            return dbs
        except Exception as e:
            return []

    def insert_row(self, table, headers, values):
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cols = ','.join(f'`{h}`' for h in headers)
                placeholders = ','.join(['%s'] * len(values))
                sql = f"INSERT INTO `{table}` ({cols}) VALUES ({placeholders})"
                cursor.execute(sql, values)
            conn.commit()
        finally:
            self.close()

    def update_row(self, table, col, value, pk_dict):
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                set_part = f'`{col}`=%s'
                where_part = ' AND '.join(f'`{k}`=%s' for k in pk_dict)
                sql = f"UPDATE `{table}` SET {set_part} WHERE {where_part}"
                params = [value] + [pk_dict[k] for k in pk_dict]
                cursor.execute(sql, params)
            conn.commit()
        finally:
            self.close()

    def delete_row(self, table, pk_dict):
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                where_part = ' AND '.join(f'`{k}`=%s' for k in pk_dict)
                sql = f"DELETE FROM `{table}` WHERE {where_part}"
                params = [pk_dict[k] for k in pk_dict]
                cursor.execute(sql, params)
            conn.commit()
        finally:
            self.close() 