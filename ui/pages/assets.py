"""
Seitenmodul für Vermögenswerte
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import random
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from ui.components import render_badge, render_empty_state


def render(db, sim, get_cached_alerts=None, get_cached_recommendations=None, get_cached_capacity=None):
    """Rendert die Vermögenswerte-Seite"""
    # Abschnitt Lager-/Inventarrisiko
    st.markdown("### Lagerrisiko")
    st.markdown("")  # Abstand
    
    # Simulierte Inventarmaterialien mit Risiko
    inventory_materials = [
        {"name": "Untersuchungshandschuhe (Nitril)", "current_stock": 45, "min_threshold": 100, "max_capacity": 500, "unit": "Boxen", "department": "Chirurgie", "days_until_stockout": 3},
        {"name": "IV-Katheter (18G)", "current_stock": 12, "min_threshold": 50, "max_capacity": 300, "unit": "Stück", "department": "Notaufnahme", "days_until_stockout": 2},
        {"name": "Antibiotika-Lösung (Ceftriaxon)", "current_stock": 8, "min_threshold": 30, "max_capacity": 200, "unit": "Fläschchen", "department": "Intensivstation", "days_until_stockout": 1},
        {"name": "Sauerstoffmasken (Erwachsene)", "current_stock": 25, "min_threshold": 40, "max_capacity": 150, "unit": "Stück", "department": "Allgemeinstation", "days_until_stockout": 5},
        {"name": "Defibrillator-Pads", "current_stock": 6, "min_threshold": 20, "max_capacity": 100, "unit": "Paare", "department": "Kardiologie", "days_until_stockout": 1},
    ]
    
    # Risiko für jedes Material berechnen
    for material in inventory_materials:
        stock_percent = (material['current_stock'] / material['max_capacity']) * 100
        threshold_percent = (material['min_threshold'] / material['max_capacity']) * 100

        # Risiko auf Deutsch zuweisen
        if material['current_stock'] < material['min_threshold']:
            if material['days_until_stockout'] <= 2:
                risk_level = "hoch"
            else:
                risk_level = "mittel"
        else:
            risk_level = "niedrig"

        material['risk_level'] = risk_level
        material['stock_percent'] = stock_percent
        material['threshold_percent'] = threshold_percent

    # Nach Risiko sortieren (hoch zuerst)
    inventory_materials.sort(key=lambda x: {'hoch': 1, 'mittel': 2, 'niedrig': 3}[x['risk_level']])
    top_5_materials = inventory_materials[:5]

    # Anzeige der Top-5-Risiko-Materialien
    if top_5_materials:
        table_data = []
        for mat in top_5_materials:
            risk_color = get_severity_color(mat['risk_level'])
            risk_badge = render_badge(mat['risk_level'].upper(), mat['risk_level'])
            table_data.append({
                "Material": mat['name'],
                "Aktueller Bestand": f"{mat['current_stock']} {mat['unit']}",
                "Mindestbestand": f"{mat['min_threshold']} {mat['unit']}",
                "Tage bis Engpass": mat['days_until_stockout'],
                "Risiko": risk_badge,
                "Abteilung": mat['department']
            })
        
        df_inv = pd.DataFrame(table_data)
        # Risiko-Spalte als HTML anzeigen
        st.markdown("#### Top 5 Materialien mit Risiko")
        st.markdown("")  # Abstand
        
        # Als formatierte Tabelle anzeigen
        for mat in top_5_materials:
            risk_color = get_severity_color(mat['risk_level'])
            risk_badge = render_badge(mat['risk_level'].upper(), mat['risk_level'])
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {risk_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                    <div>
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{mat['name']}</div>
                        <div style="font-size: 0.75rem; color: #6b7280;">{mat['department']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Aktuell</div>
                        <div style="font-weight: 600; color: #1f2937;">{mat['current_stock']} {mat['unit']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Mindestbestand</div>
                        <div style="font-weight: 600; color: #1f2937;">{mat['min_threshold']} {mat['unit']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Tage bis Engpass</div>
                        <div style="font-weight: 600; color: {risk_color};">{mat['days_until_stockout']} Tage</div>
                    </div>
                    <div>
                        {risk_badge}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Nachfüllvorschläge
    st.markdown("---")
    st.markdown("#### Nachfüllvorschläge")
    st.markdown("")  # Abstand
    
    restock_suggestions = []
    for mat in top_5_materials:
        if mat['risk_level'] in ['high', 'medium']:
            suggested_qty = max(mat['min_threshold'] * 2, mat['min_threshold'] + 50)
            restock_suggestions.append({
                "material": mat['name'],
                "suggested_qty": suggested_qty,
                "current": mat['current_stock'],
                "priority": mat['risk_level']
            })
    
    if restock_suggestions:
        for suggestion in restock_suggestions:
            priority_color = get_severity_color(suggestion['priority'])
            st.markdown(f"""
            <div style="background: #f9fafb; padding: 1rem; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid {priority_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; color: #1f2937;">{suggestion['material']}</div>
                        <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">
                            Aktuell: {suggestion['current']} → Vorgeschlagen: {suggestion['suggested_qty']} Einheiten
                        </div>
                    </div>
                    <div style="font-weight: 600; color: {priority_color};">
                        +{suggestion['suggested_qty'] - suggestion['current']} Einheiten
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("📦", "Keine Nachfüllvorschläge", "Alle Lagerbestände sind ausreichend"), unsafe_allow_html=True)
    
    # Risikoverteilung
    st.markdown("---")
    st.markdown("#### Risikoverteilung")
    st.markdown("")  # Abstand

    # Deutsche Risikostufen
    risk_counts = {'hoch': 0, 'mittel': 0, 'niedrig': 0}
    for mat in inventory_materials:
        risk_counts[mat['risk_level']] = risk_counts.get(mat['risk_level'], 0) + 1

    risikostufen_labels = {"hoch": "Hoch", "mittel": "Mittel", "niedrig": "Niedrig"}
    risikostufen_farben = {"hoch": '#DC2626', "mittel": '#F59E0B', "niedrig": '#10B981'}

    fig_risk = px.bar(
        x=[risikostufen_labels[k] for k in risk_counts.keys()],
        y=list(risk_counts.values()),
        title="",
        labels={'x': 'Risikostufe', 'y': 'Anzahl'},
        color=[risikostufen_labels[k] for k in risk_counts.keys()],
        color_discrete_map={risikostufen_labels[k]: risikostufen_farben[k] for k in risk_counts.keys()}
    )
    fig_risk.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis_title="Risikostufe",
        yaxis_title="Anzahl Materialien"
    )
    st.plotly_chart(fig_risk, use_container_width=True)
    
    st.markdown("---")
    
    # Gerätrisiko-Abschnitt
    st.markdown("### Gerätrisiko")
    st.markdown("")  # Abstand
    
    # Simulated devices with risk
    devices = [
        {"name": "MRI Scanner", "device_id": "MRI-001", "type": "Imaging", "department": "Radiology", "risk_level": "high", "last_maintenance": "2024-01-15", "next_maintenance_due": "2024-02-15", "days_until_due": 5, "usage_hours": 3200, "recommended_window": "Within 3 days"},
        {"name": "CT Scanner", "device_id": "CT-203", "type": "Imaging", "department": "Radiology", "risk_level": "medium", "last_maintenance": "2024-01-20", "next_maintenance_due": "2024-03-20", "days_until_due": 18, "usage_hours": 2400, "recommended_window": "Within 2 weeks"},
        {"name": "X-Ray Machine", "device_id": "XR-501", "type": "Imaging", "department": "ER", "risk_level": "low", "last_maintenance": "2024-02-01", "next_maintenance_due": "2024-05-01", "days_until_due": 45, "usage_hours": 1800, "recommended_window": "Within 4 weeks"},
        {"name": "Ultrasound System", "device_id": "US-102", "type": "Imaging", "department": "Cardiology", "risk_level": "medium", "last_maintenance": "2024-01-25", "next_maintenance_due": "2024-03-25", "days_until_due": 23, "usage_hours": 2100, "recommended_window": "Within 2 weeks"},
        {"name": "Ventilator", "device_id": "V-203", "type": "Life Support", "department": "ICU", "risk_level": "high", "last_maintenance": "2024-01-15", "next_maintenance_due": "2024-02-15", "days_until_due": 5, "usage_hours": 3200, "recommended_window": "Within 3 days"},
        {"name": "Defibrillator", "device_id": "D-102", "type": "Emergency", "department": "Cardiology", "risk_level": "low", "last_maintenance": "2024-02-01", "next_maintenance_due": "2024-05-01", "days_until_due": 45, "usage_hours": 1800, "recommended_window": "Within 4 weeks"},
    ]
    
    # Gerätetabelle anzeigen
    st.markdown("#### Gerätewartungsstatus")
    st.markdown("")  # Abstand
    
    # Mapping für Gerätetypen ins Deutsche
    device_type_map = {
        'Imaging': 'Bildgebung',
        'Life Support': 'Lebensunterstützung',
        'Emergency': 'Notfall',
        'Monitoring': 'Überwachung',
        'Therapy': 'Therapie',
        'Surgical': 'Chirurgisch',
        'Diagnostic': 'Diagnostik',
        'Other': 'Andere',
    }
    # Mapping für Risikostufen ins Deutsche
    risk_level_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig', 'hoch': 'hoch', 'mittel': 'mittel', 'niedrig': 'niedrig'}
    risk_label_map = {'hoch': 'HOHES RISIKO', 'mittel': 'MITTLERES RISIKO', 'niedrig': 'GERINGES RISIKO'}
    for device in devices:
        risk_level_de = risk_level_map.get(device['risk_level'], device['risk_level'])
        risk_color = get_severity_color(risk_level_de)
        risk_badge = render_badge(risk_label_map.get(risk_level_de, risk_level_de.upper()), risk_level_de)
        device_type_de = device_type_map.get(device['type'], device['type'])
        # Mapping für recommended_window ins Deutsche
        recommended_window_map = {
            'Within 3 days': 'Innerhalb von 3 Tagen',
            'Within 2 weeks': 'Innerhalb von 2 Wochen',
            'Within 4 weeks': 'Innerhalb von 4 Wochen',
            'Within 1 week': 'Innerhalb von 1 Woche',
            'Overdue': 'Überfällig',
            'Soon': 'Bald',
        }
        recommended_window_de = recommended_window_map.get(device.get('recommended_window', ''), device.get('recommended_window', ''))
        # Mapping für Abteilungsnamen ins Deutsche
        department_map = {
            'Radiology': 'Radiologie',
            'ER': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Cardiology': 'Kardiologie',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Other': 'Andere',
        }
        department_de = department_map.get(device.get('department', ''), device.get('department', ''))
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {risk_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{device['name']}</div>
                    <div style="font-size: 0.75rem; color: #6b7280;">{device['device_id']} • {department_de}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Gerätetyp</div>
                    <div style="font-weight: 600; color: #1f2937;">{device_type_de}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Tage bis fällig</div>
                    <div style="font-weight: 600; color: {risk_color};">{device['days_until_due']} Tage</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Betriebsstunden</div>
                    <div style="font-weight: 600; color: #1f2937;">{device['usage_hours']:,}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Empfohlenes Wartungsfenster</div>
                    <div style="font-weight: 600; color: #667eea; font-size: 0.875rem;">{recommended_window_de}</div>
                </div>
                <div>
                    {risk_badge}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Geräterisikoverteilung
    st.markdown("---")
    st.markdown("#### Verteilung der Geräterisiken")
    st.markdown("")  # Abstand
    
    # German labels and color mapping
    risk_map = {'hoch': 'hoch', 'mittel': 'mittel', 'niedrig': 'niedrig', 'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
    label_map = {'hoch': 'Hoch', 'mittel': 'Mittel', 'niedrig': 'Niedrig'}
    color_map = {'hoch': '#DC2626', 'mittel': '#F59E0B', 'niedrig': '#10B981'}
    device_risk_counts = {'hoch': 0, 'mittel': 0, 'niedrig': 0}
    for device in devices:
        risk_level = risk_map.get(device['risk_level'], device['risk_level'])
        device_risk_counts[risk_level] = device_risk_counts.get(risk_level, 0) + 1

    x_labels = [label_map[k] for k in device_risk_counts.keys()]
    colors = [label_map[k] for k in device_risk_counts.keys()]
    color_discrete_map = {label_map[k]: color_map[k] for k in device_risk_counts.keys()}

    fig_device_risk = px.bar(
        x=x_labels,
        y=list(device_risk_counts.values()),
        title="",
        labels={'x': 'Risikostufe', 'y': 'Anzahl'},
        color=colors,
        color_discrete_map=color_discrete_map
    )
    fig_device_risk.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis_title="Risikostufe",
        yaxis_title="Anzahl Geräte"
    )
    st.plotly_chart(fig_device_risk, use_container_width=True)
