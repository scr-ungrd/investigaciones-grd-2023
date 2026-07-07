#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Maestro de Migración y Consolidación Arquitectónica - UNGRD
-----------------------------------------------------------------
Este script realiza la migración completa de un libro "crudo" en una sola pasada:
1. Metadatos y YAML:
   - Lee 'prelim-lista-de-autores.qmd' y 'data/orcid-2023.xlsx' como fuentes de verdad.
   - Re-mapea el frontmatter YAML estructurando 'author:' con superíndices manuales.
   - Aplica numeración inteligente (IDs únicos por institución) y deduplica afiliaciones.
   - Inyecta 'date: ""' y 'doi: ""' en cada capítulo.
   - Configura 'lang: es' y 'number-sections: false' en '_quarto.yml'.
2. Cajas y Resúmenes:
   - Envuelve '## Resumen' y '## Abstract' en Pandoc divs.
   - Transforma los bloques '::: {.caja-box}' a callouts estilizados UNGRD con títulos <h2>.
3. Numeración In-Place:
   - Extrae el número de capítulo del nombre del archivo (Formato 01-c).
   - Aplica numeración jerárquica manual '## {cap}.{h2}' y '### {cap}.{h2}.{h3}'
     in-place (ignorando Resumen y Abstract).
4. Limpieza Interna:
   - Elimina las carpetas temporales '_book/' y '.quarto/' al finalizar.
