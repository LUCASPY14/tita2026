"""
Importa la configuración según el entorno
"""

import os

environment = os.environ.get("DJANGO_ENVIRONMENT", "development")

if environment == "production":
    pass
elif environment == "test":
    pass
else:
    pass
