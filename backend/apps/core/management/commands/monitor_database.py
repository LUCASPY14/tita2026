"""
====================================
Database Management Command - Cantina Tita
Django management command for database monitoring and optimization
====================================
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Monitor database health and performance"

    def handle(self, *args, **options):
        """Check database connectivity and basic health metrics."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS("Database connection: OK"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Database error: {e}"))
