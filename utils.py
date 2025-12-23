"""
Hilfsfunktionen für HospitalFlow
Vorhersagen, Berechnungen und Formatierungshelfer
"""
from datetime import datetime, timedelta
from typing import Dict, List
import random


def calculate_prediction_confidence(base_value: float, time_horizon: int) -> float:
    """Berechne Prognose-Vertrauen basierend auf dem Zeithorizont"""
    # Kürzere Horizonte = höheres Vertrauen
    confidence = max(0.6, 1.0 - (time_horizon / 60) * 0.3)
    return round(confidence, 2)


def format_time_ago(timestamp: str) -> str:
    """Formatiere Zeitstempel als relative Zeit"""
    if isinstance(timestamp, str):
        try:
            # Versuche zuerst ISO-Format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            try:
                # Versuche SQLite-Datumsformat mit Mikrosekunden
                # SQLite CURRENT_TIMESTAMP gibt UTC zurück, also als UTC behandeln
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    # Versuche SQLite-Datumsformat ohne Mikrosekunden
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except:
                    # Fallback auf "kürzlich", wenn das Parsen fehlschlägt
                    return "kürzlich"
    else:
        dt = timestamp
    
    # Verwende datetime.now() für Vergleich (lokale Zeit)
    # Da SQLite CURRENT_TIMESTAMP in UTC ist, aber als String ohne Timezone gespeichert wird,
    # und die Simulation datetime.now() für Timestamps verwendet, bleiben wir bei lokalem Vergleich
    now = datetime.now()
    diff = now - dt
    
    if diff.total_seconds() < 60:
        return "gerade eben"
    elif diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"vor {mins} Min."
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"vor {hours} Std."
    else:
        days = int(diff.total_seconds() / 86400)
        return f"vor {days} Tg."


def get_severity_color(severity: str) -> str:
    """Farbe für Schweregrad-Badge ermitteln"""
    farben = {
        "hoch": "#DC2626",      # rot-600
        "mittel": "#F59E0B",    # bernstein-500
        "niedrig": "#10B981",   # smaragd-500
        "kritisch": "#991B1B",  # rot-800
        # Für Kompatibilität mit englischen Keys:
        "high": "#DC2626",
        "medium": "#F59E0B",
        "low": "#10B981",
        "critical": "#991B1B",
    }
    return farben.get(severity.lower(), "#6B7280")


def get_priority_color(priority: str) -> str:
    """Farbe für Prioritäts-Badge ermitteln"""
    return get_severity_color(priority)


def get_risk_color(risk_level: str) -> str:
    """Farbe für Risikostufen-Badge ermitteln (unterstützt Deutsch und Englisch)"""
    return get_severity_color(risk_level)


def get_status_color(status: str) -> str:
    """Farbe für Status-Badge ermitteln"""
    farben = {
        # Deutsch
        "ausstehend": "#F59E0B",      # bernstein-500
        "in_bearbeitung": "#3B82F6",  # blau-500
        "abgeschlossen": "#10B981",   # smaragd-500
        "akzeptiert": "#10B981",      # smaragd-500
        "abgelehnt": "#EF4444",       # rot-500
        "betriebsbereit": "#10B981",  # smaragd-500
        "wartung": "#F59E0B",         # bernstein-500
        "kritisch": "#DC2626",        # rot-600
        # Englisch (Kompatibilität)
        "pending": "#F59E0B",
        "in_progress": "#3B82F6",
        "completed": "#10B981",
        "accepted": "#10B981",
        "rejected": "#EF4444",
        "operational": "#10B981",
        "maintenance": "#F59E0B",
        "critical": "#DC2626",
    }
    return farben.get(status.lower(), "#6B7280")


def calculate_inventory_status(current: int, min_threshold: int, max_capacity: int) -> Dict:
    """Berechne Lagerstatus und Prozentsatz"""
    prozent = (current / max_capacity) * 100 if max_capacity > 0 else 0
    ist_niedrig = current < min_threshold
    ist_kritisch = current < (min_threshold * 0.5)
    # Status sowohl auf Deutsch als auch Englisch für Kompatibilität
    if ist_kritisch:
        status = "kritisch"
        status_en = "critical"
    elif ist_niedrig:
        status = "niedrig"
        status_en = "low"
    else:
        status = "normal"
        status_en = "normal"
    return {
        "percentage": round(prozent, 1),
        "is_low": ist_niedrig,
        "is_critical": ist_kritisch,
        "status": status,
        "status_en": status_en
    }


def calculate_capacity_status(utilization: float) -> Dict:
    """Berechne Kapazitätsstatus"""
    if utilization >= 0.9:
        status = "kritisch"
        status_en = "critical"
        color = "#DC2626"
    elif utilization >= 0.75:
        status = "hoch"
        status_en = "high"
        color = "#F59E0B"
    elif utilization >= 0.5:
        status = "moderat"
        status_en = "moderate"
        color = "#3B82F6"
    else:
        status = "niedrig"
        status_en = "low"
        color = "#10B981"
    return {
        "status": status,
        "status_en": status_en,
        "color": color,
        "percentage": round(utilization * 100, 1)
    }


