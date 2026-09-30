import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Filtro de Datos", layout="wide")
st.title("📊 Aplicación de Filtrado de Datos")
st.markdown("Sube un archivo **CSV** o **Excel**, filtra los datos según la columna que elijas y descarga el resultado.")

# 1. Cargar archivo
uploaded_file = st.file_uploader("Sube tu archivo aquí", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Leer el archivo dependiendo de su extensión
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("Vista previa de los datos originales")
        st.dataframe(df.head(), use_container_width=True)

        # 2. Filtrado dinámico
        st.subheader("Filtros")
        
        # Seleccionar columna a filtrar
        columnas = df.columns.tolist()
        columna_seleccionada = st.selectbox("1. Selecciona la columna a filtrar:", columnas)

        if columna_seleccionada:
            # Obtener valores únicos de esa columna (ignorando valores nulos)
            valores_unicos = df[columna_seleccionada].dropna().unique().tolist()
            
            # Permitir selección múltiple de los valores
            valores_seleccionados = st.multiselect(
                f"2. Selecciona los valores para '{columna_seleccionada}':", 
                valores_unicos
            )

            # Aplicar filtro si se seleccionaron valores, de lo contrario mostrar todo
            if valores_seleccionados:
                df_filtrado = df[df[columna_seleccionada].isin(valores_seleccionados)]
            else:
                df_filtrado = df

            st.subheader(f"Datos Filtrados ({len(df_filtrado)} filas)")
            st.dataframe(df_filtrado, use_container_width=True)

            # 3. Descarga de archivos
            st.subheader("Descargar resultados")
            col1, col2 = st.columns(2)

            # Preparar CSV
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            col1.download_button(
                label="📥 Descargar como CSV",
                data=csv,
                file_name="datos_filtrados.csv",
                mime="text/csv",
            )

            # Preparar Excel en memoria usando io.BytesIO
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtrado.to_excel(writer, index=False, sheet_name='Filtrados')
            
            col2.download_button(
                label="📥 Descargar como Excel",
                data=buffer.getvalue(),
                file_name="datos_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Se produjo un error al leer el archivo: {e}")