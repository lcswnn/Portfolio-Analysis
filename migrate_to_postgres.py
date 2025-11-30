#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL
This script reads data from your SQLite database and inserts it into PostgreSQL
"""

import os
from sqlalchemy import create_engine, text

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""

    # Source database (SQLite)
    sqlite_db_uri = 'sqlite:////Users/lucaswaunn/projects/Portfolio-Analysis/backend/data/portfolio.db'

    # Destination database (PostgreSQL) - uses environment variables
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'portfolio')

    postgres_db_uri = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    print("Starting migration...")
    print(f"Source: SQLite")
    print(f"Destination: PostgreSQL")

    try:
        # Create engines
        sqlite_engine = create_engine(sqlite_db_uri, echo=False)
        postgres_engine = create_engine(postgres_db_uri, echo=False)

        print("\nConnecting to databases...")

        # Test connections
        with sqlite_engine.connect() as conn:
            print("✓ Connected to SQLite")

        with postgres_engine.connect() as conn:
            print("✓ Connected to PostgreSQL")

        # Create tables in PostgreSQL using raw SQL
        print("\nCreating tables in PostgreSQL...")

        with postgres_engine.connect() as conn:
            # Create user table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS "user" (
                    id SERIAL PRIMARY KEY,
                    firstname VARCHAR(30) NOT NULL,
                    lastname VARCHAR(30) NOT NULL,
                    email VARCHAR(50) UNIQUE NOT NULL,
                    username VARCHAR(20) UNIQUE NOT NULL,
                    password VARCHAR(80) NOT NULL
                )
            """))
            print("  ✓ Created table: user")

            # Create uploaded_files table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id),
                    filename VARCHAR(255) NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    position_count INTEGER DEFAULT 0
                )
            """))
            print("  ✓ Created table: uploaded_files")

            # Create positions table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS positions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES "user"(id),
                    "Symbol" VARCHAR(50),
                    "Description" VARCHAR(500),
                    "Qty_Quantity" VARCHAR(100),
                    "Price" VARCHAR(100),
                    "Price_Chng_Dollar" VARCHAR(100),
                    "Price_Chng_Percent" VARCHAR(100),
                    "Mkt_Val" VARCHAR(100),
                    "Day_Chng_Dollar" VARCHAR(100),
                    "Day_Chng_Percent" VARCHAR(100),
                    "Cost_Basis" VARCHAR(100),
                    "Gain_Dollar" VARCHAR(100),
                    "Gain_Percent" VARCHAR(100),
                    "Reinvest" VARCHAR(50),
                    "Reinvest_Capital_Gains" VARCHAR(50),
                    "Security_Type" VARCHAR(100),
                    "Date" VARCHAR(50)
                )
            """))
            print("  ✓ Created table: positions")

            conn.commit()

        # Migrate data
        print("\nMigrating data...")

        with sqlite_engine.connect() as sqlite_conn:
            with postgres_engine.connect() as postgres_conn:

                # Migrate users
                users = sqlite_conn.execute(text("SELECT id, firstname, lastname, email, username, password FROM user"))
                user_rows = users.fetchall()

                if user_rows:
                    for row in user_rows:
                        postgres_conn.execute(text(
                            'INSERT INTO "user" (id, firstname, lastname, email, username, password) VALUES (:id, :firstname, :lastname, :email, :username, :password)'
                        ), {
                            'id': row[0],
                            'firstname': row[1],
                            'lastname': row[2],
                            'email': row[3],
                            'username': row[4],
                            'password': row[5]
                        })
                    postgres_conn.commit()
                    print(f"  ✓ Migrated {len(user_rows)} users")
                else:
                    print(f"  - No users to migrate")

                # Migrate uploaded files
                files = sqlite_conn.execute(text("SELECT id, user_id, filename, upload_date, position_count FROM uploaded_files"))
                file_rows = files.fetchall()

                if file_rows:
                    for row in file_rows:
                        postgres_conn.execute(text(
                            'INSERT INTO uploaded_files (id, user_id, filename, upload_date, position_count) VALUES (:id, :user_id, :filename, :upload_date, :position_count)'
                        ), {
                            'id': row[0],
                            'user_id': row[1],
                            'filename': row[2],
                            'upload_date': row[3],
                            'position_count': row[4]
                        })
                    postgres_conn.commit()
                    print(f"  ✓ Migrated {len(file_rows)} uploaded files")
                else:
                    print(f"  - No files to migrate")

                # Migrate positions
                positions = sqlite_conn.execute(text(
                    'SELECT id, user_id, "Symbol", "Description", "Qty_Quantity", "Price", "Price_Chng_Dollar", "Price_Chng_Percent", "Mkt_Val", "Day_Chng_Dollar", "Day_Chng_Percent", "Cost_Basis", "Gain_Dollar", "Gain_Percent", "Reinvest", "Reinvest_Capital_Gains", "Security_Type", "Date" FROM positions'
                ))
                pos_rows = positions.fetchall()

                if pos_rows:
                    for row in pos_rows:
                        postgres_conn.execute(text(
                            'INSERT INTO positions (id, user_id, "Symbol", "Description", "Qty_Quantity", "Price", "Price_Chng_Dollar", "Price_Chng_Percent", "Mkt_Val", "Day_Chng_Dollar", "Day_Chng_Percent", "Cost_Basis", "Gain_Dollar", "Gain_Percent", "Reinvest", "Reinvest_Capital_Gains", "Security_Type", "Date") VALUES (:id, :user_id, :symbol, :description, :qty, :price, :price_chng_dollar, :price_chng_percent, :mkt_val, :day_chng_dollar, :day_chng_percent, :cost_basis, :gain_dollar, :gain_percent, :reinvest, :reinvest_capital_gains, :security_type, :date)'
                        ), {
                            'id': row[0],
                            'user_id': row[1],
                            'symbol': row[2],
                            'description': row[3],
                            'qty': row[4],
                            'price': row[5],
                            'price_chng_dollar': row[6],
                            'price_chng_percent': row[7],
                            'mkt_val': row[8],
                            'day_chng_dollar': row[9],
                            'day_chng_percent': row[10],
                            'cost_basis': row[11],
                            'gain_dollar': row[12],
                            'gain_percent': row[13],
                            'reinvest': row[14],
                            'reinvest_capital_gains': row[15],
                            'security_type': row[16],
                            'date': row[17]
                        })
                    postgres_conn.commit()
                    print(f"  ✓ Migrated {len(pos_rows)} positions")
                else:
                    print(f"  - No positions to migrate")

        print("\n✅ Migration complete!")
        print(f"Total users: {len(user_rows) if user_rows else 0}")
        print(f"Total files: {len(file_rows) if file_rows else 0}")
        print(f"Total positions: {len(pos_rows) if pos_rows else 0}")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    if not os.getenv('DB_HOST'):
        print("Error: DB_HOST environment variable not set")
        print("Please set the PostgreSQL connection environment variables:")
        print("  export DB_HOST='your-host.ohio-postgres.render.com'")
        print("  export DB_PORT='5432'")
        print("  export DB_USER='your_username'")
        print("  export DB_PASSWORD='your_password'")
        print("  export DB_NAME='your_database_name'")
        exit(1)

    migrate_data()
