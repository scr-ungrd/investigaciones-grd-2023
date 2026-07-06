#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Portada e Índice - UNGRD
---------------------------------
Este script procesa el archivo 'index.qmd' para aplicar un diseño
beautified de grilla responsiva con tarjetas homogéneas:
1. Grilla: ::: {.grid .indice-grid}
2. Columnas: ::: {.g-col-12 .g-col-md-6}
3. Tarjetas: ::: {.card .h-100 .shadow-sm}
4. Espaciado estricto (blank lines) para evitar problemas de parseo en Pandoc.
5. Limpieza automática de scripts obsoletos al finalizar.
"""

import os
import re

# Ruta raíz del proyecto (un nivel arriba del script en workflow/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    filepath = os.path.join(PROJECT_ROOT, "index.qmd")
    if not os.path.exists(filepath):
        print(f"[Error] No se encontró el archivo: {filepath}")
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Detectar el estado del archivo (crudo vs procesado)
    is_processed = "::: {.grid .indice-grid}" in content
    
    if is_processed:
        # Estado procesado: Usar divisor de grilla
        grid_start_marker = "::: {.grid .indice-grid}"
        parts = content.split(grid_start_marker)
        pre_content = parts[0].strip()
        rest = parts[1].strip()
        
        # Quitar cierre de la grilla
        if rest.endswith(":::"):
            rest = rest[:-3].strip()
            
        # Separar tarjetas por su clase de columna (soportando .g-col-lg-4 opcional)
        raw_cards = re.split(r':::\s*\{\s*\.g-col-12\s+\.g-col-md-6(?:\s+\.g-col-lg-4)?\s*\}', rest)
        cards_data = []
        for rc in raw_cards:
            rc = rc.strip()
            if not rc:
                continue
                
            # Extraer link (soportando cualquier clase en el header)
            header_match = re.search(r':::\s*\{\s*\.card-header.*?\s*\}\s*\n+(.*?)\n+:::', rc, re.DOTALL)
            title_link = header_match.group(1).strip() if header_match else ""
            
            # Extraer body (soportando cualquier clase en el body)
            body_match = re.search(r':::\s*\{\s*\.card-body.*?\s*\}\s*\n+(.*?)\n+:::', rc, re.DOTALL)
            body_text = body_match.group(1).strip() if body_match else ""
            
            # Imagen y autores
            img_match = re.search(r'!\[\]\((.*?)\)', body_text)
            img_tag = ""
            if img_match:
                img_path = img_match.group(1).strip()
                # Limpiar cualquier parámetro inline previo
                img_path = img_path.split('}')[0].split('{')[0].strip()
                img_tag = f"![]({img_path}){{height=\"130px\" style=\"object-fit: cover;\"}}"
            
            authors_match = re.search(r'\*\*Autores:\*\*(.*?)</p>', body_text, re.IGNORECASE)
            if not authors_match:
                authors_match = re.search(r'class="autores-text".*?\*\*Autores:\*\*(.*?)</p>', body_text, re.IGNORECASE | re.DOTALL)
            authors_text = authors_match.group(1).strip() if authors_match else ""
            
            cards_data.append((title_link, img_tag, authors_text))
    else:
        # Estado crudo (raw)
        grid_start_marker = '::::::::::::::::::::::::::::::::: {layout-ncol="2"}'
        grid_end_marker = ':::::::::::::::::::::::::::::::::'
        parts = content.split(grid_start_marker)
        if len(parts) < 2:
            print("[Error] No se encontró el marcador de inicio de grilla en index.qmd")
            return
            
        pre_content = parts[0].strip()
        rest = parts[1]
        
        post_parts = rest.split(grid_end_marker)
        if len(post_parts) < 2:
            print("[Error] No se encontró el marcador de fin de grilla en index.qmd")
            return
            
        cards_section = post_parts[0].strip()
        post_content = post_parts[1].strip()
        
        raw_cards = cards_section.split('::::: card')
        cards_data = []
        for rc in raw_cards:
            rc = rc.strip()
            if not rc:
                continue
            if rc.endswith(':::::'):
                rc = rc[:-5].strip()
                
            header_match = re.search(r':::\s*\{\s*\.card-header.*?\s*\}\s*\n+(.*?)\n+:::', rc, re.DOTALL)
            if not header_match:
                header_match = re.search(r':::\s*card-header\s*\n+(.*?)\n+:::', rc, re.DOTALL)
            title_link = header_match.group(1).strip() if header_match else ""
            
            body_match = re.search(r':::\s*card-body\s*\n+(.*?)\n+:::', rc, re.DOTALL)
            if not body_match:
                body_match = re.search(r':::\s*\{\s*\.card-body.*?\s*\}\s*\n+(.*?)\n+:::', rc, re.DOTALL)
            body_text = body_match.group(1).strip() if body_match else ""
            
            img_match = re.search(r'!\[\]\((.*?)\)', body_text)
            img_tag = ""
            if img_match:
                img_path = img_match.group(1).strip()
                img_path = img_path.split('}')[0].split('{')[0].strip()
                img_tag = f"![]({img_path}){{height=\"130px\" style=\"object-fit: cover;\"}}"
                
            authors_match = re.search(r'\*\*Autores:?\*\*\s*:?\s*(.*)', body_text, re.IGNORECASE)
            authors_text = authors_match.group(1).strip() if authors_match else ""
            
            cards_data.append((title_link, img_tag, authors_text))

    def format_title_link(title):
        title = title.strip()
        if title.startswith("**") and title.endswith("**"):
            title = title[2:-2].strip()
        match = re.match(r'^\[(.*?)\]\((.*?)\)(?:\{.*?\})?$', title)
        if match:
            text = match.group(1).strip()
            url = match.group(2).strip()
            return f"[{text}]({url}){{.fs-6 .fw-bold .text-decoration-none}}"
        return title
            
    # Construir las tarjetas con el formato estricto de Pandoc
    new_cards = []
    for title_link, img_tag, authors_text in cards_data:
        formatted_title = format_title_link(title_link)
        new_card = "::: {.g-col-12 .g-col-md-6}\n"
        new_card += "::: {.card .h-100 .shadow-sm}\n\n"
        
        new_card += "::: {.card-header .pt-2 .pb-2}\n\n"
        new_card += f"{formatted_title}\n\n"
        new_card += ":::\n\n"
        
        new_card += "::: {.card-body .pt-2 .pb-2}\n"
        if img_tag:
            new_card += "\n"
            new_card += f"{img_tag}\n\n"
        else:
            new_card += "\n"
            
        new_card += f'<p class="autores-text">**Autores:** {authors_text}</p>\n\n'
        new_card += ":::\n\n"
        
        new_card += ":::\n"
        new_card += ":::\n"
        
        new_cards.append(new_card)
        
    # Re-ensamblar index.qmd
    final_grid = "::: {.grid .indice-grid}\n"
    final_grid += "\n".join(new_cards)
    final_grid += ":::\n"
    
    final_content = pre_content + "\n\n" + final_grid
    if not is_processed and 'post_content' in locals() and post_content:
        final_content += "\n\n" + post_content
        
    final_content = final_content.strip() + "\n"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_content)
    print("[Portada] index.qmd procesado y formateado con éxito.")
    
    # Eliminar scripts obsoletos
    obsolete_files = [os.path.join(PROJECT_ROOT, f) for f in ["embellecer_indice.py", "reparar_indice.py"]]
    print("\n--- Limpieza de archivos temporales ---")
    for file in obsolete_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  [Eliminado] Archivo obsoleto: {file}")
            except Exception as e:
                print(f"  [Error] No se pudo eliminar {file}: {e}")
        else:
            print(f"  [Info] El archivo {file} no existía o ya fue eliminado.")

if __name__ == "__main__":
    main()
