import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

print("🚀 FORCE INIT: Connecting to MySQL...")

try:
    # 1. Connect to Server (No DB selected yet)
    conn = pymysql.connect(
        host='localhost', 
        user='root', 
        password=os.getenv('MYSQL_PASSWORD')
    )
    cursor = conn.cursor()
    
    # 2. Create the Database
    print("🛠️ Creating Database 'codestatic_db'...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS codestatic_db")
    
    # 3. Select the Database
    conn.select_db('codestatic_db')
    
    # 4. Create Tables Manually (Since run.py was stuck)
    print("📦 Creating Tables...")
    
    tables = [
        """CREATE TABLE IF NOT EXISTS ai_chat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_message TEXT,
            ai_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS code_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code LONGTEXT,
            language VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_name VARCHAR(255),
            code LONGTEXT,
            language VARCHAR(50),
            is_favorite TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS analysis_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            language VARCHAR(50),
            quality_score INT,
            critical_errors_count INT,
            original_code LONGTEXT,
            fixed_code LONGTEXT,
            full_json_report JSON, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS ci_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_name VARCHAR(255),
            status VARCHAR(50),
            score INT,
            detected_issues TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
    
    for sql in tables:
        cursor.execute(sql)
        
    conn.commit()
    conn.close()
    print("\n✅ SUCCESS! Database and Tables are ready.")
    print("👉 You can now run 'python run.py'")

except Exception as e:
    print(f"\n❌ ERROR: {e}")