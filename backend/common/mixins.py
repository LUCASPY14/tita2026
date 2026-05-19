"""
Mixins reutilizables para vistas de la API
"""

import csv
from django.http import HttpResponse


class ExportCSVMixin:
    """
    Agrega exportación CSV al endpoint list cuando ?formato=csv.

    Uso en el ViewSet:
        export_fields = [("columna_header", "attr_o_callable"), ...]
        export_filename = "archivo"

    El atributo puede ser:
        - un string "campo" -> str(obj.campo)
        - un string con doble guion bajo "campo__sub" -> obj.campo.sub (dot-walk)
        - un callable lambda obj: ...
    """

    export_fields: list = []
    export_filename: str = "export"

    def _get_value(self, obj, attr):
        if callable(attr):
            return attr(obj)
        parts = attr.split("__")
        val = obj
        for part in parts:
            if val is None:
                return ""
            val = getattr(val, part, "")
        return val if val is not None else ""

    def list(self, request, *args, **kwargs):
        if request.query_params.get("formato") == "csv":
            return self._export_csv(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def _export_csv(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        headers = [h for h, _ in self.export_fields]
        attrs = [a for _, a in self.export_fields]

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="{self.export_filename}.csv"'

        writer = csv.writer(response)
        writer.writerow(headers)
        for obj in queryset:
            writer.writerow([self._get_value(obj, a) for a in attrs])

        return response
