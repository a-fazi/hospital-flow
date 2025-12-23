"""
Seitenmodul für Vorhersagen
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
    """Rendert die Vorhersagen-Seite"""
    st.markdown("### 5-15 Minuten Vorhersagen")
    
    predictions = db.get_predictions(15)
    if predictions:
        df = pd.DataFrame(predictions)
        # German translation for prediction types
        pred_type_map = {
            'patient_arrival': 'Patientenzugang',
            'bed_demand': 'Bettenbedarf',
            'resource_needed': 'Ressourcenbedarf',
            'waiting_count': 'Wartende Patienten',
            'ed_load': 'Notaufnahme-Auslastung',
            'or_load': 'OP-Auslastung',
            'staff_load': 'Personal-Auslastung',
            'transport_queue': 'Transport-Warteschlange',
            'rooms_free': 'Freie Räume',
            'beds_free': 'Freie Betten',
            # Bei Bedarf weitere hinzufügen
        }
        dept_map = {
            'ER': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Cardiology': 'Kardiologie',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Radiology': 'Radiologie',
            'Other': 'Andere'
        }
        # Vorhersagen gruppieren
        st.markdown("#### Bevorstehende Vorhersagen")
        for pred in predictions[:10]:
            confidence_color = "#10B981" if pred['confidence'] > 0.8 else "#F59E0B" if pred['confidence'] > 0.7 else "#EF4444"
            # Vorhersagetyp übersetzen
            pred_type = pred_type_map.get(pred['prediction_type'], pred['prediction_type'].replace('_', ' ').title())
            # Abteilung übersetzen
            dept = pred.get('department', 'N/A')
            dept_de = dept_map.get(dept, dept)
            # Zeitstring übersetzen
            minutes = pred['time_horizon_minutes']
            if minutes == 1:
                time_str = f'in {minutes} Minute'
            else:
                time_str = f'in {minutes} Minuten'
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{pred_type}</strong>
                        <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem;">
                            {dept_de} • {time_str}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">
                            {pred['predicted_value']:.1f}
                        </div>
                        <div style="font-size: 0.75rem; color: {confidence_color};">
                            {pred['confidence']*100:.0f}% Vertrauen
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Prediction chart
        st.markdown("---")
        st.markdown("### Prognose-Vertrauen nach Zeithorizont")
        
        if len(df) > 0:
            # German translation for prediction types
            pred_type_map = {
                'patient_arrival': 'Patientenzugang',
                'bed_demand': 'Bettenbedarf',
                'resource_needed': 'Ressourcenbedarf',
                'waiting_count': 'Wartende Patienten',
                'ed_load': 'Notaufnahme-Auslastung',
                'or_load': 'OP-Auslastung',
                'staff_load': 'Personal-Auslastung',
                'transport_queue': 'Transport-Warteschlange',
                'rooms_free': 'Freie Räume',
                'beds_free': 'Freie Betten',
                # Bei Bedarf weitere hinzufügen
            }
            df_plot = df.copy()
            df_plot['Problem'] = df_plot['prediction_type'].map(lambda x: pred_type_map.get(x, x.replace('_', ' ').title()))
            fig = px.scatter(
                df_plot,
                x='time_horizon_minutes',
                y='confidence',
                size='predicted_value',
                color='Problem',
                hover_data=['department'],
                title=""
            )
            fig.update_layout(
                height=400,
                xaxis_title="Zeithorizont (Minuten)",
                yaxis_title="Vertrauen",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🔮", "Keine Vorhersagen verfügbar", "Vorhersagen werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)
