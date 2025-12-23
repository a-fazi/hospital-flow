"""
Datenbankoperationen für HospitalFlow
SQLite-Datenbank mit ausschließlich aggregierten Daten (keine personenbezogenen Informationen)
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
        """Initialisiere Datenbankschema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Metriken-Tabelle (Live-Metriken)
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
        
        # Vorhersagen-Tabelle
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
        
        # Warnungen-Tabelle
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
        
        # Empfehlungen-Tabelle
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
        
        # Migriere bestehende Empfehlungen-Tabelle, falls neue Spalten nicht existieren
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
        
        # Prüfprotokoll
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
        
        # Transportanfragen
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
        
        # Inventar
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
        
        # Gerätewartung
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
        
        # Entlassungsplanung (aggregiert)
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
        
        # Kapazitätsübersicht
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
        """Fülle Datenbank mit Beispiel-Aggregatdaten"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Prüfe, ob Daten bereits existieren
        cursor.execute("SELECT COUNT(*) FROM metrics")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        departments = ["Notaufnahme", "Intensivstation", "Chirurgie", "Kardiologie", "Allgemeinstation"]
        now = datetime.utcnow()
        
        # Metriken einfügen
        for i in range(20):
            metric_type = random.choice(["patient_count", "wait_time", "throughput", "occupancy"])
            # Assign proper units based on metric type
            if metric_type == "wait_time":
                unit = "minutes"
                value = random.uniform(5, 30)
            elif metric_type == "throughput":
                unit = "per_hour"
                value = random.uniform(10, 50)
            elif metric_type == "patient_count":
                unit = "count"
                value = random.uniform(5, 50)
            else:  # occupancy
                unit = "percent"
                value = random.uniform(50, 95)
            
            cursor.execute("""
                INSERT INTO metrics (timestamp, metric_type, value, unit, department)
                VALUES (?, ?, ?, ?, ?)
            """, (
                now - timedelta(minutes=random.randint(0, 60)),
                metric_type,
                value,
                unit,
                random.choice(departments)
            ))
        
        # Vorhersagen einfügen
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
        
        # Warnungen einfügen
        alerts_data = [
            ("Kapazität", "hoch", "Intensivstation-Kapazität bei 92%", "Intensivstation", 0, 0),
            ("Inventar", "mittel", "Sauerstoffflaschen unter Schwellenwert", "Notaufnahme", 0, 0),
            ("Gerät", "hoch", "Beatmungsgerät #V-203 benötigt Wartung", "Intensivstation", 0, 0),
            ("Transport", "niedrig", "Transportverzögerung: 15 Min.", "Chirurgie", 1, 0),
        ]
        for alert in alerts_data:
            cursor.execute("""
                INSERT INTO alerts (timestamp, alert_type, severity, message, department, acknowledged, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now - timedelta(minutes=random.randint(5, 120)), *alert))
        
        # Empfehlungen mit neuem Template-Format einfügen
        recs_data = [
            (
                "capacity", 
                "Erwägen Sie das Öffnen von Überlaufbetten",
                "ICU-Auslastung hoch. Öffnen Sie 3 Überlaufbetten.",
                "hoch",
                "ICU",
                "Öffnen Sie vorübergehend 3 Überlaufbetten im ICU-Bereich.",
                "ICU-Kapazität bei 92% mit steigendem Trend. Aktuelle Belegung: 23/25 Betten.",
                "Wartezeiten um 15-20 Minuten reduzieren. Kapazitätsüberlauf in den nächsten 30 Minuten verhindern.",
                "Überprüfen Sie die Ausrüstungsbereitschaft der Überlaufbetten. Bestätigen Sie die Verfügbarkeit des Personals für zusätzliche Betten.",
                "hoch"
            ),
            (
                "staffing",
                "Pflegekraft in die Notaufnahme umsetzen",
                "Wartezeiten in der Notaufnahme steigen. Versetzen Sie 1 Pflegekraft von der Allgemeinstation.",
                "mittel",
                "ER",
                "Versetzen Sie vorübergehend 1 Mitarbeiter von Station B für 20 Minuten in die Notaufnahme.",
                "Notaufnahme-Belastung steigt + Warteschlange nimmt zu. Aktuelle Wartezeit: 8 Patienten, Ø 12 Min.",
                "Voraussichtliche Entlastung in 10 Minuten. Wartezeiten um 25-30% senken.",
                "Menschliche Kontrolle: Verfügbarkeit vor Umsetzung prüfen. Station B Abdeckung sicherstellen.",
                "mittel"
            ),
            (
                "inventory",
                "Zusätzliche Vorräte bestellen",
                "Sauerstoffflaschenbestand bei 15%. Bestellen Sie 20 Einheiten.",
                "hoch",
                "ER",
                "Bestellen Sie sofort 20 Sauerstoffflaschen für die Notaufnahme.",
                "Sauerstoffflaschenbestand bei 15% (3/20 Einheiten). Verbrauchsrate zeigt Engpassrisiko in 4-6 Stunden.",
                "Versorgungsengpass verhindern. Kontinuierliche Patientenversorgung sicherstellen.",
                "Lieferantenverfügbarkeit und Lieferzeit prüfen. Notfall-Lieferanten ggf. berücksichtigen.",
                "hoch"
            ),
        ]
        for rec in recs_data:
            rec_type, title, description, priority, department, action, reason, expected_impact, safety_note, explanation_score = rec
            cursor.execute("""
                INSERT INTO recommendations (timestamp, rec_type, title, description, priority, department, status, action, reason, expected_impact, safety_note, explanation_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now - timedelta(minutes=random.randint(10, 180)), rec_type, title, description, priority, department, "pending", action, reason, expected_impact, safety_note, explanation_score))
        
        # Transport einfügen
        transport_data = [
            ("Patient", "Notaufnahme", "Intensivstation", "hoch", "in_bearbeitung", 10, None),
            ("Ausrüstung", "Lager", "Chirurgie", "mittel", "ausstehend", 15, None),
            ("Probe", "Labor", "Pathologie", "niedrig", "abgeschlossen", 8, 7),
        ]
        for trans in transport_data:
            cursor.execute("""
                INSERT INTO transport (timestamp, request_type, from_location, to_location, priority, status, estimated_time_minutes, actual_time_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now - timedelta(minutes=random.randint(5, 60)), *trans))
        
        # Inventar einfügen
        inventory_items = [
            ("Sauerstoffflaschen", "Medizinische Gase", 15, 20, 100, "Notaufnahme", "Einheiten"),
            ("Infusionslösungen", "Versorgung", 45, 30, 200, "Intensivstation", "Einheiten"),
            ("OP-Masken", "PSA", 120, 50, 500, "Chirurgie", "Boxen"),
            ("Beatmungsfilter", "Ausrüstung", 8, 10, 50, "Intensivstation", "Einheiten"),
        ]
        for item in inventory_items:
            cursor.execute("""
                INSERT INTO inventory (timestamp, item_name, category, current_stock, min_threshold, max_capacity, department, unit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, *item))
        
        # Gerätewartung einfügen
        devices = [
            ("V-203", "Beatmungsgerät", "Intensivstation", "hoch", "2024-01-15", "2024-02-15", 3200, "in_betrieb"),
            ("M-501", "Monitor", "Notaufnahme", "mittel", "2024-01-20", "2024-03-20", 2400, "in_betrieb"),
            ("D-102", "Defibrillator", "Kardiologie", "niedrig", "2024-02-01", "2024-05-01", 1800, "in_betrieb"),
        ]
        for device in devices:
            cursor.execute("""
                INSERT INTO device_maintenance (timestamp, device_id, device_type, department, risk_level, last_maintenance, next_maintenance_due, usage_hours, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, *device))
        
        # Entlassungsplanung einfügen
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
        
        # Kapazität einfügen
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
        """Hole aktuelle Metriken"""
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
        """Hole Metriken der letzten N Minuten"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
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
        """Hole Vorhersagen für die nächsten N Minuten"""
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
        """Hole nicht bestätigte Warnungen"""
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
        """Hole Warnungen innerhalb des Zeitraums"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
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
        """Hole ausstehende Empfehlungen"""
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
        """Hole Empfehlungen gefiltert nach Rolle (all, nurse, doctor, manager)"""
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
            # In einer echten App hätten Empfehlungen ein Rollenfeld
            # Für MVP filtern wir nach rec_type oder Abteilung
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
        """Akzeptiere eine Empfehlung"""
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
        # Randomize role for demo purposes
        roles = ['nurse', 'doctor', 'admin', 'manager']
        role = random.choice(roles)
        self.log_audit("recommendation_accepted", role, "recommendation", rec_id, f"Action: {action_taken}")
        conn.close()
    
    def reject_recommendation(self, rec_id: int, reason: str):
        """Lehne eine Empfehlung ab"""
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
        # Randomize role for demo purposes
        roles = ['nurse', 'doctor', 'admin', 'manager']
        role = random.choice(roles)
        self.log_audit("recommendation_rejected", role, "recommendation", rec_id, f"Reason: {reason}")
        conn.close()
    
    def acknowledge_alert(self, alert_id: int):
        """Bestätige eine Warnung"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts
            SET acknowledged = 1
        # Randomize role for demo purposes
        roles = ['nurse', 'doctor', 'admin', 'manager']
        role = random.choice(roles)
        self.log_audit("alert_acknowledged", role
        """, (alert_id,))
        conn.commit()
        self.log_audit("alert_acknowledged", "staff", "alert", alert_id, "")
        conn.close()
    
    def get_transport_requests(self, status: Optional[str] = None) -> List[Dict]:
        """Hole Transportanfragen"""
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
        """Hole Inventarstatus"""
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
        """Hole Gerätewartungsrisiken"""
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
        """Hole aggregierte Entlassungsplanungsdaten"""
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
        """Hole Kapazitätsübersicht"""
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
        """Hole Prüfprotokoll"""
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
        """Protokolliere ein Prüfereignis"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (action_type, user_role, entity_type, entity_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (action_type, user_role, entity_type, entity_id, details, "127.0.0.1"))
        conn.commit()
        conn.close()

