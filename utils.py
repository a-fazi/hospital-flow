"""
Utility functions for HospitalFlow
Predictions, calculations, and formatting helpers
"""
from datetime import datetime, timedelta
from typing import Dict, List
import random


def calculate_prediction_confidence(base_value: float, time_horizon: int) -> float:
    """Calculate prediction confidence based on time horizon"""
    # Shorter horizons = higher confidence
    confidence = max(0.6, 1.0 - (time_horizon / 60) * 0.3)
    return round(confidence, 2)


def format_time_ago(timestamp: str) -> str:
    """Format timestamp as relative time"""
    if isinstance(timestamp, str):
        try:
            # Try ISO format first
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            try:
                # Try SQLite datetime format
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except:
                # Fallback to current time if parsing fails
                return "kürzlich"
    else:
        dt = timestamp
    
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
    """Get color for severity badge"""
    colors = {
        "high": "#DC2626",      # red-600
        "medium": "#F59E0B",    # amber-500
        "low": "#10B981",       # emerald-500
        "critical": "#991B1B",  # red-800
    }
    return colors.get(severity.lower(), "#6B7280")


def get_priority_color(priority: str) -> str:
    """Get color for priority badge"""
    return get_severity_color(priority)


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level badge"""
    return get_severity_color(risk_level)


def get_status_color(status: str) -> str:
    """Get color for status badge"""
    colors = {
        "pending": "#F59E0B",      # amber-500
        "in_progress": "#3B82F6",  # blue-500
        "completed": "#10B981",   # emerald-500
        "accepted": "#10B981",     # emerald-500
        "rejected": "#EF4444",     # red-500
        "operational": "#10B981",  # emerald-500
        "maintenance": "#F59E0B",  # amber-500
        "critical": "#DC2626",     # red-600
    }
    return colors.get(status.lower(), "#6B7280")


def calculate_inventory_status(current: int, min_threshold: int, max_capacity: int) -> Dict:
    """Calculate inventory status and percentage"""
    percentage = (current / max_capacity) * 100 if max_capacity > 0 else 0
    is_low = current < min_threshold
    is_critical = current < (min_threshold * 0.5)
    
    return {
        "percentage": round(percentage, 1),
        "is_low": is_low,
        "is_critical": is_critical,
        "status": "critical" if is_critical else ("low" if is_low else "normal")
    }


def calculate_capacity_status(utilization: float) -> Dict:
    """Calculate capacity status"""
    if utilization >= 0.9:
        status = "critical"
        color = "#DC2626"
    elif utilization >= 0.75:
        status = "high"
        color = "#F59E0B"
    elif utilization >= 0.5:
        status = "moderate"
        color = "#3B82F6"
    else:
        status = "low"
        color = "#10B981"
    
    return {
        "status": status,
        "color": color,
        "percentage": round(utilization * 100, 1)
    }


def generate_short_term_prediction(current_value: float, trend: str = "stable") -> Dict:
    """Generate 5-15 minute predictions"""
    # Simple prediction logic
    if trend == "increasing":
        multiplier = 1.1
    elif trend == "decreasing":
        multiplier = 0.9
    else:
        multiplier = 1.0
    
    predictions = []
    for minutes in [5, 10, 15]:
        predicted = current_value * (multiplier ** (minutes / 10))
        confidence = calculate_prediction_confidence(predicted, minutes)
        predictions.append({
            "minutes": minutes,
            "value": round(predicted, 1),
            "confidence": confidence
        })
    
    return predictions


def format_duration_minutes(minutes: int) -> str:
    """Format duration in minutes to human-readable string"""
    if minutes < 60:
        return f"{minutes}m"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours}h"
        return f"{hours}h {mins}m"


def get_department_color(department: str) -> str:
    """Get consistent color for department"""
    colors = {
        "ER": "#EF4444",           # red-500
        "ICU": "#DC2626",          # red-600
        "Surgery": "#3B82F6",      # blue-500
        "Cardiology": "#8B5CF6",   # violet-500
        "General Ward": "#10B981", # emerald-500
    }
    return colors.get(department, "#6B7280")


def calculate_device_risk_score(usage_hours: int, days_until_maintenance: int) -> str:
    """Calculate device maintenance risk level"""
    if days_until_maintenance < 7 or usage_hours > 3000:
        return "high"
    elif days_until_maintenance < 30 or usage_hours > 2500:
        return "medium"
    else:
        return "low"


def get_system_status() -> tuple[str, str]:
    """Get current system status (status, color)"""
    # In a real app, this would check actual system health
    # For MVP, return operational
    return "operational", "#10B981"


def calculate_metric_severity(value: float, thresholds: dict) -> tuple[str, str]:
    """
    Calculate severity based on value and thresholds
    Returns: (severity, hint_text)
    thresholds: {'critical': max, 'watch': max, 'stable': max}
    """
    if value >= thresholds.get('critical', 90):
        return 'high', 'Kritisch'
    elif value >= thresholds.get('watch', 70):
        return 'medium', 'Beobachten'
    else:
        return 'low', 'Stabil'


def get_metric_severity_for_load(load_percent: float) -> tuple[str, str]:
    """Get severity for load-based metrics (0-100%)"""
    if load_percent >= 90:
        return 'high', 'Kritisch'
    elif load_percent >= 75:
        return 'medium', 'Beobachten'
    else:
        return 'low', 'Stabil'


def get_metric_severity_for_count(count: int, thresholds: dict) -> tuple[str, str]:
    """Get severity for count-based metrics"""
    if count >= thresholds.get('critical', 20):
        return 'high', 'Kritisch'
    elif count >= thresholds.get('watch', 10):
        return 'medium', 'Beobachten'
    else:
        return 'low', 'Stabil'


def get_metric_severity_for_free(free: int, total: int) -> tuple[str, str]:
    """Get severity for free/available metrics (lower is worse)"""
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
    Calculate explanation score (low/medium/high) based on trend strength
    trend_strength: 0-1 (how strong the trend is)
    data_points: number of data points used
    confidence: 0-1 (prediction confidence)
    """
    # Combine factors
    score = (trend_strength * 0.4) + (min(data_points / 20, 1.0) * 0.3) + (confidence * 0.3)
    
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    else:
        return "low"


def get_explanation_score_color(score: str) -> str:
    """Get color for explanation score badge"""
    colors = {
        "high": "#10B981",    # emerald-500
        "medium": "#F59E0B",  # amber-500
        "low": "#6B7280",     # gray-500
    }
    return colors.get(score.lower(), "#6B7280")

