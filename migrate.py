import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

MEDIA_BASE_PATH = os.getenv("MEDIA_BASE_PATH", "/tmp")
DB_PATH = os.path.join(MEDIA_BASE_PATH, "folders.db")

con = duckdb.connect(DB_PATH)
con.execute("""
CREATE TABLE IF NOT EXISTS folders (
    media_type VARCHAR,
    name VARCHAR,
    PRIMARY KEY (media_type, name)
)
""")
con.close()
print("Migration complete.")