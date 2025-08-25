import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pandas as pd
from datetime import datetime
import json
import os
import io

# Definición de criterios de acreditación
CRITERIOS_ACREDITACION = {
    "I. DIMENSIÓN DOCENCIA Y RESULTADOS DEL PROCESO FORMATIVO": {
        "Criterio 1. Modelo educativo y diseño curricular": "La formulación del modelo educativo define las características y objetivos de los programas. El diseño e implementación curricular se orienta por procedimientos institucionales que guían el desarrollo de los programas conducentes a títulos y grados académicos.",
        "Criterio 2. Procesos y resultados de enseñanza y aprendizaje": "El diseño e implementación de los programas de enseñanza y aprendizaje provee las condiciones necesarias para el logro del perfil de egreso por parte de los estudiantes, en los distintos niveles, programas y modalidades.",
        "Criterio 3. Cuerpo académico": "El cuerpo académico cuenta con la dedicación y credenciales académicas y profesionales para el desarrollo del proceso de enseñanza y aprendizaje de toda la oferta educativa.",
        "Criterio 4. Investigación, innovación docente y mejora del proceso formativo": "La universidad emprende y desarrolla acciones de investigación y/o innovación sobre su experiencia docente que impactan positivamente en el proceso formativo, en lo disciplinar y en lo pedagógico, de acuerdo con el proyecto institucional."
    },
    "II. DIMENSIÓN GESTIÓN ESTRATÉGICA Y RECURSOS INSTITUCIONALES": {
        "Criterio 5. Gobierno y estructura organizacional": "La universidad cuenta con un sistema de gobierno y una estructura organizacional que le permiten gestionar todas las funciones institucionales conforme a su misión, visión, propósitos y tamaño.",
        "Criterio 6. Gestión y desarrollo de personas": "La universidad posee y aplica mecanismos para los procesos de reclutamiento, selección, inducción, desarrollo profesional, evaluación y retiro.",
        "Criterio 7. Gestión de la convivencia, equidad de género, diversidad e inclusión": "La universidad promueve el desarrollo integral de su comunidad en todo su quehacer y responde en su gestión a los desafíos en materia de convivencia, equidad de género, respeto a la diversidad e inclusión.",
        "Criterio 8. Gestión de recursos": "La universidad cuenta con los medios necesarios para el desarrollo de sus actividades, así como con políticas y mecanismos para la gestión de los recursos operativos y económicos."
    },
    "III. DIMENSIÓN ASEGURAMIENTO INTERNO DE LA CALIDAD": {
        "Criterio 9. Gestión y resultados del aseguramiento interno de la calidad": "La universidad define, implementa, monitorea y optimiza su sistema interno de aseguramiento de la calidad.",
        "Criterio 10. Aseguramiento de la calidad de los programas formativos": "La institución dispone y aplica normativa o procedimientos vigentes para la mejora continua de sus procesos de formación, en todos los programas conducentes a títulos y grados académicos."
    },
    "IV. DIMENSIÓN VINCULACIÓN CON EL MEDIO": {
        "Criterio 11. Política y gestión de la vinculación con el medio": "La función de vinculación con el medio es bidireccional, es decir, una construcción conjunta de la universidad con sus grupos relevantes de interés.",
        "Criterio 12. Resultados e impacto de la vinculación con el medio": "La universidad realiza acciones de vinculación con el medio que tienen un impacto positivo en su entorno significativo o a nivel nacional, y en la formación de los estudiantes."
    },
    "V. DIMENSIÓN INVESTIGACIÓN, CREACIÓN Y/O INNOVACIÓN": {
        "Criterio 13. Política y gestión de la investigación, creación y/o innovación": "La investigación, creación y/o innovación están presentes de manera explícita en la misión y propósitos declarados por la universidad.",
        "Criterio 14. Resultados de la investigación, creación y/o innovación": "La universidad obtiene resultados de investigación, creación y/o innovación que generan impacto en el medio interno o externo (académico, cultural, servicios, productivo o social)."
    }
}

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evidencias - Acreditación Universitaria",
    page_icon="📚",
    layout="wide"
)

