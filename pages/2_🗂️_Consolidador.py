import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import io

# --- LÓGICA DE PROCESAMIENTO (ADAPTADA) ---
# Adaptamos las funciones para que retornen los logs en vez de imprimirlos con un callback

def procesar_archivos(lista_archivos):
    logs = []
    lista_df = []
    for archivo in lista_archivos:
        try:
            if archivo.name.endswith('.csv'):
                df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8-sig', dtype=str)
            else:
                df = pd.read_excel(archivo, dtype=str)
            lista_df.append(df)
            logs.append(f"✅ Archivo leído correctamente: {archivo.name}")
        except Exception as e:
            logs.append(f"❌ Error al leer el archivo {archivo.name}: {e}")
    
    if not lista_df:
        logs.append("Error: No se pudo procesar ningún archivo.")
        return None, logs
    
    df_combinado = pd.concat(lista_df, ignore_index=True)
    
    # Limpieza y procesamiento
    # (Nombres de columnas definidos globalmente)
    COLUMNA_FECHA_CREACION = 'Fecha_Creacion'
    COLUMNA_UNIDADES_PLAN = 'Unidades_Asignadas'
    COLUMNA_HORAS_PLAN = 'Horas_Utilizadas'
    COLUMNA_UNIDADES_REALES = 'Unidades Reales'
    COLUMNA_HORAS_REALES = 'Horas reales'
    COLUMNAS_CLAVE = ['Semana', 'Linea', 'PRTNUM']

    df_combinado[COLUMNA_FECHA_CREACION] = pd.to_datetime(df_combinado[COLUMNA_FECHA_CREACION], errors='coerce')
    columnas_numericas = [COLUMNA_UNIDADES_PLAN, COLUMNA_HORAS_PLAN, COLUMNA_UNIDADES_REALES, COLUMNA_HORAS_REALES, 'Productividad']
    for col in columnas_numericas:
        if col in df_combinado.columns:
            df_combinado[col] = df_combinado[col].astype(str).str.replace(',', '.', regex=False)
            df_combinado[col] = pd.to_numeric(df_combinado[col], errors='coerce').fillna(0)
        else:
            logs.append(f"⚠️ Advertencia: La columna '{col}' no se encontró. Se asumirá como 0.")
            df_combinado[col] = 0

    df_combinado.dropna(subset=[COLUMNA_FECHA_CREACION] + COLUMNAS_CLAVE, inplace=True)
    df_combinado = df_combinado.sort_values(by=[COLUMNA_UNIDADES_REALES, COLUMNA_FECHA_CREACION], ascending=[False, False])
    num_filas_antes = len(df_combinado)
    df_limpio = df_combinado.drop_duplicates(subset=COLUMNAS_CLAVE, keep='first')
    num_filas_despues = len(df_limpio)
    logs.append(f"Se procesaron {num_filas_antes} filas en total.")
    logs.append(f"Después de la limpieza, quedaron {num_filas_despues} tareas únicas.")
    
    df_final = df_limpio.sort_index()

    # Calcular KPIs
    df_final['Capacidad Disponible (H)'] = df_final[COLUMNA_HORAS_PLAN] - df_final[COLUMNA_HORAS_REALES]
    df_final['% Cumplimiento Unidades'] = np.divide(df_final[COLUMNA_UNIDADES_REALES] * 100, df_final[COLUMNA_UNIDADES_PLAN], out=np.zeros_like(df_final[COLUMNA_UNIDADES_REALES], dtype=float), where=df_final[COLUMNA_UNIDADES_PLAN] != 0)
    df_final['Productividad Real (Ud/H)'] = np.divide(df_final[COLUMNA_UNIDADES_REALES], df_final[COLUMNA_HORAS_REALES], out=np.zeros_like(df_final[COLUMNA_UNIDADES_REALES], dtype=float), where=df_final[COLUMNA_HORAS_REALES] != 0)
    
    return df_final, logs

# --- INTERFAZ DE STREAMLIT ---
st.title("🗂️ Consolidador de Reportes de Producción")

archivos_cargados = st.file_uploader(
    "Carga uno o más archivos de reporte (.xlsx o .csv)",
    type=['xlsx', 'csv'],
    accept_multiple_files=True
)

if archivos_cargados:
    st.info(f"Se han cargado {len(archivos_cargados)} archivos. Haz clic en el botón para procesarlos.")
    
    if st.button("🧩 Consolidar Reportes", type="primary", use_container_width=True):
        with st.spinner("Combinando y analizando reportes..."):
            df_resultado, logs = procesar_archivos(archivos_cargados)

            with st.expander("Ver registro del proceso"):
                st.text("\n".join(logs))

            if df_resultado is not None:
                st.subheader("📊 Resumen del Reporte Consolidado")
                st.dataframe(df_resultado)
                
                # Resumen de capacidad
                total_horas_asignadas = df_resultado['Horas_Utilizadas'].sum()
                total_horas_reales = df_resultado['Horas reales'].sum()
                porcentaje_utilizado = (total_horas_reales / total_horas_asignadas * 100) if total_horas_asignadas > 0 else 0
                
                st.subheader("KPIs Globales")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Horas Asignadas", f"{total_horas_asignadas:.2f} H")
                col2.metric("Total Horas Reales", f"{total_horas_reales:.2f} H")
                col3.metric("% Capacidad Utilizada", f"{porcentaje_utilizado:.2f}%")

                # Botón de descarga
                output = io.BytesIO()
                df_resultado.to_excel(output, index=False, sheet_name='Reporte_Consolidado')
                excel_bytes = output.getvalue()

                st.download_button(
                    label="📥 Descargar Reporte Consolidado",
                    data=excel_bytes,
                    file_name=f"Reporte_Consolidado_{date.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    st.info("Por favor, carga los reportes que deseas consolidar.")