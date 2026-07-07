#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Organización de Imágenes con Auditoría de Integridad - UNGRD
---------------------------------------------------------------------
Este script organiza las imágenes en 'images/capitulo_X/' y realiza
una verificación física y de texto al 100% para evitar enlaces rotos.
"""

import os
import re
import glob
import shutil
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def process_images_in_chapter(fpath):
    fname = os.path.basename(fpath)
    # Busca los dos primeros dígitos seguidos de "-c" (ej. "01-c", "15-c")
    match_chap = re.search(r'^(\d{2})-c', fname)
    if not match_chap:
        return False
    
    # Convierte a entero para quitar el cero a la izquierda y vuelve a string
    cap_num = str(int(match_chap.group(1)))
    cap_folder = f"capitulo_{cap_num}"
    media_dir = os.path.join(PROJECT_ROOT, "media")
    dest_dir = os.path.join(PROJECT_ROOT, "images", cap_folder)
    
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    images_copied = 0

    def replace_and_copy(match_obj, path_group_idx, full_replacement_formatter):
        raw_rel_path = match_obj.group(path_group_idx)
        
        # Aislar la ruta limpia (ignorando atributos extra de Quarto como {width=100})
        old_rel_path = raw_rel_path.split()[0].split('{')[0]
        
        if not old_rel_path.startswith("media/"):
            return match_obj.group(0)
            
        img_filename = os.path.basename(old_rel_path)
        new_rel_path = f"images/{cap_folder}/{img_filename}"
        
        src_abs_path = os.path.join(PROJECT_ROOT, old_rel_path)
        dest_abs_path = os.path.join(dest_dir, img_filename)
        
        os.makedirs(dest_dir, exist_ok=True)
        
        # Validar ANTES de retornar el texto de reemplazo
        if os.path.exists(src_abs_path):
            if not os.path.exists(dest_abs_path):
                shutil.copy2(src_abs_path, dest_abs_path)
            nonlocal images_copied
            images_copied += 1
            
            # Reconstruimos respetando los atributos extra que pudiera haber en el string crudo
            final_rel_path = raw_rel_path.replace(old_rel_path, new_rel_path)
            return full_replacement_formatter(match_obj, final_rel_path)
        else:
            # Si el origen físico no existe, NO modificamos el Markdown
            print(f"⚠️ Advertencia: No se encontró {src_abs_path}. Omitiendo reemplazo.")
            return match_obj.group(0)

    # 1. Reemplazo en formato Markdown
    content_new = re.sub(
        r'!\[(.*?)\]\((media/[^\)]+)\)', 
        lambda m: replace_and_copy(m, 2, lambda msg, p: f"![{msg.group(1)}]({p})"), 
        content
    )

    # 2. Reemplazo en formato HTML src=
    content_new = re.sub(
        r'(src=["\'])(media/[^"\']+)(["\'])', 
        lambda m: replace_and_copy(m, 2, lambda msg, p: f"{msg.group(1)}{p}{msg.group(3)}"), 
        content_new
    )

    if content != content_new:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content_new)
        return True
    return False

def ejecutar_auditoria_estricta():
    """ Escanea el libro final y comprueba la existencia física de cada imagen """
    print("\n--- INICIANDO FASE DE AUDITORÍA FÍSICA DE INTEGRIDAD ---")
    
    qmd_files = sorted(glob.glob(os.path.join(PROJECT_ROOT, "[0-9][0-9]-c*.qmd")))
    errores_detectados = []
    total_imagenes_auditadas = 0

    for fpath in qmd_files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Buscar si quedó algún rastro de la carpeta antigua media/
        if "media/" in content:
            # Verificar si la palabra media/ está dentro de una ruta de imagen
            fugas = re.findall(r'(!\[.*?\]\(media/.*?\)|src=["\']media/.*?["\'])', content)
            if fugas:
                errores_detectados.append(f"Fuga de ruta antigua en {fname}: Enlaces sin migrar: {fugas}")

        # Extraer todas las rutas nuevas que apuntan a images/capitulo_X/
        rutas_nuevas_md = re.findall(r'!\[.*?\]\((images/capitulo_\d+/[^\)]+)\)', content)
        rutas_nuevas_html = re.findall(r'src=["\'](images/capitulo_\d+/[^"\']+)["\']', content)
        todas_las_rutas = rutas_nuevas_md + rutas_nuevas_html

        for rel_path in todas_las_rutas:
            total_imagenes_auditadas += 1
            # Limpiar posibles parámetros de Quarto inline tipo {width=100}
            clean_path = rel_path.split('{')[0].strip()
            abs_path = os.path.join(PROJECT_ROOT, clean_path)
            
            if not os.path.exists(abs_path):
                errores_detectados.append(f"En {fname}: Enlace roto detectado. Archivo no existe en disco: {clean_path}")

    if errores_detectados:
        print("\n🛑 [CRÍTICO] LA AUDITORÍA DE IMÁGENES HA FALLADO:")
        for err in errores_detectados:
            print(f"  - {err}")
        print("\nInvocando protocolo de seguridad. El script terminará con código de error.")
        sys.exit(1) # Forzar salida errónea para alertar al agente
        
    print(f"✅ Auditoría completada con éxito. Se verificaron {total_imagenes_auditadas} enlaces e imágenes en disco. Cero errores.")

def main():
    print("=========================================================")
    print("INICIANDO MIGRACIÓN ARQUITECTÓNICA DE IMÁGENES")
    print("=========================================================")
    
    # Expresión regular corregida para los archivos de la UNGRD
    chapters = sorted(glob.glob(os.path.join(PROJECT_ROOT, "[0-9][0-9]-c*.qmd")))
    qmd_files = [c for c in chapters if re.match(r'^(0[1-9]|1[0-5])-c', os.path.basename(c))]
    
    for fpath in qmd_files:
        process_images_in_chapter(fpath)
            
    # Lanzar la verificación cruzada obligatoria
    ejecutar_auditoria_estricta()

if __name__ == "__main__":
    main()