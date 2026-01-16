import pymysql
import os
from dotenv import load_dotenv

# --- 💀 SILENT KILLER PROBE: DB CONNECTION ---
print("🚀 [INIT] Loading Environment Variables...")
load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DB", "codestatic_db")

print(f"🔍 [DEBUG] Connecting to {DB_HOST} as {DB_USER}...")

try:
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    
    # Create DB if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.select_db(DB_NAME)
    print(f"✅ [SUCCESS] Database '{DB_NAME}' selected.")

    # 1. USERS TABLE (Auth)
    print("🛠️ [MIGRATION] Checking 'users' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email VARCHAR(255) PRIMARY KEY,
            provider VARCHAR(50),
            full_name VARCHAR(255),
            otp_code VARCHAR(10),
            otp_expiry DATETIME,
            is_verified TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. FEEDBACK TABLE
    print("🛠️ [MIGRATION] Checking 'feedbacks' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255),
            message TEXT,
            rating INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. ADD OWNER COLUMN TO EXISTING TABLES
    tables = ['ai_chat', 'code_history', 'projects', 'analysis_reports', 'ci_logs']
    for t in tables:
        try:
            cursor.execute(f"ALTER TABLE {t} ADD COLUMN user_email VARCHAR(255) DEFAULT 'anonymous@local'")
            print(f"   -> Added 'user_email' to {t}")
        except Exception as e:
            if "Duplicate column" in str(e):
                print(f"   -> 'user_email' exists in {t}")
            else:
                print(f"   ⚠️ [WARNING] Could not update {t}: {e}")

    conn.commit()
    conn.close()
    print("\n✅ [DONE] Database Upgrade Complete. Ready for Production.")

except Exception as e:
    print(f"\n💀 [FATAL] Database Upgrade Failed: {e}")