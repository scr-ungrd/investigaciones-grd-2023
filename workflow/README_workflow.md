# Guía de Uso del Workflow y Organización de Imágenes

Esta documentación detalla el flujo de trabajo de preparación y maquetación del libro, con especial énfasis en el **enfoque híbrido asistido** para la organización de recursos gráficos y la auditoría de integridad física de imágenes.

---

## 1. Estructura y Propósito del Workflow

El directorio `workflow/` contiene un conjunto de scripts en Python diseñados para automatizar la estandarización y estructuración de los capítulos del libro (archivos `.qmd`):

1. **`01_metadatos.py` (Estandarización y Metadatos):**
   * Configura la localización global en `_quarto.yml` (`lang: es`, `number-sections: false`).
   * Re-estructura el frontmatter de los capítulos basándose en `prelim-lista-de-autores.qmd` (autores, afiliaciones con superíndices, ORCIDs).
   * Envuelve los resúmenes y abstracts en contenedores Pandoc Divs (`::: {#resumen}`).
   * Convierte bloques y tablas obsoletas (`.caja-box`, Puntos Clave, Recomendaciones, Retos) en callouts nativos y estilizados de Quarto con colores específicos.
   * Aplica numeración jerárquica manual H2 (`## {cap}.{h2}`) y H3 (`### {cap}.{h2}.{h3}`) directamente en el texto.
   * Elimina carpetas de caché de compilación (`_book/` y `.quarto/`).

2. **`02_bibliografia.py` (Vinculación de Bibliografía):**
   * Convierte referencias numéricas entre corchetes (ej. `[1]`, `[2-4]`) en hipervínculos internos (`[[1]](#ref-1)`).
   * Envuelve las entradas bibliográficas finales de cada capítulo en elementos `<div id="ref-N">` únicos.
   * Asegura la idempotencia del proceso (ignora archivos procesados previamente con anclas `#ref-`).

3. **`03_indice.py` (Maquetación del Índice):**
   * Construye una grilla responsiva de tarjetas en `index.qmd` para los capítulos.
   * Modela tarjetas estilizadas con imágenes uniformes (`height="130px" object-fit: cover`) y listados de autores formateados.
   * Purga scripts obsoletos de la raíz.

4. **`04_organizar_imagenes.py` (Organización de Imágenes):**
   * Centraliza los recursos gráficos desde el directorio temporal de desarrollo `media/` a carpetas locales por capítulos (`images/capitulo_X/`).
   * Re-mapea las rutas en los archivos `.qmd` (sintaxis Markdown `![]()` y etiquetas HTML `<img src="">`).
   * Realiza una auditoría física estricta de enlaces, asegurando que no existan enlaces rotos y que cada archivo exista físicamente en disco.

---

## 2. Preparación y Seguridad (Obligatorio)

> [!WARNING]
> Dado que la manipulación in-place mediante expresiones regulares puede comprometer contenidos complejos, nunca debes ejecutar el script sin antes seguir este protocolo de seguridad.

1. **Trabajar en una rama nueva:**
   Antes de hacer cambios, crea una rama limpia para contener la refactorización:
   ```bash
   git checkout -b refactor/organizacion-imagenes
   ```

2. **Crear Backup Preventivo de archivos `.qmd` (Paso Crítico):**
   Copia todos los archivos de capítulos del directorio raíz en una carpeta temporal independiente antes de ejecutar cualquier script:
   ```bash
   mkdir -p backup_temporal_qmd && cp [0-1][0-9]-capitulo-*.qmd backup_temporal_qmd/
   ```

---

## 3. Ejecución del Script Central de Imágenes

Una vez creada la copia de seguridad, ejecuta el script de organización desde el directorio raíz del proyecto:

```bash
python3 workflow/04_organizar_imagenes.py
```

### Evaluación del Resultado y Acción

