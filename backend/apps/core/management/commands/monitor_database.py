"""
====================================
Database Management Command - Cantina Tita
Django management command for database monitoring and optimization
====================================
"""

import os
import sys

# Add the parent directory to the path so we can import from monitoring
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.database_monitor import Command
