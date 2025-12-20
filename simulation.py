"""
Simulation engine for HospitalFlow
Provides correlated signals, events, and realistic behavior
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math


class HospitalSimulation:
    def __init__(self):
        self.state = {
            'ed_load': 65.0,  # 0-100%
            'waiting_count': 8,
            'beds_free': 45,
            'staff_load': 72.0,  # 0-100%
            'rooms_free': 12,
            'or_load': 58.0,  # 0-100%
            'transport_queue': 3,
            'inventory_risk_count': 2,
        }
        
        self.base_state = self.state.copy()
        self.trends = {
            'ed_load': 0.0,  # -1 to 1, trend direction
            'waiting_count': 0.0,
            'beds_free': 0.0,
            'staff_load': 0.0,
        }
        
        self.active_events = []  # List of active surge events
        self.recommendation_effects = {}  # Track active recommendation effects
        self.last_update = datetime.now()
    
    def update(self, minutes_passed: int = 1):
        """Update simulation state based on time passed"""
        now = datetime.now()
        
        # Remove expired events
        self.active_events = [
            e for e in self.active_events 
            if (now - e['start_time']).total_seconds() < e['duration_minutes'] * 60
        ]
        
        # Remove expired recommendation effects
        expired_effects = [
            k for k, v in self.recommendation_effects.items()
            if (now - v['start_time']).total_seconds() > v['duration_minutes'] * 60
        ]
        for k in expired_effects:
            del self.recommendation_effects[k]
        
        # Update trends based on current state
        self._update_trends()
        
        # Apply correlations
        self._apply_correlations()
        
        # Apply active events
        self._apply_events()
        
        # Apply recommendation effects
        self._apply_recommendation_effects()
        
        # Add natural variation
        self._add_natural_variation()
        
        # Ensure bounds
        self._enforce_bounds()
        
        self.last_update = now
    
    def _update_trends(self):
        """Update trend directions based on current state"""
        # ED load trend: tends to drift toward 70% if no intervention
        if self.state['ed_load'] < 70:
            self.trends['ed_load'] = min(0.3, self.trends['ed_load'] + 0.05)
        else:
            self.trends['ed_load'] = max(-0.3, self.trends['ed_load'] - 0.05)
        
        # Add some randomness to trends
        self.trends['ed_load'] += random.uniform(-0.1, 0.1)
        self.trends['ed_load'] = max(-1.0, min(1.0, self.trends['ed_load']))
    
    def _apply_correlations(self):
        """Apply correlated signals"""
        # When ED load rises, waiting_count tends to rise
        if self.state['ed_load'] > 75:
            self.state['waiting_count'] += random.uniform(0.5, 1.5) * (self.state['ed_load'] - 75) / 25
        elif self.state['ed_load'] < 60:
            self.state['waiting_count'] -= random.uniform(0.2, 0.8)
        
        # Staff load rises with ED load (with some delay/smoothing)
        target_staff_load = 50 + (self.state['ed_load'] * 0.5)
        self.state['staff_load'] = self.state['staff_load'] * 0.8 + target_staff_load * 0.2
        
        # Transport queue rises with delay when ED load is high
        if self.state['ed_load'] > 70:
            self.state['transport_queue'] += random.uniform(0.1, 0.3)
        elif self.state['ed_load'] < 65:
            self.state['transport_queue'] = max(0, self.state['transport_queue'] - random.uniform(0.1, 0.2))
        
        # Beds free tends to drop when ED load is high
        if self.state['ed_load'] > 75:
            self.state['beds_free'] = max(0, self.state['beds_free'] - random.uniform(0.2, 0.5))
        elif self.state['ed_load'] < 60:
            self.state['beds_free'] += random.uniform(0.1, 0.3)
        
        # Rooms free correlates with beds free
        if self.state['beds_free'] < 10:
            self.state['rooms_free'] = max(0, self.state['rooms_free'] - random.uniform(0.1, 0.3))
    
    def _apply_events(self):
        """Apply active surge events"""
        for event in self.active_events:
            intensity = event['intensity']
            elapsed = (datetime.now() - event['start_time']).total_seconds() / 60
            
            # Event effect decreases over time
            decay = 1.0 - (elapsed / event['duration_minutes'])
            if decay > 0:
                # Surge increases ED load, waiting count, decreases beds free
                self.state['ed_load'] = min(100, self.state['ed_load'] + intensity * decay * 15)
                self.state['waiting_count'] += intensity * decay * 3
                self.state['beds_free'] = max(0, self.state['beds_free'] - intensity * decay * 2)
                self.state['staff_load'] = min(100, self.state['staff_load'] + intensity * decay * 10)
    
    def _apply_recommendation_effects(self):
        """Apply effects from accepted recommendations"""
        for effect_name, effect in self.recommendation_effects.items():
            elapsed = (datetime.now() - effect['start_time']).total_seconds() / 60
            remaining = max(0, effect['duration_minutes'] - elapsed)
            
            if remaining > 0:
                # Decay effect over time
                strength = remaining / effect['duration_minutes']
                
                if effect_name == 'staffing_reassignment':
                    # Reduces ED load and waiting count
                    self.state['ed_load'] = max(0, self.state['ed_load'] - strength * 8)
                    self.state['waiting_count'] = max(0, self.state['waiting_count'] - strength * 2)
                    self.state['staff_load'] = max(0, self.state['staff_load'] - strength * 5)
                
                elif effect_name == 'open_overflow_beds':
                    # Increases beds free, reduces ED load
                    self.state['beds_free'] += strength * 3
                    self.state['ed_load'] = max(0, self.state['ed_load'] - strength * 5)
                
                elif effect_name == 'room_allocation':
                    # Increases rooms free
                    self.state['rooms_free'] += strength * 2
    
    def _add_natural_variation(self):
        """Add natural random variation to all metrics"""
        self.state['ed_load'] += random.uniform(-2, 2)
        self.state['waiting_count'] += random.uniform(-0.5, 0.5)
        self.state['beds_free'] += random.uniform(-0.3, 0.3)
        self.state['staff_load'] += random.uniform(-1, 1)
        self.state['rooms_free'] += random.uniform(-0.2, 0.2)
        self.state['or_load'] += random.uniform(-1.5, 1.5)
        self.state['transport_queue'] += random.uniform(-0.2, 0.2)
    
    def _enforce_bounds(self):
        """Ensure all metrics stay within valid bounds"""
        self.state['ed_load'] = max(0, min(100, self.state['ed_load']))
        self.state['waiting_count'] = max(0, int(self.state['waiting_count']))
        self.state['beds_free'] = max(0, int(self.state['beds_free']))
        self.state['staff_load'] = max(0, min(100, self.state['staff_load']))
        self.state['rooms_free'] = max(0, int(self.state['rooms_free']))
        self.state['or_load'] = max(0, min(100, self.state['or_load']))
        self.state['transport_queue'] = max(0, int(self.state['transport_queue']))
        self.state['inventory_risk_count'] = max(0, int(self.state['inventory_risk_count']))
    
    def trigger_surge_event(self, intensity: float = 1.0, duration_minutes: int = None):
        """Trigger a surge event"""
        if duration_minutes is None:
            duration_minutes = random.randint(10, 20)
        
        event = {
            'start_time': datetime.now(),
            'duration_minutes': duration_minutes,
            'intensity': intensity,
            'type': 'surge'
        }
        self.active_events.append(event)
        return event
    
    def apply_discharge_event(self, count: int = 1):
        """Simulate discharge events (increases beds free)"""
        self.state['beds_free'] += count
        # Discharges reduce ED load slightly (patients leaving)
        self.state['ed_load'] = max(0, self.state['ed_load'] - count * 2)
        self._enforce_bounds()
    
    def apply_recommendation_effect(self, rec_type: str, effect_name: str, duration_minutes: int = 30):
        """Apply effect from accepted recommendation"""
        self.recommendation_effects[effect_name] = {
            'start_time': datetime.now(),
            'duration_minutes': duration_minutes,
            'rec_type': rec_type
        }
    
    def get_current_metrics(self) -> Dict:
        """Get current simulation state"""
        self.update()
        return self.state.copy()
    
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[Dict]:
        """Get historical values for a metric (simulated)"""
        # For MVP, generate realistic historical data based on current state
        history = []
        now = datetime.now()
        current_value = self.state.get(metric_name, 0)
        
        # Generate trend-based history
        for i in range(minutes, -1, -5):
            timestamp = now - timedelta(minutes=i)
            # Add some variation and trend
            variation = random.uniform(-5, 5) if metric_name in ['ed_load', 'staff_load', 'or_load'] else random.uniform(-2, 2)
            trend_factor = (minutes - i) / minutes * 0.1  # Slight trend
            value = current_value + variation - trend_factor * 5
            
            # Enforce bounds
            if metric_name in ['ed_load', 'staff_load', 'or_load']:
                value = max(0, min(100, value))
            else:
                value = max(0, value)
            
            history.append({
                'timestamp': timestamp,
                'value': value
            })
        
        return history
    
    def should_trigger_surge(self, demo_mode: bool = False) -> bool:
        """Determine if a surge event should be triggered (random chance)"""
        # 5% chance per update cycle, 20% in demo mode
        chance = 0.20 if demo_mode else 0.05
        return random.random() < chance


# Global simulation instance
_simulation_instance: Optional[HospitalSimulation] = None


def get_simulation() -> HospitalSimulation:
    """Get or create the global simulation instance"""
    global _simulation_instance
    if _simulation_instance is None:
        _simulation_instance = HospitalSimulation()
    return _simulation_instance


def reset_simulation():
    """Reset the simulation (useful for testing)"""
    global _simulation_instance
    _simulation_instance = None

