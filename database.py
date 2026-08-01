"""Database management for builder discovery system"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from config import DATABASE_FILE

class BuilderDatabase:
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.init_db()

    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id TEXT UNIQUE,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                license_type TEXT,
                date_discovered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new',
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permit_id TEXT UNIQUE,
                builder_id INTEGER,
                builder_name TEXT,
                property_address TEXT,
                zipcode TEXT,
                lot_size TEXT,
                permit_type TEXT,
                application_type TEXT,
                date_issued TIMESTAMP,
                amount REAL,
                scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(builder_id) REFERENCES builders(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                builder_id INTEGER,
                builder_name TEXT,
                permit_count INTEGER,
                alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_sent_to TEXT,
                FOREIGN KEY(builder_id) REFERENCES builders(id)
            )
        """)

        conn.commit()
        conn.close()

    def add_builder(self, license_id: str, name: str, phone: str = None,
                   email: str = None, license_type: str = None) -> int:
        """Add new builder to database. Returns builder ID."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO builders (license_id, name, phone, email, license_type)
                VALUES (?, ?, ?, ?, ?)
            """, (license_id, name, phone, email, license_type))
            conn.commit()
            builder_id = cursor.lastrowid
            return builder_id
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM builders WHERE license_id = ?", (license_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()

    def get_builder_by_license(self, license_id: str) -> Optional[Dict]:
        """Get builder by license ID"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM builders WHERE license_id = ?", (license_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'id': result[0],
                'license_id': result[1],
                'name': result[2],
                'phone': result[3],
                'email': result[4],
                'license_type': result[5],
                'date_discovered': result[6],
                'status': result[7]
            }
        return None

    def add_permit(self, permit_id: str, builder_id: int, builder_name: str,
                  property_address: str, zipcode: str = None, lot_size: str = None,
                  permit_type: str = None, application_type: str = None,
                  date_issued: str = None, amount: float = None):
        """Add new permit to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO permits (permit_id, builder_id, builder_name, property_address,
                                   zipcode, lot_size, permit_type, application_type,
                                   date_issued, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (permit_id, builder_id, builder_name, property_address, zipcode, lot_size,
                  permit_type, application_type, date_issued, amount))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def get_new_builders_since(self, days: int = 7) -> List[Dict]:
        """Get builders with permits in last N days"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT b.id, b.name, b.license_id, COUNT(p.id) as permit_count,
                   MAX(p.date_issued) as latest_permit
            FROM builders b
            LEFT JOIN permits p ON b.id = p.builder_id
            WHERE p.date_issued >= datetime('now', '-' || ? || ' days')
            GROUP BY b.id
            ORDER BY permit_count DESC
        """, (days,))

        results = cursor.fetchall()
        conn.close()

        return [
            {
                'id': r[0],
                'name': r[1],
                'license_id': r[2],
                'permit_count': r[3],
                'latest_permit': r[4]
            }
            for r in results if r[0] is not None
        ]

    def get_alert_sent_today(self, builder_id: int) -> bool:
        """Check if alert was sent for builder today"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM alerts_sent
            WHERE builder_id = ? AND DATE(alert_date) = DATE('now')
        """, (builder_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] > 0

    def log_alert_sent(self, builder_id: int, builder_name: str, permit_count: int, email: str):
        """Log that an alert was sent"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alerts_sent (builder_id, builder_name, permit_count, email_sent_to)
            VALUES (?, ?, ?, ?)
        """, (builder_id, builder_name, permit_count, email))

        conn.commit()
        conn.close()

    def get_permits_for_builder(self, builder_id: int, days: int = 1) -> List[Dict]:
        """Get recent permits for a specific builder"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT permit_id, builder_name, property_address, zipcode, lot_size,
                   permit_type, application_type, date_issued, amount
            FROM permits
            WHERE builder_id = ? AND DATE(date_issued) = DATE('now')
            ORDER BY date_issued DESC
        """, (builder_id,))

        results = cursor.fetchall()
        conn.close()

        return [
            {
                'permit_id': r[0],
                'builder_name': r[1],
                'property_address': r[2],
                'zipcode': r[3],
                'lot_size': r[4],
                'permit_type': r[5],
                'application_type': r[6],
                'date_issued': r[7],
                'amount': r[8]
            }
            for r in results
        ]
