import streamlit as st
import pandas as pd
import numpy as np
import math
from datetime import datetime
import io

# --- LÓGICA DE PROCESAMIENTO (ADAPTADA DE TU CÓDIGO) ---
# Traemos las funciones lógicas de tu app Tkinter. Son reutilizables.

def generar_programacion_logica(df, prioridad_inventario, semana_inicio, priorizacion_df=None):
    # (Esta es una adaptación directa de tu lógica de `generar_programacion`)
    MIN_UNIDADES_POR_ASIGNACION = 10
    df.columns = [col.strip().upper() for col in df.columns]
    
    if priorizacion_df is not None:
        df = pd.merge(df, priorizacion_df[['PRTNUM', 'PRIORIDAD']], on='PRTNUM', how='left')
        df['PRIORIDAD'] = pd.to_numeric(df['PRIORIDAD'], errors='coerce').fillna(99)
    else:
        df['PRIORIDAD'] = 99

    df['HORAS_REQUERIDAS'] = df['INVENTARIO'] / df['PROD. HORA']
    abc_priority = {'A': 1, 'B': 2, 'C': 3}
    df['ABC_PRIORITY'] = df['CLASIFICACION ABC'].map(abc_priority).fillna(99)
    
    df_sorted = df.sort_values(
        by=['PRIORIDAD', 'ABC_PRIORITY', 'INVENTARIO', 'PROD. HORA'],
        ascending=[True, True, prioridad_inventario == "menor", False]
    )
    
    asignaciones = []
    inventario_restante = df_sorted.set_index('PRTNUM')['INVENTARIO'].copy()
    df_sorted.set_index('PRTNUM', inplace=True)
    
    # En la app real, las horas por línea vendrían de la UI. Aquí usamos un valor fijo.
    horas_por_linea = 37.5
    lineas_activas = [f"L{i:02d}" for i in range(1, 13)]

    for semana in range(semana_inicio, semana_inicio + 52):
        for linea in lineas_activas:
            horas_disponibles = horas_por_linea
            for prtnum, producto in df_sorted.iterrows():
                if horas_disponibles <= 0.01: break
                if inventario_restante.loc[prtnum] <= 0: continue
                
                unidades_max_linea = math.floor(horas_disponibles * producto['PROD. HORA'])
                unidades_disponibles_stock = int(inventario_restante.loc[prtnum])
                unidades_a_asignar = min(unidades_disponibles_stock, unidades_max_linea)
                
                es_el_remate_final = (unidades_a_asignar == unidades_disponibles_stock)
                es_un_lote_significativo = (unidades_a_asignar >= MIN_UNIDADES_POR_ASIGNACION)

                if unidades_a_asignar > 0 and (es_un_lote_significativo or es_el_remate_final):
                    horas_necesarias = unidades_a_asignar / producto['PROD. HORA']
                    asignaciones.append({
                        'Semana': semana, 'Linea': linea, 'PRTNUM': prtnum,
                        'Descripcion': producto.get('DESCRIPCION', 'N/A'),
                        'Clasificacion_ABC': producto['CLASIFICACION ABC'],
                        'Prioridad_Externa': 'Pred.' if producto['PRIORIDAD'] == 99 else producto['PRIORIDAD'],
                        'Unidades_Asignadas': int(unidades_a_asignar),
                        'Horas_Utilizadas': round(horas_necesarias, 2),
                        'Productividad': producto['PROD. HORA'],
                        'Unidades Reales': '', 'Horas reales': ''
                    })
                    inventario_restante.loc[prtnum] -= unidades_a_asignar
                    horas_disponibles -= horas_necesarias
    
    if not asignaciones:
        return None

    df_asignaciones = pd.DataFrame(asignaciones)
    fecha_creacion = datetime.now().strftime('%Y-%m-%d')
    df_asignaciones.insert(0, 'Fecha_Creacion', fecha_creacion)
    return df_asignaciones

# --- INTERFAZ DE STREAMLIT ---
st.title("📊 Planificador de Reetiquetado")

# Barra lateral para los controles
with st.sidebar:
    st.header("⚙️ Controles de Planificación")
    
    archivo_principal = st.file_uploader("1. Cargar archivo de inventario", type=['xlsx', 'xls'])
    archivo_priorizacion = st.file_uploader("2. Cargar archivo de priorización (Opcional)", type=['xlsx', 'xls', 'csv'])
    
    prioridad_inventario = st.radio(
        "Priorización de Inventario",
        ["mayor", "menor"],
        captions=["Mayor inventario primero", "Menor inventario primero"],
        horizontal=True
    )
    semana_inicio = st.number_input("Semana de Inicio", value=datetime.now().isocalendar()[1], min_value=1, max_value=52)

if archivo_principal:
    df_principal = pd.read_excel(archivo_principal, sheet_name='Consolidado', dtype={'PRTNUM': str})
    st.success(f"Archivo '{archivo_principal.name}' cargado con {len(df_principal)} filas.")
    
    df_priorizacion = None
    if archivo_priorizacion:
        try:
            if archivo_priorizacion.name.endswith('.csv'):
                df_priorizacion = pd.read_csv(archivo_priorizacion, dtype={'PRTNUM': str})
            else:
                df_priorizacion = pd.read_excel(archivo_priorizacion, dtype={'PRTNUM': str})
            st.info(f"Archivo de priorización '{archivo_priorizacion.name}' cargado.")
        except Exception as e:
            st.error(f"No se pudo leer el archivo de priorización: {e}")

    if st.button("🚀 Generar Planificación", type="primary", use_container_width=True):
        with st.spinner("Calculando..."):
            resultado = generar_programacion_logica(df_principal, prioridad_inventario, semana_inicio, df_priorizacion)
            
            if resultado is not None:
                st.subheader("✅ Planificación Generada")
                st.dataframe(resultado)
                
                # Botón de descarga
                output = io.BytesIO()
                resultado.to_excel(output, index=False, sheet_name='Planificacion')
                excel_bytes = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Planificación en Excel",
                    data=excel_bytes,
                    file_name=f"Planificacion_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("No se generaron asignaciones con los criterios actuales.")
else:
    st.info("Por favor, carga un archivo de inventario para comenzar.")