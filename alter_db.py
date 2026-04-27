import sqlite3

def upgrade_db():
    conn = sqlite3.connect('security_profile.db')
    cursor = conn.cursor()
    
    # Add new columns
    try:
        cursor.execute("ALTER TABLE qua_trinh_hoat_dong ADD COLUMN tu_ngay DATE")
        print("Added tu_ngay")
    except Exception as e:
        print("tu_ngay exists?", e)
        
    try:
        cursor.execute("ALTER TABLE qua_trinh_hoat_dong ADD COLUMN den_ngay DATE")
        print("Added den_ngay")
    except Exception as e:
        print("den_ngay exists?", e)
        
    try:
        cursor.execute("ALTER TABLE qua_trinh_hoat_dong ADD COLUMN thiet_lap_canh_bao BOOLEAN DEFAULT 0")
        print("Added thiet_lap_canh_bao")
    except Exception as e:
        print("thiet_lap_canh_bao exists?", e)
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    upgrade_db()
