import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = pymysql.connect(
        host='localhost', # Try 127.0.0.1 if this fails
        user='root',
        password=os.getenv('MYSQL_PASSWORD'),
        database='codestatic_db'
    )
    print("✅ PyMySQL Connected Successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")