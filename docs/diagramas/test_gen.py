#!/usr/bin/env python3
"""
generar_docx.py - Convierte documentacion-uml.html a documentacion-uml.docx
Renderiza cada diagrama Mermaid a PNG con mmdc y lo embebe en el DOCX.
"""

import os
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY  = RGBColor(0x1E, 0x3A, 0x5F)
GREEN = RGBColor(0x27, 0xAE, 0x60)
GRAY  = RGBColor(0x88, 0x88, 0x88)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

DOCS_DIR = Path(r"d:	ita2026\docs\diagramas")
print(DOCS_DIR)
