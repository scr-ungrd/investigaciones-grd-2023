# Investigaciones en Gestión del Riesgo - Edición 2023

![Banner UNGRD](media/Logo-UNGRD-Horizontal-removebg-preview.png)

## 📖 Descripción General

Este repositorio contiene el código fuente y los activos de la publicación **"Investigaciones en Gestión del Riesgo"**, edición 2023. Este proyecto es una iniciativa de la **Unidad Nacional para la Gestión del Riesgo de Desastres (UNGRD)** de la República de Colombia, diseñada para consolidar y divulgar hallazgos científicos, tecnológicos y de innovación en torno a la gestión del riesgo y la adaptación al cambio climático.

El libro está estructurado como un compendio multidisciplinario que aborda desde la calidad del agua y la amenaza por tsunami hasta la percepción del riesgo y las soluciones basadas en la naturaleza (SbN).

## 🛠️ Tecnologías Utilizadas

El proyecto ha sido desarrollado utilizando herramientas modernas de publicación científica para garantizar un formato accesible, profesional y responsive:

*   **[Quarto](https://quarto.org/):** Sistema de publicación científica y técnica basado en Pandoc.
*   **Markdown / QMD:** Formato de autoría para el contenido de los capítulos.
*   **SCSS/CSS:** Estilizado personalizado mediante `theme.scss` y `styles.css` para alinearse con la identidad visual institucional.
*   **MathJax:** Soporte para la renderización de notación matemática compleja.

## 📂 Estructura del Repositorio

La organización del proyecto sigue el estándar de un libro de Quarto:

```text
├── _quarto.yml           # Configuración global del libro (metadatos, capítulos, tema)
├── index.qmd             # Página de inicio / Presentación institucional
├── theme.scss            # Definiciones de variables y estilos SASS (Custom Bootstrap)
├── styles.css            # Reglas de estilo CSS adicionales
├── media/                # Activos visuales, logotipos y recursos multimedia
├── images/               # Imágenes específicas de los capítulos y portadas
├── workflow/             # Documentación y recursos de apoyo para el flujo de trabajo
└── [00-99]-*.qmd         # Capítulos del libro ordenados secuencialmente
```

## 🚀 Guía de Uso

### Requisitos Previos

Es necesario tener instalado **Quarto CLI** (versión 1.3 o superior) en su sistema. Puede descargarlo desde [quarto.org](https://quarto.org/docs/get-started/).

### Previsualización en Tiempo Real

Para realizar cambios y ver los resultados instantáneamente en el navegador, ejecute:

```bash
quarto preview
```

### Compilación (Renderizado)

Para generar la versión final del libro en formato HTML:

```bash
quarto render
```

Los archivos generados se ubicarán en el directorio `_book/`, listos para ser desplegados en un servidor web.

## 🎨 Personalización Estética

El proyecto utiliza un sistema de temas híbrido:
1.  **Capa Base:** Utiliza el tema `lumen` de Bootstrap.
2.  **Personalización SASS:** El archivo `theme.scss` sobrescribe variables de Bootstrap (colores, tipografía, espaciado) para lograr un acabado "premium" y técnico.
3.  **Ajustes Finos:** `styles.css` se utiliza para reglas específicas de componentes HTML que requieren un control más granular.

## 🖋️ Contenido Académico

El libro incluye investigaciones sobre temas críticos para el territorio colombiano, tales como:
*   Evaluación de amenazas por tsunami y avenidas torrenciales.
*   Gestión del riesgo en corredores viales y sistemas de control sísmico.
*   Dinámicas de inundación en la región de La Mojana.
*   Impacto de incendios forestales en la Orinoquía.
*   Miradas diferenciales y participación comunitaria en la gestión del riesgo.

## ⚖️ Licencia

Este proyecto se distribuye bajo la **Licencia MIT**. Consulte el archivo `LICENSE` para obtener más detalles.

---

**Unidad Nacional para la Gestión del Riesgo de Desastres (UNGRD)**  
*Ciencia, Tecnología e Innovación para la Vida.*  
Bogotá, Colombia.
