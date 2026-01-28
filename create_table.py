import pymysql
import ssl

# ⚠️ REPLACE WITH YOUR REAL DETAILS FOR THIS ONE-TIME SCRIPT
DB_HOST = "mysql-3d5f002c-codestatic-ffd8.h.aivencloud.com"
DB_PORT = 25214
DB_USER = "avnadmin"
DB_PASS = "PASTE_YOUR_REAL_AIVEN_PASSWORD_HERE" # <--- UPDATE THIS
DB_NAME = "defaultdb"

def manual_create_table():
    # Bypass the certificate check just for this script
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    print(f"⏳ Connecting to {DB_HOST}...")
    
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            ssl=ssl_context,  # Use the bypass context
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = conn.cursor()
        print("🔨 Creating 'users' table...")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255),
            name VARCHAR(255),
            google_id VARCHAR(255),
            profile_pic VARCHAR(500),
            otp VARCHAR(10),
            otp_expiry DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        print("✅ SUCCESS! Table created.")
        conn.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    manual_create_table()