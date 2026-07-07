#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import re
import sys

"""
Módulo de vinculación automática de bibliografía para documentos Quarto.

Este script automatiza la conversión de citas académicas en texto plano a hipervínculos
internos HTML en documentos Quarto (.qmd). Soporta la detección y procesamiento de citas individuales, 
listas de citas separadas por comas, y rangos o listas con guiones y rayas (ej. [1-3], [1, 2, 5], o [1–3]).
Adicionalmente, formatea y numera de manera homogénea la sección de referencias o bibliografía al final 
de cada capítulo, vinculando las citas del cuerpo con sus respectivas entradas bibliográficas mediante
identificadores únicos.
"""

# Ruta raíz del proyecto (un nivel arriba del script en workflow/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_and_wrap(citation_str):
    """
    Parsea una cadena de texto de cita y envuelve cada número de referencia en un hipervínculo.
    """
    parts = citation_str.split(',')
    wrapped_parts = []
    for part in parts:
        part_strip = part.strip()
        if not part_strip:
            continue
        
        # Check for en-dash or hyphen representing ranges
        if '–' in part_strip:
            range_parts = part_strip.split('–')
            wrapped_parts.append('–'.join(f"[[{rp.strip()}]](#ref-{rp.strip()})" for rp in range_parts if rp.strip()))
        elif '-' in part_strip:
            range_parts = part_strip.split('-')
            wrapped_parts.append('-'.join(f"[[{rp.strip()}]](#ref-{rp.strip()})" for rp in range_parts if rp.strip()))
        else:
            wrapped_parts.append(f"[[{part_strip}]](#ref-{part_strip})")
            
    return ', '.join(wrapped_parts)

def replace_citations(text):
    """
    Busca todas las ocurrencias de citas entre corchetes en un texto y las reemplaza
    por enlaces utilizando parse_and_wrap.
    """
    def repl(match):
        content = match.group(1)
        if not any(c.isdigit() for c in content):
            return match.group(0)
        return parse_and_wrap(content)
        
    return re.sub(r'\[([\d,\s–\-]+)\]', repl, text)

def process_file(fpath, dry_run=False):
    """
    Procesa un archivo Quarto (.qmd) individual para vincular su bibliografía.
    """
    fname = os.path.basename(fpath)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Idempotency check
    if "#ref-1" in content or "ref-1" in content:
        m = re.match(r'^(\d+)', fname)
        chap_num = int(m.group(1)) if m else fname
        print(f"Capítulo {chap_num}: Ya procesado previamente.")
        return False
        
    lines = content.splitlines(keepends=True)
    
    # Locate bibliography header using search-based logic with word boundaries
    header_idx = -1
    strategy = ""
    for idx, line in enumerate(lines):
        if re.search(r'\b(BIBLIOGR[AÁ]F[IÍ]A|REFERENCIAS|LITERATURA)\b', line, re.IGNORECASE):
            if re.match(r'^(?:#{1,3}|\*\*|\d+)', line.strip()):
                header_idx = idx
                strategy = "Detectado por encabezado formal"
                break
            
    # Contingency plan
    is_contingency = False
    if header_idx == -1:
        contingency_pat = re.compile(r'^(?:\[1\]|1\.)\s+')
        for idx in range(len(lines) - 1, -1, -1):
            if contingency_pat.match(lines[idx].lstrip()):
                header_idx = idx
                strategy = "Detectado por lista [1]/1. al final"
                is_contingency = True
                break
                
    if header_idx == -1:
        m = re.match(r'^(\d+)', fname)
        chap_num = int(m.group(1)) if m else fname
        print(f"Capítulo {chap_num}: No se encontró la bibliografía.")
        return False
        
    # Detect line ending style
    newline_char = "\n"
    if lines:
        if lines[0].endswith("\r\n"):
            newline_char = "\r\n"
        elif lines[0].endswith("\r"):
            newline_char = "\r"

    # Split body and bibliography
    if is_contingency:
        body_lines = lines[:header_idx] + [f"## Bibliografía{newline_char}{newline_char}"]
        bib_lines = lines[header_idx:]
    else:
        body_lines = lines[:header_idx+1]
        bib_lines = lines[header_idx+1:]
        
    # Process body citations
    body_text = "".join(body_lines)
    new_body_text = replace_citations(body_text)
    
    # Process bibliography entries
    new_bib_lines = []
    entry_index = 1
    for line in bib_lines:
        stripped = line.strip()
        if not stripped:
            new_bib_lines.append(line)
            continue
            
        if re.match(r'^(?:\*\*|\b)?\d+(?:\*\*|\b)?$', stripped):
            new_bib_lines.append(line)
            continue
            
        if stripped.startswith('#') or (stripped.startswith('**') and stripped.endswith('**') and len(stripped) < 40):
            new_bib_lines.append(line)
            continue
            
        clean_text = re.sub(r'^(?:\[\d+\]|\d+[\.\-]?)\s*', '', stripped)
        
        line_newline = "\n"
        if line.endswith("\r\n"):
            line_newline = "\r\n"
        elif line.endswith("\r"):
            line_newline = "\r"
            
        new_bib_lines.append(f'<div id="ref-{entry_index}">{entry_index}. {clean_text}</div>{line_newline}')
        entry_index += 1
        
    final_content = new_body_text + "".join(new_bib_lines)
        
    m = re.match(r'^(\d+)', fname)
    chap_num = int(m.group(1)) if m else fname
    
    if dry_run:
        print(f"Capítulo {chap_num}: {strategy} (Dry run)")
    else:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(final_content)
        print(f"Capítulo {chap_num}: {strategy}")
        
    return True

def main():
    """
    Función principal que orquesta el procesamiento de todos los capítulos del libro.
    """
    # Filtro estricto para procesar únicamente los capítulos 01 al 15
    chapters = sorted(glob.glob(os.path.join(PROJECT_ROOT, "[0-9][0-9]-c*.qmd")))
    qmd_files = [c for c in chapters if re.match(r'^(0[1-9]|1[0-5])-c', os.path.basename(c))]
    
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("Starting dry-run...")
    else:
        print("Starting in-place processing for all QMD files...")
        
    processed_count = 0
    for fpath in qmd_files:
        if process_file(fpath, dry_run=dry_run):
            processed_count += 1
            
    if not dry_run:
        print(f"Done. Processed {processed_count} files.")

if __name__ == "__main__":
    main()