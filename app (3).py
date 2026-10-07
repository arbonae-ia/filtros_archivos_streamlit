import streamlit as st
import pandas as pd
import uuid
import io

# Configuración inicial de la página
st.set_page_config(
    page_title="Filtro Dinámico de Datos",
    page_icon="📊",
    layout="wide"
)

# Inyectamos algo de CSS para darle el fondo gris al panel de filtros 
# y fijar el pie de página con tus créditos.
st.markdown("""
<style>
    /* Fondo gris suave para el contenedor de filtros */
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: #f1f5f9;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    
    /* Estilos para el footer */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        padding: 15px 0;
        font-size: 14px;
        color: #64748b;
        z-index: 100;
    }
    .footer span {
        font-weight: bold;
        color: #334155;
    }
    
    /* Espacio en la parte inferior para que el footer no tape la tabla */
    .block-container {
        padding-bottom: 80px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file):
    """Carga el archivo Excel o CSV y formatea las fechas."""
    try:
        filename = uploaded_file.name.lower()
        if filename.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif filename.endswith(('.xls', '.xlsx')):
            # Leemos el Excel. Pandas intentará parsear las fechas automáticamente
            df = pd.read_excel(uploaded_file)
        else:
            return None
        
        # Procesar columnas de fecha para que tengan el formato DD-MM-YYYY
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%d-%m-%Y')
                
        # Llenar valores nulos (NaN) con texto vacío para evitar errores en los filtros
        df = df.fillna("")
        return df
    
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

def convert_df_to_csv(df):
    """Convierte el DataFrame a formato CSV en memoria."""
    return df.to_csv(index=False).encode('utf-8')

def convert_df_to_excel(df):
    """Convierte el DataFrame a formato Excel en memoria."""
    output = io.BytesIO()
    # Usamos xlsxwriter como motor
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos Filtrados')
    return output.getvalue()

# Usamos session_state para mantener vivos los filtros al recargar la página
if 'filters' not in st.session_state:
    st.session_state.filters = []

def add_filter():
    """Añade un nuevo ID de filtro a la lista de filtros activos."""
    st.session_state.filters.append(str(uuid.uuid4()))

def remove_filter(filter_id):
    """Elimina un filtro específico."""
    st.session_state.filters.remove(filter_id)
    # Limpiamos las variables de ese filtro del session state para no ocupar memoria
    for key in [f"col_{filter_id}", f"op_{filter_id}", f"val_{filter_id}"]:
        if key in st.session_state:
            del st.session_state[key]

def clear_filters():
    """Elimina todos los filtros."""
    for f_id in st.session_state.filters:
        for key in [f"col_{f_id}", f"op_{f_id}", f"val_{f_id}"]:
            if key in st.session_state:
                del st.session_state[key]
    st.session_state.filters = []


# ==========================================
# INTERFAZ DE USUARIO
# ==========================================
st.title("📊 Filtro Dinámico de Datos")
st.markdown("Carga tu archivo CSV o Excel, aplica los filtros que necesites y exporta el resultado.")

uploaded_file = st.file_uploader("📂 Selecciona tu base de datos (.csv, .xlsx, .xls)", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    # 1. Cargar Datos
    with st.spinner("Procesando datos..."):
        df = load_data(uploaded_file)
    
    if df is not None:
        columns = df.columns.tolist()
        
        # 2. Panel de Filtros (Gris suave gracias al CSS inyectado arriba)
        st.write("### 🎛️ Panel de Filtros")
        
        # Botones de control de filtros
        col_btn1, col_btn2 = st.columns([1, 6])
        with col_btn1:
            st.button("➕ Añadir Filtro", on_click=add_filter)
        with col_btn2:
            if len(st.session_state.filters) > 0:
                st.button("🗑️ Limpiar Todos", on_click=clear_filters)

        # Mostrar las filas de filtros dinámicos
        if len(st.session_state.filters) == 0:
            st.info("No hay filtros activos. Añade uno para comenzar a limpiar tus datos.")
        
        for filter_id in st.session_state.filters:
            # Creamos columnas para organizar (Columna, Operador, Valor, Botón Eliminar)
            f_col1, f_col2, f_col3, f_col4 = st.columns([3, 3, 4, 1])
            
            with f_col1:
                col_name = st.selectbox("Columna", columns, key=f"col_{filter_id}", label_visibility="collapsed")
            
            with f_col2:
                # Determinamos si la columna es numérica para cambiar los operadores
                is_numeric = pd.api.types.is_numeric_dtype(df[col_name].replace("", pd.NA).dropna())
                
                if is_numeric:
                    operators = ['Es igual a', 'No es igual a', 'Mayor que', 'Menor que', 'Mayor o igual', 'Menor o igual', 'Está vacío', 'No está vacío']
                else:
                    operators = ['Contiene', 'No contiene', 'Es igual a', 'No es igual a', 'Empieza con', 'Termina con', 'Está vacío', 'No está vacío']
                    
                operator = st.selectbox("Operador", operators, key=f"op_{filter_id}", label_visibility="collapsed")
            
            with f_col3:
                # Si el operador es de vacío, no mostramos el campo de texto
                if operator not in ['Está vacío', 'No está vacío']:
                    val = st.text_input("Valor", key=f"val_{filter_id}", label_visibility="collapsed", placeholder="Escribe el valor...")
            
            with f_col4:
                st.button("❌", key=f"del_{filter_id}", on_click=remove_filter, args=(filter_id,), help="Eliminar este filtro")

        # 3. Aplicar Filtros
        df_filtered = df.copy()
        mask = pd.Series(True, index=df_filtered.index)
        
        for f_id in st.session_state.filters:
            col = st.session_state.get(f"col_{f_id}")
            op = st.session_state.get(f"op_{f_id}")
            val = st.session_state.get(f"val_{f_id}", "")
            
            if not col or not op: 
                continue
                
            if op not in ['Está vacío', 'No está vacío'] and val == "":
                continue # Ignorar si falta el valor de búsqueda
                
            try:
                if op == 'Está vacío':
                    mask = mask & (df_filtered[col] == "")
                elif op == 'No está vacío':
                    mask = mask & (df_filtered[col] != "")
                
                # Operaciones Numéricas
                elif pd.api.types.is_numeric_dtype(df_filtered[col].replace("", pd.NA).dropna()) and val:
                    val_num = float(val)
                    # Convertimos temporalmente a numérico para comparar, ignorando los vacíos ("")
                    temp_col = pd.to_numeric(df_filtered[col], errors='coerce')
                    
                    if op == 'Es igual a': mask = mask & (temp_col == val_num)
                    elif op == 'No es igual a': mask = mask & (temp_col != val_num)
                    elif op == 'Mayor que': mask = mask & (temp_col > val_num)
                    elif op == 'Menor que': mask = mask & (temp_col < val_num)
                    elif op == 'Mayor o igual': mask = mask & (temp_col >= val_num)
                    elif op == 'Menor o igual': mask = mask & (temp_col <= val_num)
                
                # Operaciones de Texto
                else:
                    col_str = df_filtered[col].astype(str).str.lower()
                    val_str = str(val).lower()
                    
                    if op == 'Contiene': mask = mask & col_str.str.contains(val_str, na=False, regex=False)
                    elif op == 'No contiene': mask = mask & ~col_str.str.contains(val_str, na=False, regex=False)
                    elif op == 'Es igual a': mask = mask & (col_str == val_str)
                    elif op == 'No es igual a': mask = mask & (col_str != val_str)
                    elif op == 'Empieza con': mask = mask & col_str.str.startswith(val_str, na=False)
                    elif op == 'Termina con': mask = mask & col_str.str.endswith(val_str, na=False)
            
            except ValueError:
                # Si el usuario escribe una letra en un filtro numérico, no rompemos la app, solo ignoramos ese filtro.
                pass

        df_filtered = df_filtered[mask]

        # 4. Vista previa y Descargas
        st.write("---")
        res_col1, res_col2 = st.columns([1, 1])
        
        with res_col1:
            st.write(f"### 📋 Vista Previa")
            st.caption(f"Mostrando **{len(df_filtered)}** de {len(df)} registros.")
            
        with res_col2:
            # Botones de exportación alineados a la derecha
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                csv_data = convert_df_to_csv(df_filtered)
                st.download_button(
                    label="⬇️ Exportar CSV",
                    data=csv_data,
                    file_name="datos_filtrados.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with dl_col2:
                excel_data = convert_df_to_excel(df_filtered)
                st.download_button(
                    label="⬇️ Exportar Excel",
                    data=excel_data,
                    file_name="datos_filtrados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        # Mostrar tabla (Pandas renderiza la tabla de forma muy eficiente en Streamlit)
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

# 5. Footer fijo
st.markdown("""
<div class="footer">
    Creado por <span>Yury Arbona</span> | y asistido por la inteligencia artificial 🤖
</div>
""", unsafe_allow_html=True)