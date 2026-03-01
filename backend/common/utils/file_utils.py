"""
Utilidades para manejo de archivos
"""
import os
from django.core.files.storage import default_storage


def save_uploaded_file(file, path):
    """
    Guarda un archivo subido en el path especificado
    """
    file_path = os.path.join(path, file.name)
    return default_storage.save(file_path, file)


def delete_file(file_path):
    """
    Elimina un archivo del sistema
    """
    if default_storage.exists(file_path):
        default_storage.delete(file_path)
        return True
    return False


def get_file_extension(filename):
    """
    Obtiene la extensión de un archivo
    """
    return os.path.splitext(filename)[1].lower()
