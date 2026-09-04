from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class NonStrictManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    ManifestStaticFilesStorage, pero sin abortar el request cuando falta una
    entrada en el manifest.

    Jazzmin's admin/base.html referencia `{% static 'vendor/bootswatch' %}`
    como data-attribute (un directorio, no un archivo) sin importar el tema
    configurado. ManifestStaticFilesStorage en modo estricto (el default)
    levanta ValueError ante cualquier ruta sin hash — esto tira 500 en toda
    carga del admin autenticado. manifest_strict=False hace que devuelva la
    ruta tal cual en vez de fallar.
    """

    manifest_strict = False
