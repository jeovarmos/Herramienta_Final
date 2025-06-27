import streamlit as st

st.set_page_config(
    page_title="Herramientas DHL",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Herramientas de Planificación y Consolidación DHL")

st.markdown("""
### ¡Bienvenido!

Esta aplicación web centraliza dos herramientas clave para la gestión de operaciones:

1.  **📊 Planificador de Reetiquetado:**
    - Carga un inventario y genera un plan de trabajo semanal optimizado.
    - Permite priorizar por volumen de inventario o por un archivo externo.
    - Calcula las horas y unidades a asignar por línea de producción.

2.  **🗂️ Consolidador de Reportes:**
    - Combina múltiples reportes de producción (generados por el planificador) en un único archivo.
    - Calcula KPIs de cumplimiento y capacidad para tener una visión global del rendimiento.

**👈 Para comenzar, selecciona una herramienta del menú de navegación a la izquierda.**
""")

st.info("Esta aplicación es una versión web de las herramientas de escritorio originales, diseñada para ser más accesible y fácil de usar.", icon="💡")