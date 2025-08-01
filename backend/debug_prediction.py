#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.enhanced_prediction_service import EnhancedPredictionService

# Initialize service
service = EnhancedPredictionService()

# Test exactly what the API would call
print("=== API Call Simulation ===")
result = service.predict_driver_performance(
    driver="PIA",
    track="Hungarian Grand Prix", 
    weather="clear",
    team="McLaren"
)

print(f"Final API result: {result}")