*   **Caso Éxito:**
    Si el script finaliza de manera correcta y la auditoría concluye sin errores:
    ```text
    ✅ Auditoría completada con éxito. Se verificaron 229 enlaces e imágenes en disco. Cero errores.
    ```
    1. Revisa rápidamente que la estructura `images/capitulo_X/` se haya poblado y contenga las imágenes correspondientes.
    2. Elimina la carpeta temporal de backup:
       ```bash
       rm -rf backup_temporal_qmd
       ```

*   **Caso Falla / Advertencia:**
    Si el script lanza un error crítico `🛑 [CRÍTICO] LA AUDITORÍA DE IMÁGENES HA FALLADO`, muestra advertencias `⚠️ Advertencia: No se encontró...` o aborta la ejecución con código `1`:
    1. **Detente.** No guardes ni agregues cambios.
    2. Analiza el output de la consola para identificar qué imágenes o enlaces fallaron.
    3. Si la estructura del archivo `.qmd` resultó corrompida, restaura los archivos originales desde el backup temporal:
       ```bash
       cp backup_temporal_qmd/*.qmd ./
       ```

---

## 4. Revisión Manual y Ajustes (Fase Crítica)

El script realiza la mayor parte del trabajo pesado, pero **no puede automatizarse al 100%** debido a la presencia de estructuras de Markdown complejas y fórmulas matemáticas. Es indispensable realizar una inspección visual interactiva mediante:

```bash
git diff
```

Presta especial atención a los siguientes elementos:

### A. Manejo de Tablas con Imágenes
*   Las tablas complejas que contienen imágenes (por ejemplo, grillas de mapas o figuras comparativas) deben validarse manualmente.
*   Asegúrate de que la sintaxis de tabla de Quarto/Pandoc esté intacta (`|---|---|`).
*   Inyecta atributos de tamaño en las imágenes (`{width=50%}`) directamente dentro de las celdas de la tabla para controlar su aspecto visual final:
    ```markdown
    | Aceleración máxima del terreno | Aceleración espectral para 0.5 segundos |
    | --- | --- |
    | ![](images/capitulo_1/Figura_4a.png){width=85%} | ![](images/capitulo_1/Figura_4b.png){width=85%} |
    ```

### B. Manejo de Fórmulas y Ecuaciones
*   Ciertas imágenes del documento original pueden representar fórmulas matemáticas en lugar de gráficos.
*   Estas imágenes **deben transcribirse manualmente a sintaxis LaTeX nativa de Quarto** para mejorar la accesibilidad y calidad tipográfica.
*   **Bloques de ecuación:** Usa doble signo de dólar (`$$`) y define la numeración con `\tag{N}`:
    ```latex
    $$S_{DS} = \frac{2}{3} S_{MS} \qquad S_{D1} = \frac{2}{3} S_{M1} \tag{1}$$
    ```
*   **Fórmulas en línea:** Usa signos de dólar simple (`$`), por ejemplo: `$Sa$`.

---

## 5. Limpieza y Conventional Commits

Antes de consolidar los cambios en el repositorio, sigue estas directrices para mantener la higiene del código y el historial de Git:

1. **Eliminar Metadatos Residuales de Windows (NTFS):**
   Si se ha trabajado desde un entorno Windows o compartido por red, elimina los archivos de flujo de datos alternativos (`Zone.Identifier`):
   ```bash
   find . -name "*:Zone.Identifier" -type f -delete
   ```

2. **Mensajes de Commit Estandarizados (Conventional Commits):**
   Realiza commits modulares e informativos en inglés, agrupando las modificaciones por capítulo:
   *   *Estructura del mensaje:* `<type>(<scope>): <description>`
   *   *Ejemplos:*
       ```bash
       git add 01-capitulo-1-*.qmd images/capitulo_1/
       git commit -m "refactor(cap1): migrate images, update paths, and inject manual LaTeX formulas"
       ```
       ```bash
       git add 03-capitulo-3-*.qmd images/capitulo_3/
       git commit -m "refactor(cap3): adjust image locations and fix table syntax inside callout boxes"
       ```