# Función para inicializar Google Sheets
@st.cache_resource
def init_google_sheets():
    """Inicializa la conexión con Google Sheets usando las credenciales de los secrets"""
    try:
        # Obtener credenciales desde los secrets de Replit
        google_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        if not google_credentials:
            st.error("No se encontraron las credenciales de Google Sheets en los secrets")
            return None
            
        # Parsear las credenciales JSON
        creds_dict = json.loads(google_credentials)
        
        # Configurar los scopes necesarios
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Crear las credenciales
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        # Inicializar el cliente de gspread
        client = gspread.authorize(credentials)
        
        return client
    except Exception as e:
        st.error(f"Error al inicializar Google Sheets: {str(e)}")
        return None

# Función para inicializar Google Drive
@st.cache_resource
def init_google_drive():
    """Inicializa la conexión con Google Drive usando las credenciales de los secrets"""
    try:
        # Obtener credenciales desde los secrets de Replit
        google_credentials = os.getenv("GOOGLE_DRIVE_CREDENTIALS") or os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        if not google_credentials:
            st.error("No se encontraron las credenciales de Google Drive en los secrets")
            return None
            
        # Parsear las credenciales JSON
        creds_dict = json.loads(google_credentials)
        
        # Configurar los scopes necesarios
        scopes = [
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Crear las credenciales
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        # Inicializar el cliente de Google Drive
        drive_service = build('drive', 'v3', credentials=credentials)
        
        return drive_service
    except Exception as e:
        st.error(f"Error al inicializar Google Drive: {str(e)}")
        return None

# Función para obtener usuarios desde Google Sheets
@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_users_data(_client):
    """Obtiene los datos de usuarios desde la hoja de Google Sheets"""
    try:
        # Abrir la hoja de cálculo
        sheet = _client.open("BaseDeDatosAppReha")
        
        # Obtener la pestaña de usuarios
        usuarios_worksheet = sheet.worksheet("usuarios")
        
        # Obtener todos los datos
        data = usuarios_worksheet.get_all_records()
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error al obtener datos de usuarios: {str(e)}")
        return pd.DataFrame()

# Función para obtener evidencias desde Google Sheets
@st.cache_data(ttl=60)  # Cache por 1 minuto
def get_evidencias_data(_client):
    """Obtiene los datos de evidencias desde la hoja de Google Sheets"""
    try:
        # Abrir la hoja de cálculo
        sheet = _client.open("BaseDeDatosAppReha")
        
        # Obtener la pestaña de evidencias
        evidencias_worksheet = sheet.worksheet("evidencias")
        
        # Obtener todos los datos
        data = evidencias_worksheet.get_all_records()
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error al obtener datos de evidencias: {str(e)}")
        return pd.DataFrame()

# Función para agregar nueva evidencia
def add_evidencia(client, programa, subido_por, url_cloudinary, criterio, dimension, nombre_archivo):
    """Agrega una nueva evidencia a la hoja de Google Sheets"""
    try:
        # Abrir la hoja de cálculo
        sheet = client.open("BaseDeDatosAppReha")
        
        # Obtener la pestaña de evidencias
        evidencias_worksheet = sheet.worksheet("evidencias")
        
        # Crear nueva fila con los datos
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [programa, subido_por, url_cloudinary, fecha_hora, criterio, dimension, nombre_archivo]
        
        # Agregar la fila
        evidencias_worksheet.append_row(new_row)
        
        return True
    except Exception as e:
        st.error(f"Error al agregar evidencia: {str(e)}")
        return False

# Función para subir archivo a Google Drive
def upload_to_google_drive(file, folder_name, drive_service):
    """Sube un archivo a Google Drive y retorna la URL pública"""
    try:
        # Usar el folder ID específico proporcionado
        folder_id = "1GWFa2LeZ4BLwDLcTpXe3zEpD9aEuI_pZ"
        
        # Preparar los metadatos del archivo
        file_metadata = {
            'name': file.name,
            'parents': [folder_id]
        }
        
        # Crear el media upload
        media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.type)
        
        # Subir el archivo
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink'
        ).execute()
        
        # Hacer el archivo público para lectura
        drive_service.permissions().create(
            fileId=uploaded_file['id'],
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        return uploaded_file.get('webViewLink')
    except Exception as e:
        st.error(f"Error al subir archivo a Google Drive: {str(e)}")
        return None

def create_or_get_folder(drive_service, folder_name):
    """Crea una carpeta en Google Drive o retorna su ID si ya existe"""
    try:
        # Buscar si la carpeta ya existe
        results = drive_service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        else:
            # Crear nueva carpeta
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            return folder.get('id')
    except Exception as e:
        st.error(f"Error al crear/obtener carpeta: {str(e)}")
        return None

# Función de autenticación
def authenticate_user(email, users_df):
    """Autentica al usuario y retorna sus datos"""
    if users_df.empty:
        return None
        
    user_data = users_df[users_df['correo'].str.lower() == email.lower()]
    
    if not user_data.empty:
        return {
            'correo': user_data.iloc[0]['correo'],
            'programa': user_data.iloc[0]['programa'],
            'rol': user_data.iloc[0]['rol']
        }
    return None

# Función para mostrar el login
def show_login():
    """Muestra la pantalla de login"""
    st.title("🔐 Iniciar Sesión")
    st.write("Sistema de Gestión de Evidencias de Acreditación Universitaria")
    
    with st.form("login_form"):
        email = st.text_input("Correo electrónico", placeholder="usuario@universidad.edu")
        submit_button = st.form_submit_button("Iniciar Sesión")
        
        if submit_button:
            if not email:
                st.error("Por favor ingrese su correo electrónico")
                return
                
            # Inicializar Google Sheets
            client = init_google_sheets()
            if not client:
                return
                
            # Obtener datos de usuarios
            users_df = get_users_data(client)
            if users_df.empty:
                st.error("No se pudieron cargar los datos de usuarios")
                return
                
            # Autenticar usuario
            user_data = authenticate_user(email, users_df)
            
            if user_data:
                st.session_state.user_data = user_data
                st.session_state.logged_in = True
                st.success(f"¡Bienvenido! Ingresando como {user_data['rol']}")
                st.rerun()
            else:
                st.error("Correo no encontrado en la base de datos")

# Función para mostrar panel de usuario
def show_user_panel():
    """Muestra el panel para usuarios regulares"""
    user_data = st.session_state.user_data
    
    st.title(f"📋 Panel de Usuario - {user_data['programa']}")
    st.write(f"Bienvenido, {user_data['correo']}")
    
    # Sidebar con información del usuario
    with st.sidebar:
        st.header("Información del Usuario")
        st.write(f"**Correo:** {user_data['correo']}")
        st.write(f"**Programa:** {user_data['programa']}")
        st.write(f"**Rol:** {user_data['rol']}")
        
        if st.button("Cerrar Sesión"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    # Inicializar servicios
    client = init_google_sheets()
    drive_service = init_google_drive()
    
    if not client or not drive_service:
        st.error("Error al inicializar los servicios necesarios")
        return
    
    # Tabs para organizar la interfaz
    tab1, tab2 = st.tabs(["📤 Subir Evidencia", "📋 Mis Evidencias"])
    
    with tab1:
        st.header("Subir Evidencias por Criterios de Acreditación")
        
        # Selector de dimensión
        dimension_seleccionada = st.selectbox(
            "Seleccione la Dimensión",
            list(CRITERIOS_ACREDITACION.keys()),
            help="Seleccione la dimensión de acreditación correspondiente"
        )
        
        # Selector de criterio basado en la dimensión
        criterios_disponibles = list(CRITERIOS_ACREDITACION[dimension_seleccionada].keys())
        criterio_seleccionado = st.selectbox(
            "Seleccione el Criterio",
            criterios_disponibles,
            help="Seleccione el criterio específico dentro de la dimensión"
        )
        
        # Mostrar descripción del criterio
        descripcion = CRITERIOS_ACREDITACION[dimension_seleccionada][criterio_seleccionado]
        st.info(f"**Descripción:** {descripcion}")
        
        # Subida de múltiples archivos
        uploaded_files = st.file_uploader(
            f"Seleccione los archivos para {criterio_seleccionado}",
            type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'],
            help="Formatos permitidos: PDF, imágenes, documentos de Office",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} archivo(s) seleccionado(s):**")
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size / 1024:.2f} KB)")
            
            if st.button("Subir Evidencias", type="primary"):
                progress_bar = st.progress(0)
                total_files = len(uploaded_files)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    progress_bar.progress((i + 1) / total_files)
                    
                    with st.spinner(f"Subiendo {uploaded_file.name}..."):
                        # Subir a Google Drive
                        url_drive = upload_to_google_drive(uploaded_file, user_data['programa'], drive_service)
                        
                        if url_drive:
                            # Registrar en Google Sheets
                            success = add_evidencia(
                                client, 
                                user_data['programa'], 
                                user_data['correo'], 
                                url_drive,
                                criterio_seleccionado,
                                dimension_seleccionada,
                                uploaded_file.name
                            )
                            
                            if success:
                                st.success(f"✅ {uploaded_file.name} subido exitosamente!")
                            else:
                                st.error(f"❌ Error al registrar {uploaded_file.name} en la base de datos")
                        else:
                            st.error(f"❌ Error al subir {uploaded_file.name}")
                
                # Limpiar cache para mostrar datos actualizados
                st.cache_data.clear()
                st.balloons()
                st.success(f"🎉 Proceso completado! {total_files} archivo(s) procesado(s)")
    
    with tab2:
        st.header("Mis Evidencias por Criterios")
        
        # Obtener evidencias del usuario
        evidencias_df = get_evidencias_data(client)
        
        if not evidencias_df.empty:
            # Filtrar por programa del usuario
            user_evidencias = evidencias_df[evidencias_df['programa'] == user_data['programa']]
            
            if not user_evidencias.empty:
                # Mostrar estadísticas
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total de Evidencias", len(user_evidencias))
                
                # Verificar si existen las nuevas columnas
                if 'criterio' in user_evidencias.columns and 'dimension' in user_evidencias.columns:
                    with col2:
                        criterios_unicos = int(pd.Series(user_evidencias['criterio']).nunique())
                        st.metric("Criterios Cubiertos", criterios_unicos)
                    
                    # Selector de filtro por dimensión
                    st.subheader("🔍 Filtrar por Dimensión")
                    dimensiones_disponibles = ['Todas'] + sorted(pd.Series(user_evidencias['dimension']).unique().tolist())
                    dimension_filtro = st.selectbox("Filtrar por Dimensión", dimensiones_disponibles)
                    
                    # Aplicar filtro
                    df_mostrar = user_evidencias.copy()
                    if dimension_filtro != 'Todas':
                        df_mostrar = df_mostrar[df_mostrar['dimension'] == dimension_filtro]
                    
                    # Mostrar evidencias agrupadas por criterio
                    st.subheader("📋 Evidencias por Criterio")
                    
                    if len(df_mostrar) > 0:
                        for criterio in sorted(pd.Series(df_mostrar['criterio']).unique()):
                            criterio_evidencias = df_mostrar[df_mostrar['criterio'] == criterio]
                            
                            with st.expander(f"{criterio} ({len(criterio_evidencias)} archivo(s))"):
                                # Mostrar tabla para este criterio
                                columns_to_show = ['nombre_archivo', 'fecha_hora', 'url_cloudinary']
                                available_columns = [col for col in columns_to_show if col in criterio_evidencias.columns]
                                
                                if 'nombre_archivo' not in criterio_evidencias.columns:
                                    available_columns = ['fecha_hora', 'url_cloudinary']
                                
                                st.dataframe(
                                    criterio_evidencias[available_columns],
                                    column_config={
                                        'nombre_archivo': 'Nombre del Archivo',
                                        'fecha_hora': 'Fecha y Hora',
                                        'url_cloudinary': st.column_config.LinkColumn(
                                            'Enlace al Archivo',
                                            display_text="Ver Archivo"
                                        )
                                    },
                                    use_container_width=True,
                                    hide_index=True
                                )
                    else:
                        st.info("No hay evidencias para la dimensión seleccionada.")
                        
                else:
                    # Formato antiguo - mostrar tabla simple
                    st.warning("Algunas evidencias están en formato anterior. Mostrando vista simplificada.")
                    columns_to_show = ['fecha_hora', 'subido_por', 'url_cloudinary']
                    available_columns = [col for col in columns_to_show if col in user_evidencias.columns]
                    
                    st.dataframe(
                        user_evidencias[available_columns],
                        column_config={
                            'fecha_hora': 'Fecha y Hora',
                            'subido_por': 'Subido por',
                            'url_cloudinary': st.column_config.LinkColumn(
                                'Enlace al Archivo',
                                display_text="Ver Archivo"
                            )
                        },
                        use_container_width=True
                    )
            else:
                st.info("No hay evidencias registradas para tu programa aún.")
        else:
            st.info("No se pudieron cargar las evidencias.")

