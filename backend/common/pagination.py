from rest_framework.pagination import PageNumberPagination, CursorPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class CursorResultsSetPagination(CursorPagination):
    """Cursor pagination para logs de alto volumen (movimientos, historial).
    Opaco e inmutable: no expone número total ni permite saltar páginas.
    Usa ordering='-fecha' — el ViewSet debe garantizar ese campo."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    ordering = '-fecha'
