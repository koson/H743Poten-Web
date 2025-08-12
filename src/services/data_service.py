"""
Data service for managing measurement data
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.current_data = {'points': []}
        self.max_points = 1000  # Maximum number of points to store

    def update_measurement_data(self, new_data):
        """Update the current measurement data"""
        try:
            points = new_data.get('points', [])
            if not points:
                return

            # Add timestamp if not present
            current_time = datetime.now().timestamp()
            for point in points:
                if 'timestamp' not in point:
                    point['timestamp'] = current_time

            # Update current data, maintaining max_points limit
            self.current_data['points'].extend(points)
            if len(self.current_data['points']) > self.max_points:
                self.current_data['points'] = self.current_data['points'][-self.max_points:]

        except Exception as e:
            logger.error(f"Error updating measurement data: {e}")

    def get_current_data(self):
        """Get the current measurement data"""
        return self.current_data

    def clear_data(self):
        """Clear all stored data"""
        self.current_data = {'points': []}
