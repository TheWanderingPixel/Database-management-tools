import sqlite3

class SQLiteClient:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
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
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            self.close()
            return tables
        except Exception as e:
            return []

    def get_table_schema(self, table_name):
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = cursor.fetchall()
            desc = [d[0] for d in cursor.description]
            self.close()
            # 返回字段名、类型、主键、可空、默认值等
            return [dict(zip(desc, col)) for col in columns]
        except Exception as e:
            return []

    def insert_row(self, table, headers, values):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cols = ','.join(f'"{h}"' for h in headers)
            placeholders = ','.join(['?'] * len(values))
            sql = f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})'
            cursor.execute(sql, values)
            conn.commit()
        finally:
            self.close()

    def update_row(self, table, col, value, pk_dict):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            set_part = f'"{col}"=?'
            where_part = ' AND '.join(f'"{k}"=?' for k in pk_dict)
            sql = f'UPDATE "{table}" SET {set_part} WHERE {where_part}'
            params = [value] + [pk_dict[k] for k in pk_dict]
            cursor.execute(sql, params)
            conn.commit()
        finally:
            self.close()

    def delete_row(self, table, pk_dict):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            where_part = ' AND '.join(f'"{k}"=?' for k in pk_dict)
            sql = f'DELETE FROM "{table}" WHERE {where_part}'
            params = [pk_dict[k] for k in pk_dict]
            cursor.execute(sql, params)
            conn.commit()
        finally:
            self.close() 