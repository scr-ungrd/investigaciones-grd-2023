# Prompt de Evaluación - 03_indice.py

## Contexto
El agente debe ejecutar el script para el procesamiento del índice y la portada del libro:
```bash
python workflow/03_indice.py
```

## Criterios de Evaluación (QA)
Tras la ejecución del script, el agente debe validar los siguientes puntos:
1. **Grilla Responsiva**:
   - Comprobar que en `index.qmd` se inyecta correctamente el contenedor general de la grilla: `::: {.grid .indice-grid}`.
   - Cada tarjeta de capítulo debe estar envuelta en las clases responsivas: `::: {.g-col-12 .g-col-md-6}`.
2. **Estructura y Estilos de las Tarjetas**:
   - Cada tarjeta debe tener el formato `::: {.card .h-100 .shadow-sm}`.
   - El encabezado de la tarjeta (`.card-header .pt-2 .pb-2`) debe contener el título del capítulo como enlace con formato compacto: `[Título del Capítulo](ruta_capitulo.html){.fs-6 .fw-bold .text-decoration-none}`.
   - La imagen del capítulo en el cuerpo de la tarjeta (`.card-body .pt-2 .pb-2`) debe tener atributos de altura y estilo inline para asegurar uniformidad: `![](ruta_imagen){height="130px" style="object-fit: cover;"}`.
   - Los autores del capítulo en el cuerpo de la tarjeta deben estar envueltos en un párrafo con clase específica: `<p class="autores-text">**Autores:** Nombres...</p>`.
3. **Sintaxis de Bloques Pandoc**:
   - Se debe verificar que existen saltos de línea (líneas vacías) adecuados alrededor de cada apertura/cierre de bloques `:::` para evitar problemas en el procesamiento de Pandoc.
4. **Limpieza de Scripts Obsoletos**:
   - Verificar que los scripts antiguos de indexación `embellecer_indice.py` y `reparar_indice.py` ya no existen en la raíz del proyecto (deben haber sido eliminados por el script).

## Protocolo de Reporte de Incidencias (Sin Modificación Automática)
Si la evaluación de los criterios de QA falla, o si se genera alguna excepción de Python durante la ejecución del script, el agente tiene estrictamente PROHIBIDO modificar el script original. En su lugar, debe seguir este procedimiento:

1. **Detener el avance:** No ejecutes los siguientes scripts del flujo.
2. **Generar un Informe:** Crea un archivo Markdown en la raíz del proyecto llamado `reporte_incidencia_[nombre_del_script].md`.
3. **Estructura del Informe:** El archivo creado debe contener obligatoriamente:
   - **Estado:** Detalle del criterio exacto de QA que falló o el Traceback del error de Python.
   - **Causa Raíz:** Diagnóstico técnico de por qué el script falló o no cumplió el requerimiento sobre los archivos `.qmd` o `_quarto.yml`.
   - **Plan de Solución:** Propuesta detallada paso a paso para solucionar el problema, incluyendo los bloques de código exactos en Python que sugieres inyectar o corregir.
4. **Pausa de Seguridad:** Informa al usuario sobre la ubicación del reporte y espera la orden explícita antes de aplicar cualquier cambio en el script o realizar un `git restore`.
