"""
Seitenmodul für Entlassungsplanung
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
    """Rendert die Entlassungsplanung-Seite"""
    st.markdown("### Entlassungsplanungs-Übersicht")
    st.markdown("Aggregierte Entlassungsmetriken nach Abteilung")
    
    discharge = db.get_discharge_planning()
    
    if discharge:
        df_disch = pd.DataFrame(discharge)
        # Rename columns for German legend/axis
        df_disch = df_disch.rename(columns={
            'ready_for_discharge_count': 'Entlassungsbereit',
            'pending_discharge_count': 'Ausstehend'
        })

        # Zusammenfassende Metriken
        total_ready = df_disch['Entlassungsbereit'].sum()
        total_pending = df_disch['Ausstehend'].sum()
        avg_los = df_disch['avg_length_of_stay_hours'].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Entlassungsbereit", total_ready)
        with col2:
            st.metric("Ausstehende Entlassungen", total_pending)
        with col3:
            st.metric("Ø Verweildauer", f"{avg_los:.1f} Stunden")
        
        st.markdown("---")
        
        # Department cards
        cols = st.columns(3)
        for idx, dept_data in enumerate(discharge):
            col_idx = idx % 3
            with cols[col_idx]:
                dept_color = get_department_color(dept_data['department'])
                # Deutsche Schlüssel verwenden, falls vorhanden, sonst Englisch für Rückwärtskompatibilität
                ready = dept_data.get('Entlassungsbereit', dept_data.get('ready_for_discharge_count', 0))
                pending = dept_data.get('Ausstehend', dept_data.get('pending_discharge_count', 0))
                avg_los = dept_data.get('avg_length_of_stay_hours', 0)
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-top: 4px solid {dept_color};">
                    <h4 style="margin: 0 0 1rem 0; color: {dept_color};">{dept_data['department']}</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Entlassungsbereit:</span>
                        <strong>{ready}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Ausstehend:</span>
                        <strong>{pending}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Ø Verweildauer:</span>
                        <strong>{avg_los:.1f}h</strong>
                    </div>
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                        <div style="font-size: 0.75rem; color: #9ca3af; margin-bottom: 0.25rem;">Kapazitätsauslastung</div>
                        <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="background: {dept_color}; height: 100%; width: {dept_data['discharge_capacity_utilization']*100}%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Charts
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                df_disch,
                x='department',
                y=['Entlassungsbereit', 'Ausstehend'],
                title="Entlassungsstatus nach Abteilung",
                barmode='group',
                color_discrete_map={'Entlassungsbereit': '#10B981', 'Ausstehend': '#F59E0B'},
                labels={
                    'department': 'Abteilung',
                    'Entlassungsbereit': 'Entlassungsbereit',
                    'Ausstehend': 'Ausstehend'
                }
            )
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Mapping for department names (English to German)
            department_map = {
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
            # Deutsche Abteilungsspalte für Plotting hinzufügen
            df_disch['Abteilung'] = df_disch['department'].map(department_map).fillna(df_disch['department'])
            fig = px.bar(
                df_disch,
                x='Abteilung',
                y='avg_length_of_stay_hours',
                title="Ø Verweildauer nach Abteilung",
                color='Abteilung',
                color_discrete_map={department_map.get(dept, dept): get_department_color(dept) for dept in df_disch['department']},
                labels={
                    'Abteilung': 'Abteilung',
                    'avg_length_of_stay_hours': 'Ø Verweildauer (Std.)'
                }
            )
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🏥", "Keine Entlassungsplanungsdaten", "Entlassungsplanungsdaten werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)
