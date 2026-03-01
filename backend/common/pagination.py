"""
Clases de paginación personalizadas
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginación estándar para la API
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """
    Paginación para conjuntos de datos grandes
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500
