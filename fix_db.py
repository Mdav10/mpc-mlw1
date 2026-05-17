import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mlw_attack_user:ShJf3c9NA4Jf1ADITLYh3fIlHc7akHXC@dpg-d8063p9j2pic73f1mm40-a.frankfurt-postgres.render.com:5432/mlw_attack')

def fix_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    # Drop old table and recreate with correct schema
    cur.execute("DROP TABLE IF EXISTS captured_data CASCADE")
    cur.execute('''
        CREATE TABLE captured_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            ip TEXT,
            user_agent TEXT,
            data_type TEXT,
            data_content TEXT
        )
    ''')
    conn.commit()
    print("[+] Table recreated successfully with correct columns")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    fix_db()