# Función para mostrar panel de admin
def show_admin_panel():
    """Muestra el panel para administradores"""
    user_data = st.session_state.user_data
    
    st.title("👨‍💼 Panel de Administrador")
    st.write(f"Bienvenido, {user_data['correo']}")
    
    # Sidebar con información del usuario
    with st.sidebar:
        st.header("Información del Usuario")
        st.write(f"**Correo:** {user_data['correo']}")
        st.write(f"**Programa:** {user_data['programa']}")
        st.write(f"**Rol:** {user_data['rol']}")
        
        if st.button("Cerrar Sesión"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    # Inicializar servicios
    client = init_google_sheets()
    
    if not client:
        st.error("Error al inicializar Google Sheets")
        return
    
    # Obtener datos
    evidencias_df = get_evidencias_data(client)
    users_df = get_users_data(client)
    
    if evidencias_df.empty:
        st.info("No hay evidencias registradas en el sistema.")
        return
    
    # Estadísticas generales
    st.header("📊 Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Evidencias", len(evidencias_df))
    
    with col2:
        unique_programs = int(evidencias_df['programa'].nunique())
        st.metric("Programas Activos", unique_programs)
    
    with col3:
        unique_users = int(evidencias_df['subido_por'].nunique())
        st.metric("Usuarios Activos", unique_users)
    
    with col4:
        # Evidencias del último mes
        today = datetime.now()
        evidencias_df['fecha_hora'] = pd.to_datetime(evidencias_df['fecha_hora'], errors='coerce')
        recent_evidencias = evidencias_df[
            evidencias_df['fecha_hora'] > (today - pd.Timedelta(days=30))
        ]
        st.metric("Evidencias (30 días)", len(recent_evidencias))
    
    # Filtros
    st.header("🔍 Filtrar Evidencias")
    
    # Verificar si existen las nuevas columnas
    has_new_columns = 'criterio' in evidencias_df.columns and 'dimension' in evidencias_df.columns
    
    if has_new_columns:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por programa
            programas_disponibles = ['Todos'] + sorted(evidencias_df['programa'].unique().tolist())
            programa_seleccionado = st.selectbox("Filtrar por Programa", programas_disponibles)
        
        with col2:
            # Filtro por dimensión
            dimensiones_disponibles = ['Todas'] + sorted(pd.Series(evidencias_df['dimension']).unique().tolist())
            dimension_seleccionada = st.selectbox("Filtrar por Dimensión", dimensiones_disponibles)
            
        with col3:
            # Filtro por criterio
            if dimension_seleccionada != 'Todas':
                criterios_filtrados = pd.Series(evidencias_df[evidencias_df['dimension'] == dimension_seleccionada]['criterio']).unique()
                criterios_disponibles = ['Todos'] + sorted(criterios_filtrados.tolist())
            else:
                criterios_disponibles = ['Todos'] + sorted(pd.Series(evidencias_df['criterio']).unique().tolist())
            criterio_seleccionado = st.selectbox("Filtrar por Criterio", criterios_disponibles)
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro por programa
            programas_disponibles = ['Todos'] + sorted(evidencias_df['programa'].unique().tolist())
            programa_seleccionado = st.selectbox("Filtrar por Programa", programas_disponibles)
        
        with col2:
            dimension_seleccionada = 'Todas'
            criterio_seleccionado = 'Todos'
    
    # Filtro por fecha
    st.subheader("📅 Filtrar por Fecha")
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input("Desde", value=(today.date() - pd.Timedelta(days=30)))
    with col2:
        fecha_hasta = st.date_input("Hasta", value=today.date())
    
    # Aplicar filtros
    df_filtrado = evidencias_df.copy()
    
    if programa_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['programa'] == programa_seleccionado]
    
    if has_new_columns:
        if dimension_seleccionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['dimension'] == dimension_seleccionada]
        
        if criterio_seleccionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['criterio'] == criterio_seleccionado]
    
    # Filtrar por fecha
    if len(df_filtrado) > 0 and 'fecha_hora' in df_filtrado.columns:
        fecha_serie = pd.to_datetime(df_filtrado['fecha_hora'], errors='coerce')
        df_filtrado = df_filtrado[
            (fecha_serie.dt.date >= fecha_desde) & 
            (fecha_serie.dt.date <= fecha_hasta)
        ]
    
    # Mostrar resultados
    st.header("📋 Evidencias Filtradas")
    
    if len(df_filtrado) > 0:
        st.write(f"Mostrando {len(df_filtrado)} evidencias")
        
        # Determinar columnas a mostrar basándose en las disponibles
        if has_new_columns and 'nombre_archivo' in df_filtrado.columns:
            columns_to_show = ['programa', 'criterio', 'nombre_archivo', 'subido_por', 'fecha_hora', 'url_cloudinary']
            column_config = {
                'programa': 'Programa',
                'criterio': 'Criterio',
                'nombre_archivo': 'Nombre del Archivo',
                'subido_por': 'Subido por',
                'fecha_hora': 'Fecha y Hora',
                'url_cloudinary': st.column_config.LinkColumn(
                    'Enlace al Archivo',
                    display_text="Ver Archivo"
                )
            }
        else:
            # Formato anterior o columnas limitadas
            columns_to_show = ['programa', 'subido_por', 'fecha_hora', 'url_cloudinary']
            column_config = {
                'programa': 'Programa',
                'subido_por': 'Subido por',
                'fecha_hora': 'Fecha y Hora',
                'url_cloudinary': st.column_config.LinkColumn(
                    'Enlace al Archivo',
                    display_text="Ver Archivo"
                )
            }
        
        # Filtrar solo las columnas que existen
        available_columns = [col for col in columns_to_show if col in df_filtrado.columns]
        
        # Tabla con todas las evidencias
        st.dataframe(
            df_filtrado[available_columns],
            column_config=column_config,
            use_container_width=True
        )
        
        # Gráficos de distribución
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Distribución por Programa")
            programa_counts = pd.Series(df_filtrado['programa']).value_counts()
            st.bar_chart(programa_counts)
        
        if has_new_columns:
            with col2:
                st.subheader("📊 Distribución por Criterio")
                criterio_counts = pd.Series(df_filtrado['criterio']).value_counts()
                st.bar_chart(criterio_counts)
    else:
        st.info("No se encontraron evidencias con los filtros aplicados.")

# Función principal
def main():
    """Función principal de la aplicación"""
    
    # Inicializar session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Verificar si el usuario está logueado
    if not st.session_state.logged_in:
        show_login()
    else:
        # Mostrar panel según el rol
        user_role = st.session_state.user_data.get('rol', '')
        
        if user_role == 'admin':
            show_admin_panel()
        elif user_role == 'usuario':
            show_user_panel()
        else:
            st.error("Rol de usuario no reconocido")
            # Limpiar session state
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
