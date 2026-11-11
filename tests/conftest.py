import os

# reorder.db.engine reads this on import, and it wins over the developer's .env.
# It points nowhere: no test opens a connection.
os.environ["REORDER_DATABASE_URL"] = "postgresql+psycopg://test:test@localhost/test"
