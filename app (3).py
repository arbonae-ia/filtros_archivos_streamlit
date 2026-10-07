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

# ==========================================
# ESTILOS (diseño similar al de Gemini)
# ==========================================
st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #f8fafc;
    }

    /* Ocultar elementos por defecto de Streamlit */
    #MainMenu, footer, [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Contenedor principal: sin padding superior, márgenes laterales y espacio para el footer */
    .block-container {
        padding-top: 0 !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        padding-bottom: 90px !important;
        max-width: 100% !important;
    }

    /* Header azul a todo el ancho */
    .app-header {
        background: #2563eb;
        color: white;
        padding: 28px 3rem;
        margin: 0 -3rem 32px -3rem;
        box-shadow: 0 2px 6px rgba(0,0,0,.12);
    }
    .app-header .title-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .app-header h1 {
        color: white !important;
        margin: 0 !important;
        padding: 0 !important;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .app-header p {
        color: #dbeafe;
        margin: 6px 0 0 0;
        font-size: 0.95rem;
    }

    /* Estado vacío (tarjeta blanca con ícono CSV) */
    .empty-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,.08);
        padding: 48px 24px 24px 24px;
        text-align: center;
        margin-bottom: 12px;
    }
    .empty-icon {
        width: 96px;
        height: 96px;
        border-radius: 50%;
        background: #dbeafe;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px auto;
    }
    .empty-card h3 {
        color: #1f2937;
        font-weight: 700;
        margin: 0 0 8px 0;
        padding: 0;
        font-size: 1.35rem;
    }
    .empty-card p {
        color: #6b7280;
        margin: 0;
        font-size: 0.95rem;
    }

    /* Zona de carga estilo dropzone */
    [data-testid="stFileUploaderDropzone"] {
        background: white;
        border: 2px dashed #bfdbfe;
        border-radius: 12px;
        padding: 28px;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: #1d4ed8;
        color: white;
    }

    /* Botones generales */
    .stButton > button, .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid #e5e7eb;
        background: white;
        color: #2563eb;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #2563eb;
        color: #1d4ed8;
        background: #eff6ff;
    }

    /* Inputs y selects redondeados */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    .stTextInput input {
        border-radius: 8px !important;
    }

    /* Títulos de sección */
    h3 {
        color: #1f2937;
        font-weight: 700;
    }

    /* Fondo gris suave para formularios / expanders */
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: #f1f5f9;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }

    /* Footer fijo */
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
</style>
""", unsafe_allow_html=True)

# Header azul propio (reemplaza st.title y el texto de introducción)
st.markdown(
    '<div class="app-header">'
    '<div class="title-row">'
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M3 4h18l-7 8.5V20l-4-2v-5.5z"/></svg>'
    '<h1>Filtro Dinámico de Datos</h1>'
    '</div>'
    '<p>Carga, filtra y exporta tus datos fácilmente</p>'
    '</div>',
    unsafe_allow_html=True
)


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

# Placeholder para el estado vacío: se llena (o no) después de crear el uploader
empty_state = st.empty()

uploaded_file = st.file_uploader(
    "Sube tu base de datos",
    type=['csv', 'xlsx', 'xls'],
    label_visibility="collapsed"
)

if uploaded_file is None:
    empty_state.markdown(
        '<div class="empty-card">'
        '<div class="empty-icon">'
        '<svg width="44" height="44" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" fill="#3b82f6"/>'
        '<path d="M14 2l6 6h-4a2 2 0 0 1-2-2z" fill="#93c5fd"/>'
        '<text x="12" y="19" font-size="6" font-weight="700" text-anchor="middle" fill="white" '
        'font-family="Arial, sans-serif">CSV</text></svg>'
        '</div>'
        '<h3>Sube tu base de datos</h3>'
        '<p>Soporta formatos CSV, XLSX y XLS. Identificaremos tus columnas automáticamente.</p>'
        '</div>',
        unsafe_allow_html=True
    )

if uploaded_file is not None:
    # 1. Cargar Datos
    with st.spinner("Procesando datos..."):
        df = load_data(uploaded_file)

    if df is not None:
        columns = df.columns.tolist()

        # 2. Panel de Filtros
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
                continue  # Ignorar si falta el valor de búsqueda

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
            st.write("### 📋 Vista Previa")
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
