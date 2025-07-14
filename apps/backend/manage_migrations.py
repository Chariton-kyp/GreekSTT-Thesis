#!/usr/bin/env python
"""Database migration management script."""

import os
import sys

from app import create_app
from app.extensions import db
from flask_migrate import Migrate, downgrade, init, migrate, upgrade

# Create app instance
app, socketio = create_app(os.getenv('FLASK_ENV', 'development'))

# Initialize Migrate instance globally
migrate_instance = Migrate(app, db, directory='migrations')


def init_db():
    """Initialize migration repository."""
    with app.app_context():
        try:
            init(directory='migrations')
            print("✅ Migration repository initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing migrations: {e}")
            return False
        return True


def create_migration(message=None):
    """Create a new migration."""
    with app.app_context():
        try:
            if message:
                migrate(message=message, directory='migrations')
            else:
                migrate(directory='migrations')
            print("✅ Migration created successfully!")
        except Exception as e:
            print(f"❌ Error creating migration: {e}")
            return False
        return True


def upgrade_db():
    """Apply all pending migrations."""
    with app.app_context():
        try:
            upgrade(directory='migrations')
            print("✅ Database upgraded successfully!")
        except Exception as e:
            print(f"❌ Error upgrading database: {e}")
            return False
        return True


def downgrade_db():
    """Revert the last migration."""
    with app.app_context():
        try:
            downgrade(directory='migrations')
            print("✅ Database downgraded successfully!")
        except Exception as e:
            print(f"❌ Error downgrading database: {e}")
            return False
        return True


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print(
            "Usage: python manage_migrations.py [init|migrate|upgrade|downgrade]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init':
        init_db()
    elif command == 'migrate':
        message = sys.argv[2] if len(sys.argv) > 2 else None
        create_migration(message)
    elif command == 'upgrade':
        upgrade_db()
    elif command == 'downgrade':
        downgrade_db()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: init, migrate, upgrade, downgrade")
        sys.exit(1)


if __name__ == '__main__':
    main()