def generate_short_term_prediction(current_value: float, trend: str = "stable") -> Dict:
    """Erzeuge 5-15 Minuten Prognosen"""
    # Einfache Prognoselogik
    if trend == "increasing":
        multiplikator = 1.1
    elif trend == "decreasing":
        multiplikator = 0.9
    else:
        multiplikator = 1.0
    
    prognosen = []
    for minuten in [5, 10, 15]:
        prognosewert = current_value * (multiplikator ** (minuten / 10))
        vertrauen = calculate_prediction_confidence(prognosewert, minuten)
        prognosen.append({
            "minuten": minuten,
            "wert": round(prognosewert, 1),
            "vertrauen": vertrauen
        })
    
    return prognosen


def format_duration_minutes(minutes: int) -> str:
    """Formatiere Dauer in Minuten als lesbare Zeichenkette"""
    if minutes < 60:
        return f"{minutes} Min."
    else:
        stunden = minutes // 60
        minuten = minutes % 60
        if minuten == 0:
            return f"{stunden} Std."
        return f"{stunden} Std. {minuten} Min."


def get_department_color(department: str) -> str:
    """Gibt eine konsistente Farbe für die Abteilung zurück"""
    farben = {
        "ER": "#EF4444",              # Notaufnahme
        "ICU": "#DC2626",             # Intensivstation
        "Surgery": "#3B82F6",         # Chirurgie
        "Cardiology": "#8B5CF6",      # Kardiologie
        "General Ward": "#10B981",    # Allgemeinstation
        # Deutsche Abteilungsnamen für Kompatibilität
        "Notaufnahme": "#EF4444",
        "Intensivstation": "#DC2626",
        "Chirurgie": "#3B82F6",
        "Kardiologie": "#8B5CF6",
        "Allgemeinstation": "#10B981",
    }
    return farben.get(department, "#6B7280")


def calculate_device_risk_score(usage_hours: int, days_until_maintenance: int) -> str:
    """Berechne das Wartungsrisiko eines Geräts"""
    if days_until_maintenance < 7 or usage_hours > 3000:
        return "hoch"
    elif days_until_maintenance < 30 or usage_hours > 2500:
        return "mittel"
    else:
        return "niedrig"


def get_system_status() -> tuple[str, str]:
    """Gibt den aktuellen Systemstatus zurück (Status, Farbe)"""
    # In einer echten App würde hier der Systemzustand geprüft
    # Für das MVP: immer "betriebsbereit"
    return "betriebsbereit", "#10B981"


def calculate_metric_severity(value: float, thresholds: dict) -> tuple[str, str]:
    """
    Berechne Schweregrad basierend auf Wert und Schwellenwerten
    Rückgabe: (schweregrad, hinweis_text)
    thresholds: {'critical': max, 'watch': max, 'stable': max}
    """
    if value >= thresholds.get('critical', 90):
        return 'hoch', 'Kritisch'
    elif value >= thresholds.get('watch', 70):
        return 'mittel', 'Beobachten'
    else:
        return 'niedrig', 'Stabil'


def get_metric_severity_for_load(load_percent: float) -> tuple[str, str]:
    """Gibt den Schweregrad für Auslastungsmetriken (0-100%) zurück"""
    if load_percent >= 90:
        return 'hoch', 'Kritisch'
    elif load_percent >= 75:
        return 'mittel', 'Beobachten'
    else:
        return 'niedrig', 'Stabil'


def get_metric_severity_for_count(count: int, thresholds: dict) -> tuple[str, str]:
    """Ermittle Schweregrad für zählbasierte Metriken"""
    if count >= thresholds.get('critical', 20):
        return 'high', 'Kritisch'
    elif count >= thresholds.get('watch', 10):
        return 'medium', 'Beobachten'
    else:
        return 'low', 'Stabil'


def get_metric_severity_for_free(free: int, total: int) -> tuple[str, str]:
    """Ermittle Schweregrad für freie/verfügbare Metriken (niedriger ist schlechter)"""
    if total == 0:
        return 'high', 'Kritisch'
    free_percent = (free / total) * 100
    if free_percent <= 5:
        return 'high', 'Kritisch'
    elif free_percent <= 15:
        return 'medium', 'Beobachten'
    else:
        return 'low', 'Stabil'


def calculate_explanation_score(trend_strength: float, data_points: int, confidence: float) -> str:
    """
    Erkläre den Erklärungsscore (niedrig/mittel/hoch) basierend auf Trendstärke
    trend_strength: 0-1 (wie stark ist der Trend)
    data_points: Anzahl der verwendeten Datenpunkte
    confidence: 0-1 (Prognose-Vertrauen)
    """
    # Faktoren kombinieren
    score = (trend_strength * 0.4) + (min(data_points / 20, 1.0) * 0.3) + (confidence * 0.3)
    
    if score >= 0.7:
        return "hoch"
    elif score >= 0.4:
        return "mittel"
    else:
        return "niedrig"


def get_explanation_score_color(score: str) -> str:
    """Farbe für Erklärungsscore-Badge ermitteln"""
    farben = {
        "hoch": "#10B981",    # smaragd-500
        "mittel": "#F59E0B",  # bernstein-500
        "niedrig": "#6B7280", # grau-500
        # Für Kompatibilität mit englischen Keys:
        "high": "#10B981",
        "medium": "#F59E0B",
        "low": "#6B7280",
    }
    return farben.get(score.lower(), "#6B7280")

