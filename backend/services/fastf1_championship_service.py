#!/usr/bin/env python3
"""
FastF1 Championship Service - DEPRECATED
All championship data is now served by cache_manager.py via Jolpica-F1 API.
This file is kept as a stub for backward compatibility.
"""

import logging

logger = logging.getLogger(__name__)


class FastF1ChampionshipService:
    def __init__(self):
        logger.info("FastF1ChampionshipService is deprecated - use cache_manager instead")


# Keep global instance for any lingering imports
fastf1_championship_service = FastF1ChampionshipService()
