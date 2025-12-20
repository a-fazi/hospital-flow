"""
Database operations for HospitalFlow
SQLite database with aggregated data only (no personal information)
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random


class HospitalDB:
    def __init__(self, db_path: str = "hospitalflow.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Metrics table (live metrics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                department TEXT
            )
        """)
        
        # Predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                prediction_type TEXT NOT NULL,
                predicted_value REAL NOT NULL,
                confidence REAL,
                time_horizon_minutes INTEGER,
                department TEXT
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                department TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                resolved BOOLEAN DEFAULT 0
            )
        """)
        
        # Recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                rec_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                department TEXT,
                status TEXT DEFAULT 'pending',
                action_taken TEXT,
                action_timestamp DATETIME,
                action TEXT,
                reason TEXT,
                expected_impact TEXT,
                safety_note TEXT,
                explanation_score TEXT
            )
        """)
        
        # Migrate existing recommendations table if new columns don't exist
        try:
            cursor.execute("ALTER TABLE recommendations ADD COLUMN action TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE recommendations ADD COLUMN reason TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE recommendations ADD COLUMN expected_impact TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE recommendations ADD COLUMN safety_note TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE recommendations ADD COLUMN explanation_score TEXT")
        except:
            pass
        
        # Audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT NOT NULL,
                user_role TEXT,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                ip_address TEXT
            )
        """)
        
        # Transport requests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transport (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                request_type TEXT NOT NULL,
                from_location TEXT NOT NULL,
                to_location TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                estimated_time_minutes INTEGER,
                actual_time_minutes INTEGER
            )
        """)
        
        # Inventory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                current_stock INTEGER NOT NULL,
                min_threshold INTEGER NOT NULL,
                max_capacity INTEGER NOT NULL,
                department TEXT,
                unit TEXT
            )
        """)
        
        # Device maintenance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                device_id TEXT NOT NULL,
                device_type TEXT NOT NULL,
                department TEXT,
                risk_level TEXT NOT NULL,
                last_maintenance DATE,
                next_maintenance_due DATE,
                usage_hours INTEGER,
                status TEXT DEFAULT 'operational'
            )
        """)
        
        # Discharge planning (aggregated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discharge_planning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                department TEXT NOT NULL,
                ready_for_discharge_count INTEGER DEFAULT 0,
                pending_discharge_count INTEGER DEFAULT 0,
                avg_length_of_stay_hours REAL,
                discharge_capacity_utilization REAL
            )
        """)
        
        # Capacity overview
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capacity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                department TEXT NOT NULL,
                total_beds INTEGER NOT NULL,
                occupied_beds INTEGER NOT NULL,
                available_beds INTEGER NOT NULL,
                utilization_rate REAL NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        self.seed_sample_data()
    
    def seed_sample_data(self):
        """Seed database with sample aggregated data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM metrics")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        departments = ["ER", "ICU", "Surgery", "Cardiology", "General Ward"]
        now = datetime.now()
        
        # Seed metrics
        for i in range(20):
            cursor.execute("""
                INSERT INTO metrics (timestamp, metric_type, value, unit, department)
                VALUES (?, ?, ?, ?, ?)
            """, (
                now - timedelta(minutes=random.randint(0, 60)),
                random.choice(["patient_count", "wait_time", "throughput", "occupancy"]),
                random.uniform(10, 100),
                random.choice(["count", "minutes", "per_hour", "percent"]),
                random.choice(departments)
            ))
        
        # Seed predictions
        for i in range(10):
            cursor.execute("""
                INSERT INTO predictions (timestamp, prediction_type, predicted_value, confidence, time_horizon_minutes, department)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                now,
                random.choice(["patient_arrival", "bed_demand", "resource_needed"]),
                random.uniform(5, 50),
                random.uniform(0.7, 0.95),
                random.choice([5, 10, 15]),
                random.choice(departments)
            ))
        
        # Seed alerts
        alerts_data = [
            ("capacity", "high", "ICU capacity at 92%", "ICU", 0, 0),
            ("inventory", "medium", "Oxygen tanks below threshold", "ER", 0, 0),
            ("device", "high", "Ventilator #V-203 requires maintenance", "ICU", 0, 0),
            ("transport", "low", "Transport delay: 15 min", "Surgery", 1, 0),
        ]
        for alert in alerts_data:
            cursor.execute("""
                INSERT INTO alerts (timestamp, alert_type, severity, message, department, acknowledged, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now - timedelta(minutes=random.randint(5, 120)), *alert))
        
        # Seed recommendations with new template format
        recs_data = [
            (
                "capacity", 
                "Consider opening overflow beds",
                "ICU utilization high. Open 3 overflow beds.",
                "high",
                "ICU",
                "Temporarily open 3 overflow beds in ICU wing.",
                "ICU capacity at 92% with upward trend. Current occupancy: 23/25 beds.",
                "Reduce wait times by 15-20 minutes. Prevent capacity overflow in next 30 minutes.",
                "Verify overflow bed equipment readiness. Confirm staff availability for additional beds.",
                "high"
            ),
            (
                "staffing",
                "Reassign nurse to ER",
                "ER wait times increasing. Move 1 nurse from General Ward.",
                "medium",
                "ER",
                "Temporarily reassign 1 staff from Station B to ED for 20 minutes.",
                "ED load rising + waiting count trending upward. Current wait: 8 patients, avg 12 min.",
                "Reduce predicted congestion in 10 minutes. Lower wait times by 25-30%.",
                "Human-in-the-loop; confirm availability before reassignment. Check Station B coverage.",
                "medium"
            ),
            (
                "inventory",
                "Order additional supplies",
                "Oxygen tank stock at 15%. Order 20 units.",
                "high",
                "ER",
                "Order 20 oxygen tank units for ER department immediately.",
                "Oxygen tank stock at 15% (3/20 units). Consumption rate indicates stockout risk in 4-6 hours.",
                "Prevent supply shortage. Maintain continuous patient care without interruption.",
                "Verify supplier availability and delivery time. Consider emergency backup supplier if needed.",
                "high"
            ),
        ]
        for rec in recs_data:
            rec_type, title, description, priority, department, action, reason, expected_impact, safety_note, explanation_score = rec
            cursor.execute("""
                INSERT INTO recommendations (timestamp, rec_type, title, description, priority, department, status, action, reason, expected_impact, safety_note, explanation_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now - timedelta(minutes=random.randint(10, 180)), rec_type, title, description, priority, department, "pending", action, reason, expected_impact, safety_note, explanation_score))
        
        # Seed transport
        transport_data = [
            ("patient", "ER", "ICU", "high", "in_progress", 10, None),
            ("equipment", "Storage", "Surgery", "medium", "pending", 15, None),
            ("specimen", "Lab", "Pathology", "low", "completed", 8, 7),
        ]
        for trans in transport_data:
            cursor.execute("""
                INSERT INTO transport (timestamp, request_type, from_location, to_location, priority, status, estimated_time_minutes, actual_time_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now - timedelta(minutes=random.randint(5, 60)), *trans))
        
        # Seed inventory
        inventory_items = [
            ("Oxygen Tanks", "Medical Gases", 15, 20, 100, "ER", "units"),
            ("IV Fluids", "Supplies", 45, 30, 200, "ICU", "units"),
            ("Surgical Masks", "PPE", 120, 50, 500, "Surgery", "boxes"),
            ("Ventilator Filters", "Equipment", 8, 10, 50, "ICU", "units"),
        ]
        for item in inventory_items:
            cursor.execute("""
                INSERT INTO inventory (timestamp, item_name, category, current_stock, min_threshold, max_capacity, department, unit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, *item))
        
        # Seed device maintenance
        devices = [
            ("V-203", "Ventilator", "ICU", "high", "2024-01-15", "2024-02-15", 3200, "operational"),
            ("M-501", "Monitor", "ER", "medium", "2024-01-20", "2024-03-20", 2400, "operational"),
            ("D-102", "Defibrillator", "Cardiology", "low", "2024-02-01", "2024-05-01", 1800, "operational"),
        ]
        for device in devices:
            cursor.execute("""
                INSERT INTO device_maintenance (timestamp, device_id, device_type, department, risk_level, last_maintenance, next_maintenance_due, usage_hours, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, *device))
        
        # Seed discharge planning
        for dept in departments:
            cursor.execute("""
                INSERT INTO discharge_planning (timestamp, department, ready_for_discharge_count, pending_discharge_count, avg_length_of_stay_hours, discharge_capacity_utilization)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                now,
                dept,
                random.randint(0, 5),
                random.randint(2, 8),
                random.uniform(24, 120),
                random.uniform(0.3, 0.9)
            ))
        
        # Seed capacity
        for dept in departments:
            total = random.randint(20, 50)
            occupied = random.randint(10, total - 5)
            available = total - occupied
            cursor.execute("""
                INSERT INTO capacity (timestamp, department, total_beds, occupied_beds, available_beds, utilization_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now, dept, total, occupied, available, occupied / total))
        
        conn.commit()
        conn.close()
    
    def get_recent_metrics(self, limit: int = 10) -> List[Dict]:
        """Get recent metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM metrics
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_metrics_last_n_minutes(self, minutes: int = 60, metric_type: Optional[str] = None) -> List[Dict]:
        """Get metrics from the last N minutes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        if metric_type:
            cursor.execute("""
                SELECT * FROM metrics
                WHERE timestamp >= ? AND metric_type = ?
                ORDER BY timestamp ASC
            """, (cutoff_time, metric_type))
        else:
            cursor.execute("""
                SELECT * FROM metrics
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff_time,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_predictions(self, minutes_ahead: int = 15) -> List[Dict]:
        """Get predictions for next N minutes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM predictions
            WHERE time_horizon_minutes <= ?
            ORDER BY timestamp DESC, time_horizon_minutes ASC
        """, (minutes_ahead,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_active_alerts(self) -> List[Dict]:
        """Get unacknowledged alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM alerts
            WHERE resolved = 0
            ORDER BY 
                CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                timestamp DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_alerts_by_time_range(self, hours: int = 24) -> List[Dict]:
        """Get alerts within time range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT * FROM alerts
            WHERE timestamp >= ?
            ORDER BY 
                CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                timestamp DESC
        """, (cutoff_time,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_pending_recommendations(self) -> List[Dict]:
        """Get pending recommendations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM recommendations
            WHERE status = 'pending'
            ORDER BY 
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                timestamp DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_recommendations_by_role(self, role: str = "all") -> List[Dict]:
        """Get recommendations filtered by role (all, nurse, doctor, manager)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if role == "all":
            cursor.execute("""
                SELECT * FROM recommendations
                WHERE status = 'pending'
                ORDER BY 
                    CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                    timestamp DESC
            """)
        else:
            # In a real app, recommendations would have a role field
            # For MVP, we'll filter by rec_type or department
            cursor.execute("""
                SELECT * FROM recommendations
                WHERE status = 'pending'
                ORDER BY 
                    CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                    timestamp DESC
            """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def accept_recommendation(self, rec_id: int, action_taken: str):
        """Accept a recommendation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE recommendations
            SET status = 'accepted',
                action_taken = ?,
                action_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (action_taken, rec_id))
        conn.commit()
        self.log_audit("recommendation_accepted", "staff", "recommendation", rec_id, f"Action: {action_taken}")
        conn.close()
    
    def reject_recommendation(self, rec_id: int, reason: str):
        """Reject a recommendation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE recommendations
            SET status = 'rejected',
                action_taken = ?,
                action_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reason, rec_id))
        conn.commit()
        self.log_audit("recommendation_rejected", "staff", "recommendation", rec_id, f"Reason: {reason}")
        conn.close()
    
    def acknowledge_alert(self, alert_id: int):
        """Acknowledge an alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts
            SET acknowledged = 1
            WHERE id = ?
        """, (alert_id,))
        conn.commit()
        self.log_audit("alert_acknowledged", "staff", "alert", alert_id, "")
        conn.close()
    
    def get_transport_requests(self, status: Optional[str] = None) -> List[Dict]:
        """Get transport requests"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("""
                SELECT * FROM transport
                WHERE status = ?
                ORDER BY 
                    CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                    timestamp DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT * FROM transport
                ORDER BY 
                    CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                    timestamp DESC
            """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_inventory_status(self) -> List[Dict]:
        """Get inventory status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM inventory
            ORDER BY 
                CASE WHEN current_stock < min_threshold THEN 1 ELSE 2 END,
                department, item_name
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_device_maintenance_risks(self) -> List[Dict]:
        """Get device maintenance risks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM device_maintenance
            ORDER BY 
                CASE risk_level WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
                next_maintenance_due ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_discharge_planning(self) -> List[Dict]:
        """Get discharge planning aggregated data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM discharge_planning
            ORDER BY department
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_capacity_overview(self) -> List[Dict]:
        """Get capacity overview"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM capacity
            ORDER BY utilization_rate DESC, department
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """Get audit log"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def log_audit(self, action_type: str, user_role: str, entity_type: str, entity_id: int, details: str):
        """Log an audit event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (action_type, user_role, entity_type, entity_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (action_type, user_role, entity_type, entity_id, details, "127.0.0.1"))
        conn.commit()
        conn.close()

