#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.enhanced_prediction_service import EnhancedPredictionService
from services.race_prediction_service import race_prediction_service

# Initialize service
service = EnhancedPredictionService()

# Test if race service has correct ratings
print('=== Race Service Car Performance ===')
if hasattr(race_prediction_service, 'car_performance'):
    for team, data in race_prediction_service.car_performance.items():
        if 'McLaren' in team:
            print(f'{team}: {data}')

print('\n=== Race Service Driver Performance ===')
if hasattr(race_prediction_service, 'driver_performance'):
    for driver, data in race_prediction_service.driver_performance.items():
        if 'Piastri' in driver:
            print(f'{driver}: {data}')

# Test data-driven prediction
print('\n=== Testing Data-Driven Prediction ===')
result = service._get_data_driven_prediction('PIA', 'Italian Grand Prix', 'dry', 'McLaren')
print(f'PIA result: {result}')