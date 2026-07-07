#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Auto-Generador de Portada e Índice - UNGRD
-------------------------------------------------
Este script procesa el archivo 'index.qmd' para inyectar una grilla responsiva.
Dado que el archivo no cuenta con los capítulos listados, el script escanea 
los 15 capítulos, extrae metadatos (títulos, autores, imágenes) y 
autogenera la grilla de tarjetas dinámica.
"""

import os
import re
import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_index_grid():
    # Buscar los capítulos del 01 al 15
    chapters = sorted(glob.glob(os.path.join(PROJECT_ROOT, "[0-9][0-9]-c*.qmd")))
    chapters = [c for c in chapters if re.match(r'^(0[1-9]|1[0-5])-c', os.path.basename(c))]
    
    cards = []
    for chap in chapters:
        fname = os.path.basename(chap)
        with open(chap, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extraer Título (limpiando comillas)
        title_match = re.search(r'^title:\s*"(.*?)"', content, re.MULTILINE)
        title = title_match.group(1) if title_match else fname
        
        # Extraer Autores (limpiando los superíndices de Quarto)
        authors = []
        for name_match in re.finditer(r'^\s*-\s*name:\s*"(.*?)"', content, re.MULTILINE):
            name = name_match.group(1)
            name = re.sub(r'\s*\^[^^]+\^', '', name).strip()
            authors.append(name)
        authors_str = ", ".join(authors) if authors else "Autores UNGRD"
        
        # Extraer la primera imagen del capítulo para la miniatura
        img_path = "images/banner_2023.png" # Por defecto el banner
        
        # Intentamos buscar en sintaxis markdown primero
        img_match = re.search(r'!\[.*?\]\((media/.*?|images/.*?)\)', content)
        if img_match:
            img_path = img_match.group(1).split('{')[0].strip()
        else:
            # Intentamos buscar en sintaxis HTML
            html_img_match = re.search(r'src=["\'](media/.*?|images/.*?)["\']', content)
            if html_img_match:
                img_path = html_img_match.group(1)
        
        # Formatear la tarjeta en diseño responsivo
        card = f"""::: {{.g-col-12 .g-col-md-6}}
::: {{.card .h-100 .shadow-sm}}

::: {{.card-header .pt-2 .pb-2}}
[{title}]({fname}){{.fs-6 .fw-bold .text-decoration-none}}
:::

::: {{.card-body .pt-2 .pb-2}}
![]({img_path}){{height="130px" style="object-fit: cover;"}}

<p class="autores-text">**Autores:** {authors_str}</p>
:::

:::
:::"""
        cards.append(card)
        
    # Ensamblar la grilla de Pandoc
    grid = "\n\n::: {.grid .indice-grid}\n\n" + "\n\n".join(cards) + "\n\n:::\n"
    return grid

def main():
    print("=========================================================")
    print("INICIANDO GENERACIÓN DE ÍNDICE DINÁMICO")
    print("=========================================================")
    
    filepath = os.path.join(PROJECT_ROOT, "index.qmd")
    if not os.path.exists(filepath):
        print(f"[Error] No se encontró el archivo: {filepath}")
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Limpiamos si ya existía una grilla vieja para sobreescribirla limpiamente
    if "::: {.grid .indice-grid}" in content:
        content = content.split("::: {.grid .indice-grid}")[0].strip()
    elif "::::::::::::::::::::::::::::::::: {layout-ncol" in content:
        content = content.split("::::::::::::::::::::::::::::::::: {layout-ncol")[0].strip()
        
    # Generar nueva grilla a partir de los metadatos de los capítulos
    grid_content = generate_index_grid()
    
    # Ensamblar contenido final
    final_content = content + "\n" + grid_content
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print("[Portada] index.qmd procesado. Grilla autogenerada con éxito a partir de 15 capítulos.")

if __name__ == "__main__":
    main()