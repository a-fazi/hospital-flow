"""
Seitenmodul für Inventar
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
    """Rendert die Inventar-Seite"""
    st.markdown("### Bestandsübersicht")
    
    inventory = db.get_inventory_status()
    
    if inventory:
        # Warnung bei niedrigem Bestand
        low_stock = [i for i in inventory if i['current_stock'] < i['min_threshold']]
        if low_stock:
            st.warning(f"⚠️ {len(low_stock)} Artikel unter Mindestbestand")
        
        # Inventar-Karten
        cols = st.columns(3)
        for idx, item in enumerate(inventory):
            col_idx = idx % 3
            with cols[col_idx]:
                status = calculate_inventory_status(item['current_stock'], item['min_threshold'], item['max_capacity'])
                status_color = get_severity_color(status['status']) if status['status'] != 'normal' else "#10B981"
                
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {status_color};">
                    <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em;">
                        {item['category']}
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #1f2937; margin: 0.5rem 0;">
                        {item['item_name']}
                    </div>
                    <div style="font-size: 2rem; font-weight: 700; color: {status_color}; margin: 0.5rem 0;">
                        {item['current_stock']} <span style="font-size: 0.875rem; color: #6b7280;">{item['unit']}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.5rem;">
                        Mindestbestand: {item['min_threshold']} • Kapazität: {item['max_capacity']}
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <div style="background: #e5e7eb; height: 4px; border-radius: 2px; overflow: hidden;">
                            <div style="background: {status_color}; height: 100%; width: {status['percentage']}%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Chart
        st.markdown("---")
        st.markdown("### Bestandsverlauf")
        df_inv = pd.DataFrame(inventory)
        df_inv['utilization'] = (df_inv['current_stock'] / df_inv['max_capacity']) * 100
        
        fig = px.bar(
            df_inv,
            x='item_name',
            y='utilization',
            color='department',
            title="Bestandsauslastung nach Artikel",
            labels={'utilization': 'Auslastung %', 'item_name': 'Artikel'}
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Bestandsdaten verfügbar")
