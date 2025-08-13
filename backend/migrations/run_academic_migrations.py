#!/usr/bin/env python3
"""
OneClass Academic Management Module - Migration Runner
Automated database migration execution with validation and rollback support
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('academic_migrations.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AcademicMigrationRunner:
    """Run Academic module database migrations"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.migrations_dir = Path(__file__).parent / "academic"
        self.connection = None
        
        # Migration order and metadata
        self.migrations = [
            {
                "file": "001_create_academic_schema.sql",
                "name": "Create Academic Schema",
                "description": "Create academic schema and base tables",
                "required": True
            },
            {
                "file": "002_seed_zimbabwe_data.sql", 
                "name": "Zimbabwe Seed Data",
                "description": "Insert Zimbabwe education system data",
                "required": True
            },
            {
                "file": "003_performance_optimizations.sql",
                "name": "Performance Optimizations", 
                "description": "Add indexes, views, and functions",
                "required": False
            },
            {
                "file": "004_rls_security_policies.sql",
                "name": "RLS Security Policies",
                "description": "Enable row-level security",
                "required": False
            }
        ]
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'oneclass_platform'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', '')
            )
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")
    
    def create_migration_table(self):
        """Create migration tracking table"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE SCHEMA IF NOT EXISTS academic;
                    
                    CREATE TABLE IF NOT EXISTS academic.migration_history (
                        id SERIAL PRIMARY KEY,
                        migration_name VARCHAR(255) NOT NULL UNIQUE,
                        migration_file VARCHAR(255) NOT NULL,
                        description TEXT,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        execution_time_ms INTEGER,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        rollback_sql TEXT
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_migration_history_name 
                        ON academic.migration_history (migration_name);
                """)
            logger.info("📋 Migration tracking table ready")
        except Exception as e:
            logger.error(f"❌ Failed to create migration table: {e}")
            raise
    
    def is_migration_applied(self, migration_name: str) -> bool:
        """Check if migration has been applied"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM academic.migration_history WHERE migration_name = %s AND success = TRUE",
                    (migration_name,)
                )
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logger.warning(f"⚠️ Could not check migration status: {e}")
            return False
    
    def record_migration(self, migration: Dict, execution_time: int, success: bool, error_message: str = None):
        """Record migration in tracking table"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO academic.migration_history 
                    (migration_name, migration_file, description, execution_time_ms, success, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (migration_name) DO UPDATE SET
                        applied_at = NOW(),
                        execution_time_ms = EXCLUDED.execution_time_ms,
                        success = EXCLUDED.success,
                        error_message = EXCLUDED.error_message
                """, (
                    migration["name"],
                    migration["file"],
                    migration["description"],
                    execution_time,
                    success,
                    error_message
                ))
            logger.info(f"📝 Migration '{migration['name']}' recorded")
        except Exception as e:
            logger.error(f"❌ Failed to record migration: {e}")
    
    def run_migration(self, migration: Dict) -> bool:
        """Execute a single migration"""
        migration_file = self.migrations_dir / migration["file"]
        
        if not migration_file.exists():
            logger.error(f"❌ Migration file not found: {migration_file}")
            return False
        
        logger.info(f"🚀 Running migration: {migration['name']}")
        logger.info(f"📁 File: {migration['file']}")
        logger.info(f"📝 Description: {migration['description']}")
        
        try:
            # Read migration SQL
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Execute migration
            start_time = datetime.now()
            with self.connection.cursor() as cursor:
                cursor.execute(sql_content)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Record success
            self.record_migration(migration, execution_time, True)
            
            logger.info(f"✅ Migration completed successfully in {execution_time}ms")
            return True
            
        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            error_message = str(e)
            
            # Record failure
            self.record_migration(migration, execution_time, False, error_message)
            
            logger.error(f"❌ Migration failed: {error_message}")
            return False
    
    def validate_migration(self, migration: Dict) -> bool:
        """Validate migration was applied correctly"""
        try:
            with self.connection.cursor() as cursor:
                if migration["file"] == "001_create_academic_schema.sql":
                    # Check if tables exist
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'academic' AND table_type = 'BASE TABLE'
                    """)
                    table_count = cursor.fetchone()[0]
                    if table_count < 10:  # Expected minimum tables
                        logger.error(f"❌ Validation failed: Expected at least 10 tables, found {table_count}")
                        return False
                
                elif migration["file"] == "002_seed_zimbabwe_data.sql":
                    # Check if seed data exists
                    cursor.execute("SELECT COUNT(*) FROM academic.subjects WHERE is_core = TRUE")
                    core_subjects = cursor.fetchone()[0]
                    if core_subjects < 5:  # Expected core subjects
                        logger.error(f"❌ Validation failed: Expected at least 5 core subjects, found {core_subjects}")
                        return False
                
                elif migration["file"] == "003_performance_optimizations.sql":
                    # Check if materialized views exist
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'academic' AND table_type = 'VIEW'
                    """)
                    view_count = cursor.fetchone()[0]
                    if view_count < 3:  # Expected materialized views
                        logger.error(f"❌ Validation failed: Expected at least 3 views, found {view_count}")
                        return False
                
                elif migration["file"] == "004_rls_security_policies.sql":
                    # Check if RLS is enabled
                    cursor.execute("""
                        SELECT COUNT(*) FROM pg_tables 
                        WHERE schemaname = 'academic' AND rowsecurity = true
                    """)
                    rls_count = cursor.fetchone()[0]
                    if rls_count < 5:  # Expected RLS-enabled tables
                        logger.error(f"❌ Validation failed: Expected at least 5 RLS tables, found {rls_count}")
                        return False
            
            logger.info(f"✅ Migration validation passed: {migration['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration validation failed: {e}")
            return False
    
    def run_all_migrations(self, skip_applied: bool = True, validate: bool = True) -> bool:
        """Run all migrations in sequence"""
        logger.info("🎯 Starting Academic Management database migrations")
        logger.info(f"📁 Migrations directory: {self.migrations_dir}")
        
        success_count = 0
        total_migrations = len(self.migrations)
        
        for i, migration in enumerate(self.migrations, 1):
            logger.info(f"\n📊 Migration {i}/{total_migrations}")
            
            # Check if already applied
            if skip_applied and self.is_migration_applied(migration["name"]):
                logger.info(f"⏭️ Skipping already applied migration: {migration['name']}")
                success_count += 1
                continue
            
            # Run migration
            if self.run_migration(migration):
                if validate and not self.validate_migration(migration):
                    logger.error(f"❌ Migration validation failed, stopping")
                    return False
                success_count += 1
            else:
                if migration["required"]:
                    logger.error(f"❌ Required migration failed, stopping")
                    return False
                else:
                    logger.warning(f"⚠️ Optional migration failed, continuing")
        
        # Summary
        logger.info(f"\n🎉 Migration Summary:")
        logger.info(f"   ✅ Successful: {success_count}/{total_migrations}")
        logger.info(f"   📊 Success rate: {(success_count/total_migrations)*100:.1f}%")
        
        if success_count == total_migrations:
            logger.info("🚀 All Academic Management migrations completed successfully!")
            return True
        else:
            logger.warning("⚠️ Some migrations did not complete successfully")
            return False
    
    def get_migration_status(self) -> List[Dict]:
        """Get status of all migrations"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT migration_name, migration_file, applied_at, 
                           execution_time_ms, success, error_message
                    FROM academic.migration_history 
                    ORDER BY applied_at DESC
                """)
                results = cursor.fetchall()
                
                status = []
                for row in results:
                    status.append({
                        "name": row[0],
                        "file": row[1],
                        "applied_at": row[2].isoformat() if row[2] else None,
                        "execution_time_ms": row[3],
                        "success": row[4],
                        "error_message": row[5]
                    })
                
                return status
        except Exception as e:
            logger.error(f"❌ Failed to get migration status: {e}")
            return []
    
    def rollback_migration(self, migration_name: str) -> bool:
        """Rollback a specific migration (if possible)"""
        logger.warning(f"⚠️ Rollback requested for: {migration_name}")
        logger.warning("🚨 Automatic rollback not implemented - manual intervention required")
        logger.info("📋 To rollback manually:")
        logger.info("   1. Drop academic schema: DROP SCHEMA academic CASCADE;")
        logger.info("   2. Re-run migrations up to desired point")
        return False

def load_db_config() -> Dict[str, str]:
    """Load database configuration from environment or config file"""
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'oneclass_platform'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    # Try to load from config file if exists
    config_file = Path(__file__).parent.parent / "config" / "database.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            logger.warning(f"⚠️ Could not load config file: {e}")
    
    return config

def main():
    """Main migration runner"""
    parser = argparse.ArgumentParser(description='OneClass Academic Management Database Migrations')
    parser.add_argument('--action', choices=['migrate', 'status', 'rollback'], default='migrate',
                       help='Action to perform')
    parser.add_argument('--migration', help='Specific migration name for rollback')
    parser.add_argument('--skip-applied', action='store_true', default=True,
                       help='Skip already applied migrations')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip migration validation')
    parser.add_argument('--config', help='Database config file path')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        with open(args.config) as f:
            db_config = json.load(f)
    else:
        db_config = load_db_config()
    
    # Create migration runner
    runner = AcademicMigrationRunner(db_config)
    
    try:
        # Connect to database
        if not runner.connect():
            sys.exit(1)
        
        # Create migration tracking table
        runner.create_migration_table()
        
        # Execute requested action
        if args.action == 'migrate':
            success = runner.run_all_migrations(
                skip_applied=args.skip_applied,
                validate=not args.no_validate
            )
            sys.exit(0 if success else 1)
            
        elif args.action == 'status':
            status = runner.get_migration_status()
            if status:
                logger.info("\n📊 Migration Status:")
                for migration in status:
                    status_emoji = "✅" if migration["success"] else "❌"
                    logger.info(f"   {status_emoji} {migration['name']}")
                    logger.info(f"      📁 File: {migration['file']}")
                    logger.info(f"      ⏰ Applied: {migration['applied_at']}")
                    logger.info(f"      ⚡ Time: {migration['execution_time_ms']}ms")
                    if migration['error_message']:
                        logger.info(f"      ❌ Error: {migration['error_message']}")
                    logger.info("")
            else:
                logger.info("📋 No migrations found")
                
        elif args.action == 'rollback':
            if not args.migration:
                logger.error("❌ Migration name required for rollback")
                sys.exit(1)
            success = runner.rollback_migration(args.migration)
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Migration runner failed: {e}")
        sys.exit(1)
    finally:
        runner.disconnect()

if __name__ == "__main__":
    main()