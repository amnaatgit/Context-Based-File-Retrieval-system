from app.services.db import init_db
from app.services.seed import seed_users

if __name__ == '__main__':
    init_db()
    seed_users()
    print('Database initialized successfully.')
