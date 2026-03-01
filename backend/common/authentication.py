"""
Autenticación personalizada
"""
from rest_framework.authentication import TokenAuthentication


class CustomTokenAuthentication(TokenAuthentication):
    """
    Autenticación de token personalizada
    """
    keyword = 'Bearer'