"""

import os
import re
import glob
import shutil
import unicodedata
import subprocess

try:
    import pandas as pd
except ImportError:
    print("[Error Crítico] Faltan librerías. Ejecuta: pip install pandas openpyxl")
    exit(1)

# Ruta raíz del proyecto (un nivel arriba del script en workflow/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def normalize_string(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    return s.strip().lower()

def clean_for_comparison(s):
    s = normalize_string(s)
    return "".join([c for c in s if c.isalnum()])

def get_matching_master_affiliation(chapter_aff, master_aff_full):
    if not chapter_aff or not master_aff_full:
        return None
    chapter_clean = clean_for_comparison(chapter_aff)
    master_parts = [p.strip() for p in master_aff_full.split(".") if p.strip()]
    matched_parts = []
    for part in master_parts:
        part_clean = clean_for_comparison(part)
        if len(part_clean) < 8:
            continue
        if part_clean in chapter_clean or chapter_clean in part_clean:
            matched_parts.append(part)
        else:
            min_len = min(len(chapter_clean), len(part_clean))
            compare_len = min(min_len, 20)
            if compare_len >= 10 and chapter_clean[:compare_len] == part_clean[:compare_len]:
                matched_parts.append(part)
    if matched_parts:
        return ". ".join(matched_parts)
    return None

def load_orcids():
    orcid_map = {}
    excel_path = os.path.join(PROJECT_ROOT, "data", "orcid-2023.xlsx")
    if not os.path.exists(excel_path):
        print(f"[Advertencia] No se encontró el archivo de ORCIDs en: {excel_path}")
        return orcid_map
    
    try:
        df = pd.read_excel(excel_path)
        for _, row in df.iterrows():
            name = str(row.iloc[0]).strip()
            orcid = str(row.iloc[1]).strip()
            if name != 'nan' and orcid != 'nan':
                # Limpiar el enlace si viene como URL completa
                orcid = orcid.replace("https://orcid.org/", "").strip()
                orcid_map[normalize_string(name)] = orcid
        print(f"[Metadatos] Cargados {len(orcid_map)} ORCIDs desde el archivo Excel.")
    except Exception as e:
        print(f"[Error] Al procesar el Excel de ORCIDs: {e}")
        
    return orcid_map

def load_master_authors():
    author_map = {}
    master_file = os.path.join(PROJECT_ROOT, "prelim-lista-de-autores.qmd")
    if not os.path.exists(master_file):
        print(f"[Error] No se encontró la fuente de verdad: {master_file}")
        return author_map
        
    with open(master_file, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                parts = line.split("|", 1)
                name = parts[0].replace("*", "").strip()
                aff = parts[1].replace("*", "").strip()
                author_map[normalize_string(name)] = aff
    print(f"[Metadatos] Cargados {len(author_map)} autores desde la fuente de verdad.")
    return author_map

def parse_current_authors(yaml_text):
    authors = []
    lines = yaml_text.splitlines()
    current_author = None
    
    for line in lines:
        name_match = re.match(r'^\s+-\s*name:\s*"([^"]+)"', line)
        if name_match:
            if current_author:
                authors.append(current_author)
            current_author = {"name": name_match.group(1), "orcid": "", "affiliation": ""}
            continue
            
        if current_author:
            orcid_match = re.match(r'^\s+orcid:\s*"([^"]*)"', line)
            if orcid_match:
                current_author["orcid"] = orcid_match.group(1)
                continue
            aff_match = re.match(r'^\s+affiliation:\s*"([^"]*)"', line)
            if aff_match:
                current_author["affiliation"] = aff_match.group(1)
                continue
                
        if line.strip() and not line.startswith(" ") and not line.startswith("-"):
            if current_author:
                authors.append(current_author)
                current_author = None
                
    if current_author:
        authors.append(current_author)
        
    return authors

def extract_original_affiliations(fpath, current_yaml, current_body):
    affiliations = {}
    
    # 1. Intentar extraer del cuerpo del archivo
    heading_match = re.search(r'^#+\s+', current_body, re.MULTILINE)
    if heading_match:
        pre_heading = current_body[:heading_match.start()]
        lines = [l.strip() for l in pre_heading.splitlines() if l.strip()]
        
        has_affiliations = False
        aff_lines = []
        for l in lines:
            if ":::" in l:
                continue
            if re.search(r'Autor de contacto|Correo-e', l, re.IGNORECASE):
                continue
            if re.search(r'\*\*[^*]+\*\*', l):
                continue
            if re.match(r'^\d+\s*\w+', l) or any(k in l.lower() for k in ["universidad", "departamento", "instituto", "centro", "consultoría", "escuela", "servicio", "facultad", "fundación", "asociación"]):
                aff_lines.append(l)
                has_affiliations = True
                
        if has_affiliations:
            for idx, line in enumerate(aff_lines):
                m = re.match(r'^(\d+)\s*(.*)$', line)
                if m:
                    num = m.group(1)
                    text = m.group(2).strip()
                    affiliations[num] = text
                else:
                    num = str(idx + 1)
                    affiliations[num] = line.strip()

    # 2. Fallback 1: Recuperar versión de git
    if not affiliations:
        try:
            rel_fpath = os.path.relpath(fpath, PROJECT_ROOT)
            result = subprocess.run(["git", "show", f"HEAD:{rel_fpath}"], capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT)
            if result.returncode == 0:
                orig_content = result.stdout
                yaml_match = re.match(r'^---\n(.*?)\n---\s*\n(.*)', orig_content, re.DOTALL)
                if yaml_match:
                    orig_body = yaml_match.group(2)
                    orig_heading = re.search(r'^#+\s+', orig_body, re.MULTILINE)
                    if orig_heading:
                        orig_pre = orig_body[:orig_heading.start()]
                        orig_lines = [l.strip() for l in orig_pre.splitlines() if l.strip()]
                        orig_aff_lines = []
                        for l in orig_lines:
                            if ":::" in l:
                                continue
                            if re.search(r'Autor de contacto|Correo-e', l, re.IGNORECASE):
                                continue
                            if re.search(r'\*\*[^*]+\*\*', l):
                                continue
                            if re.match(r'^\d+\s*\w+', l) or any(k in l.lower() for k in ["universidad", "departamento", "instituto", "centro", "consultoría", "escuela", "servicio", "facultad", "fundación", "asociación"]):
                                orig_aff_lines.append(l)
                        for idx, line in enumerate(orig_aff_lines):
                            m = re.match(r'^(\d+)\s*(.*)$', line)
                            if m:
                                num = m.group(1)
                                text = m.group(2).strip()
                                affiliations[num] = text
                            else:
                                num = str(idx + 1)
                                affiliations[num] = line.strip()
        except Exception:
            pass

    # 3. Fallback 2: Parsear desde el YAML actual
    if not affiliations:
        current_authors = parse_current_authors(current_yaml)
        for aut in current_authors:
            aff_val = aut.get("affiliation", "")
            if aff_val:
                matches = re.finditer(r'\^([^^]+)\^(.*?)(?=\s*\^[^^]+\^|$)', aff_val, re.DOTALL)
                for m in matches:
                    num = m.group(1)
                    text = m.group(2).strip().strip(";").strip()
                    affiliations[num] = text

    return affiliations

def configure_quarto_yml():
    qpath = os.path.join(PROJECT_ROOT, "_quarto.yml")
    if not os.path.exists(qpath):
        print(f"[QuartoConfig] Error: No se encontró {qpath}")
        return
        
    with open(qpath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "lang: es" not in content:
        content = "lang: es\n" + content
        print("  [_quarto.yml] Inyectado 'lang: es' en la raíz.")
        
    if re.search(r'number-sections:\s*true', content):
        content = re.sub(r'number-sections:\s*true', 'number-sections: false', content)
        print("  [_quarto.yml] Cambiado 'number-sections: true' a 'number-sections: false'.")
    elif "number-sections:" not in content:
        content = re.sub(r'(html:\s*\n)', r'\1    number-sections: false\n', content)
        print("  [_quarto.yml] Agregado 'number-sections: false' en la sección html.")
        
    with open(qpath, "w", encoding="utf-8") as f:
        f.write(content)

def process_chapters(author_map, orcid_map):
    chapters = sorted(glob.glob(os.path.join(PROJECT_ROOT, "[0-9][0-9]-c*.qmd")))
    chapters = [c for c in chapters if re.match(r'^(0[1-9]|1[0-5])-c', os.path.basename(c))]

    print(f"\n--- Procesando {len(chapters)} Capítulos in-place ---")

    for fpath in chapters:
        fname = os.path.basename(fpath)
        print(f"Procesando: {fname}...")
        
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        yaml_match = re.match(r'^---\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not yaml_match:
            print(f"  [Error] No se detectó bloque YAML en {fname}")
            continue

        yaml_content = yaml_match.group(1)
        body_content = yaml_match.group(2)

        affiliations = extract_original_affiliations(fpath, yaml_content, body_content)

        author_block_match = re.search(r'^author:\s*\n((?:\s+-\s*[^\n]+\n)+)', yaml_content, re.MULTILINE)
        
        if author_block_match and "name:" not in author_block_match.group(1):
            authors = re.findall(r'-\s*"([^"]+)"', author_block_match.group(1))
            current_authors = [{"name": auth, "orcid": "", "affiliation": ""} for auth in authors]
        else:
            current_authors = parse_current_authors(yaml_content)

        heading_match = re.search(r'^#+\s+', body_content, re.MULTILINE)
        if heading_match:
            pre_heading = body_content[:heading_match.start()]
            remaining_body = body_content[heading_match.start():]
            
            has_affiliations = False
            lines = [l.strip() for l in pre_heading.splitlines() if l.strip()]
            for l in lines:
                if ":::" in l:
                    continue
                if re.match(r'^\d+\s*\w+', l) or any(k in l.lower() for k in ["universidad", "departamento", "instituto", "centro", "consultoría", "escuela", "servicio", "facultad", "fundación", "asociación"]):
                    has_affiliations = True
                    break
            
            if has_affiliations:
                body_to_process = remaining_body
            else:
                body_to_process = body_content
        else:
            body_to_process = body_content

        # =========================================================
        # NUEVO BLOQUE: Re-estructurar autores (Esquema Manual con Deduplicación)
        # =========================================================
        new_author_yaml = "author:\n"
        
        # 1. Construir registro único de afiliaciones para el capítulo
        chapter_affs = []
        author_to_ids = {}
        
        for aut in current_authors:
            clean_name = re.sub(r'\s*\^[^^]+\^$', '', aut["name"]).strip()
            norm_author = normalize_string(clean_name)
            
            master_aff_text = author_map.get(norm_author, "")
            if not master_aff_text:
                master_aff_text = aut.get("affiliation", "")
                master_aff_text = re.sub(r'\^\d+(,\d+)*\^', '', master_aff_text)
                
            if ";" in master_aff_text:
                raw_affs = [a.strip() for a in master_aff_text.split(";") if a.strip()]
            else:
                raw_affs = [master_aff_text.strip()] if master_aff_text.strip() else []
                
            ids = []
            for ra in raw_affs:
                ca = re.sub(r'^\d+[\s.-]*', '', ra).strip()
                if not ca: continue
                
                found_idx = -1
                ca_norm = ca.lower()
                for i, existing in enumerate(chapter_affs):
                    ex_norm = existing.lower()
                    if ca_norm == ex_norm or (len(ca_norm)>15 and ca_norm in ex_norm) or (len(ex_norm)>15 and ex_norm in ca_norm):
                        found_idx = i
                        break
                
                if found_idx == -1:
                    chapter_affs.append(ca)
                    found_idx = len(chapter_affs) - 1
                    
                ids.append(str(found_idx + 1))
                
            author_to_ids[clean_name] = sorted(list(set(ids)), key=int)

        # 2. Generar el YAML en formato manual
        seen_affs_printed = set()
        
        for aut in current_authors:
            clean_name = re.sub(r'\s*\^[^^]+\^$', '', aut["name"]).strip()
            norm_author = normalize_string(clean_name)
            
            ids = author_to_ids.get(clean_name, [])
            
            # Superíndices en el nombre
            aff_str = f"^{','.join(ids)}^" if ids else ""
            name_str = f"{clean_name} {aff_str}".strip() if aff_str else clean_name
            
            # Textos de afiliación a imprimir (solo los nuevos)
            aff_texts_to_print = []
            for i_str in ids:
                if i_str not in seen_affs_printed:
                    idx = int(i_str) - 1
                    if idx < len(chapter_affs):
                        aff_texts_to_print.append(f"^{i_str}^{chapter_affs[idx]}")
                        seen_affs_printed.add(i_str)
                        
            affiliation_val = "; ".join(aff_texts_to_print)
            orcid_val = orcid_map.get(norm_author, aut.get('orcid', ''))
            
            new_author_yaml += f"  - name: \"{name_str}\"\n"
            if orcid_val:
                new_author_yaml += f"    orcid: \"{orcid_val}\"\n"
            if affiliation_val:
                new_author_yaml += f"    affiliation: \"{affiliation_val}\"\n"
            else:
                new_author_yaml += f"    affiliation: \"\"\n"

        # LIMPIEZA CRÍTICA: Eliminar bloque affiliations antiguo para que no colisione
        yaml_content = re.sub(r'^affiliations:\s*\n.*?(?=^[a-zA-Z_-]+:|\Z)', '', yaml_content, flags=re.MULTILINE | re.DOTALL)

        # Reemplazar el bloque de autores en el YAML original
        yaml_content_new = re.sub(
            r'^author:\s*\n(?:[ \t]+.*\n?)*',
            new_author_yaml,
            yaml_content,
            flags=re.MULTILINE
        )

        yaml_content_new = yaml_content_new.rstrip() + "\n"
        if not re.search(r'^date:', yaml_content_new, re.MULTILINE):
            yaml_content_new += "date: \"\"\n"
        if not re.search(r'^doi:', yaml_content_new, re.MULTILINE):
            yaml_content_new += "doi: \"\"\n"

        # 4. Envoltura de Resumen y Abstract 
        if "::: {#resumen}" not in body_to_process:
            body_to_process = re.sub(
                r'(##\s+Resumen\b.*?)(?=\n##\s+)',
                r'::: {#resumen}\n\1\n:::\n\n',
                body_to_process,
                flags=re.IGNORECASE | re.DOTALL
            )
        if "::: {#abstract}" not in body_to_process:
            body_to_process = re.sub(
                r'(##\s+Abstract\b.*?)(?=\n##\s+|$)',
                r'::: {#abstract}\n\1\n:::\n\n',
                body_to_process,
                flags=re.IGNORECASE | re.DOTALL
            )

        # 5. Transformación de Cajas de Información (.caja-box -> callouts)
        box_counter = 0
        cuadro_counter = 0
        def replace_box(match):
            nonlocal box_counter, cuadro_counter
            inner_content = match.group(1).strip()
            
            if re.match(r'^\s*\*?\*?[Cc]uadro', inner_content):
                cuadro_counter += 1
                cuadro_match = re.match(r'^\s*\*\*?[Cc]uadro\s+(\d+)\.?\s*\*?\*?(.*)', inner_content, re.DOTALL)
                if cuadro_match:
                    cuadro_num = cuadro_match.group(1)
                    rest = cuadro_match.group(2).strip()
                else:
                    cuadro_num = str(cuadro_counter)
                    rest = inner_content
                new_cuadro = f'::: {{#cuadro-box-{cuadro_counter} .callout-important style="background-color: #f5f5f5ff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
                new_cuadro += f'**Cuadro {cuadro_num}.** {rest}\n'
                new_cuadro += ':::'
                return new_cuadro
            
            box_counter += 1
            caja_match = re.match(r'^\s*\*\*[Cc]aja\s+(\d+)\.?\s*\*\*(.*)', inner_content, re.DOTALL)
            if caja_match:
                caja_num = caja_match.group(1)
                rest = caja_match.group(2).strip()
            else:
                caja_num = str(box_counter)
                rest = inner_content
                
            new_box = f'::: {{#box{box_counter} .callout-important style="background-color: #e3f0fbff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_box += f'**Caja {caja_num}.** {rest}\n'
            new_box += ':::'
            return new_box

        def replace_cuadro_only(match):
            nonlocal cuadro_counter
            inner_content = match.group(1).strip()
            cuadro_counter += 1
            cuadro_match = re.match(r'^\s*\*\*?[Cc]uadro\s+(\d+)\.?\s*\*?\*?(.*)', inner_content, re.DOTALL)
            if cuadro_match:
                cuadro_num = cuadro_match.group(1)
                rest = cuadro_match.group(2).strip()
            else:
                cuadro_num = str(cuadro_counter)
                rest = inner_content
            new_cuadro = f'::: {{#cuadro-box-{cuadro_counter} .callout-important style="background-color: #f5f5f5ff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_cuadro += f'**Cuadro {cuadro_num}.** {rest}\n'
            new_cuadro += ':::'
            return new_cuadro

        box_pattern = re.compile(r':::\s*\{\s*\.caja-box\s*\}\s*\n(.*?)\n:::', re.DOTALL)
        body_to_process = box_pattern.sub(replace_box, body_to_process)

        cuadro_pattern = re.compile(r':::\s*\{\s*\.cuadro-box\s*\}\s*\n(.*?)\n:::', re.DOTALL)
        body_to_process = cuadro_pattern.sub(replace_cuadro_only, body_to_process)

        def replace_cuadro_tabla(match):
            nonlocal cuadro_counter
            cuadro_counter += 1
            content = match.group(1).strip()
            m_num = re.match(r'^[Cc]uadro\s+(\d+)\.?\s*(.*)', content, re.DOTALL)
            if m_num:
                num = m_num.group(1)
                rest = m_num.group(2).strip()
            else:
                num = str(cuadro_counter)
                rest = content
                
            new_callout = f'::: {{#cuadro-box-{cuadro_counter} .callout-important style="background-color: #f5f5f5ff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_callout += f'**Cuadro {num}.** {rest}\n'
            new_callout += ':::'
            return new_callout

        cuadro_tabla_pattern = re.compile(r'^\|\s*(Cuadro\s+\d+\..*?)\s*\|\s*\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE | re.DOTALL)
        body_to_process = cuadro_tabla_pattern.sub(replace_cuadro_tabla, body_to_process)

        puntos_counter = 0
        def replace_puntos(match):
            nonlocal puntos_counter
            puntos_counter += 1
            text_content = match.group(1).strip()
            new_puntos = f'::: {{#puntos-clave-{puntos_counter} .callout-important style="background-color: #f4ebffff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_puntos += f'**Puntos clave.** {text_content}\n'
            new_puntos += ':::'
            return new_puntos

        puntos_pattern = re.compile(r'^\|\s*PUNTOS\s+CLAVE\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = puntos_pattern.sub(replace_puntos, body_to_process)

        reco_counter = 0
        def replace_reco(match):
            nonlocal reco_counter
            reco_counter += 1
            text_content = match.group(1).strip()
            new_reco = f'::: {{#recomendaciones-{reco_counter} .callout-important style="background-color: #fff0f3ff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_reco += f'**Recomendaciones para tomar decisiones.** {text_content}\n'
            new_reco += ':::'
            return new_reco

        reco_pattern = re.compile(r'^\|\s*RECOMENDACI[OÓ]NES\s+PARA\s+TOMAR\s+DECISIONES\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = reco_pattern.sub(replace_reco, body_to_process)

        retos_counter = 0
        def replace_retos(match):
            nonlocal retos_counter
            retos_counter += 1
            text_content = match.group(1).strip()
            new_retos = f'::: {{#retos-{retos_counter} .callout-important style="background-color: #eafaf1ff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_retos += f'**Retos.** {text_content}\n'
            new_retos += ':::'
            return new_retos

        retos_pattern = re.compile(r'^\|\s*RETOS\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = retos_pattern.sub(replace_retos, body_to_process)

        trabajo_counter = 0
        def replace_trabajo(match):
            nonlocal trabajo_counter
            trabajo_counter += 1
            text_content = match.group(1).strip()
            new_trabajo = f'::: {{#trabajo-futuro-{trabajo_counter} .callout-important style="background-color: #fffbebff; padding:20px; border: none !important;" appearance="minimal" icon="false"}}\n'
            new_trabajo += f'**Trabajo a futuro.** {text_content}\n'
            new_trabajo += ':::'
            return new_trabajo

        trabajo_pattern = re.compile(r'^\|\s*TRABAJO\s+(?:A\s+)?FUTURO\s+(.*?)\s*\|\s*\r?\n^\|\s*---\s*\|\s*$', re.IGNORECASE | re.MULTILINE)
        body_to_process = trabajo_pattern.sub(replace_trabajo, body_to_process)

        # 6. Numeración Manual In-Place 
        match_chap = re.search(r'^(\d{2})-c', fname)
        chap_num = int(match_chap.group(1)) if match_chap else 1

        lines = body_to_process.splitlines()
        new_lines = []
        h2_counter = 0
        h3_counter = 0
        
        for line in lines:
            stripped_line = line.strip()
            clean_bold = stripped_line.strip('*').strip()
            cleaned_upper = clean_bold.upper()
            
            is_special_term = cleaned_upper in [
                "CONFLICTO DE INTERESES", "AGRADECIMIENTOS", 
                "IDENTIFICACIÓN DE AUTORES", "IDENTIFICACION DE AUTORES", 
                "IDENTIFICACIÓN DE AUTOR", "IDENTIFICACION DE AUTOR", 
                "IDENTIFICACIÓN DEL AUTOR", "IDENTIFICACION DEL AUTOR",
                "BIBLIOGRAFÍA", "BIBLIOGRAFIA"
            ]
            
            if stripped_line.startswith("**") and stripped_line.endswith("**") and is_special_term:
                line = f"## {cleaned_upper}"
            
            if line.startswith("#"):
                line_lower = line.lower()
                
                if "resumen" in line_lower or "abstract" in line_lower:
                    new_lines.append(line)
                    continue
                
                if line.startswith("## "):
                    h2_counter += 1
                    h3_counter = 0
                    
                    line_clean = re.sub(r'\s*\{\s*\.unnumbered\s*\}', '', line)
                    cleaned_title = re.sub(r'^##\s*(?:\d+(?:\.\d+)*\.?\s*)?', '', line_clean).strip()
                    
                    new_line = f"## {chap_num}.{h2_counter} {cleaned_title}"
                    new_lines.append(new_line)
                
                elif line.startswith("### "):
                    h3_counter += 1
                    line_clean = re.sub(r'\s*\{\s*\.unnumbered\s*\}', '', line)
                    cleaned_title = re.sub(r'^###\s*(?:\d+(?:\.\d+)*\.?\s*)?', '', line_clean).strip()
                    new_line = f"### {chap_num}.{h2_counter}.{h3_counter} {cleaned_title}"
                    new_lines.append(new_line)
                
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        body_to_process = "\n".join(new_lines)

        final_content = f"---\n{yaml_content_new.rstrip()}\n---\n\n{body_to_process}"
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(final_content)
        print(f"  [Completado] {fname} migrado con éxito.")

def purge_cache():
    folders_to_delete = [os.path.join(PROJECT_ROOT, "_book"), os.path.join(PROJECT_ROOT, ".quarto")]
    print("\n--- 3. Limpieza de Caché Interna ---")
    for folder in folders_to_delete:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"  [Completado] Carpeta eliminada con éxito: {folder}/")
            except Exception as e:
                print(f"  [Error] No se pudo eliminar la carpeta {folder}: {e}")
        else:
            print(f"  [Info] La carpeta {folder}/ no existe o ya fue eliminada.")

def main():
    print("=========================================================")
    print("INICIANDO HERRAMIENTA MAESTRA DE MIGRACIÓN - UNGRD")
    print("=========================================================")
    
    print("\n--- 1. Configurando _quarto.yml ---")
    configure_quarto_yml()
    
    orcid_map = load_orcids()
    author_map = load_master_authors()
    
    if author_map:
        process_chapters(author_map, orcid_map)
        
    purge_cache()
    
    print("\n=========================================================")
    print("¡MIGRACIÓN Y CONSOLIDACIÓN COMPLETADAS CON ÉXITO!")
    print("=========================================================")

if __name__ == "__main__":
    main()