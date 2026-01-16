import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

print("1. Loaded Credentials:")
print(f"   Host: {os.getenv('MYSQL_HOST')}")
print(f"   User: {os.getenv('MYSQL_USER')}")
print("   Pass: [HIDDEN]") 

try:
    print("2. Connecting to MySQL Server...")
    # Force a timeout so it doesn't hang forever
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        connection_timeout=5
    )
    print("✅ SUCCESS! Connected to MySQL.")
    conn.close()
except Exception as e:
    print(f"❌ FAILURE: {e}")