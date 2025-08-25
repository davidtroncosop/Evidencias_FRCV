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
def add_evidencia(client, programa, subido_por, url_cloudinary):
    """Agrega una nueva evidencia a la hoja de Google Sheets"""
    try:
        # Abrir la hoja de cálculo
        sheet = client.open("BaseDeDatosAppReha")
        
        # Obtener la pestaña de evidencias
        evidencias_worksheet = sheet.worksheet("evidencias")
        
        # Crear nueva fila con los datos
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [programa, subido_por, url_cloudinary, fecha_hora]
        
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
        # Crear o encontrar la carpeta
        folder_id = create_or_get_folder(drive_service, f"evidencias_{folder_name}")
        
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
        st.header("Subir Nueva Evidencia")
        
        uploaded_file = st.file_uploader(
            "Seleccione el archivo de evidencia",
            type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'],
            help="Formatos permitidos: PDF, imágenes, documentos de Office"
        )
        
        if uploaded_file is not None:
            st.write(f"**Archivo seleccionado:** {uploaded_file.name}")
            st.write(f"**Tamaño:** {uploaded_file.size / 1024:.2f} KB")
            
            if st.button("Subir Evidencia"):
                with st.spinner("Subiendo archivo..."):
                    # Subir a Google Drive
                    url_drive = upload_to_google_drive(uploaded_file, user_data['programa'], drive_service)
                    
                    if url_drive:
                        # Registrar en Google Sheets
                        success = add_evidencia(
                            client, 
                            user_data['programa'], 
                            user_data['correo'], 
                            url_drive
                        )
                        
                        if success:
                            st.success("✅ Evidencia subida exitosamente!")
                            st.balloons()
                            # Limpiar cache para mostrar datos actualizados
                            st.cache_data.clear()
                        else:
                            st.error("❌ Error al registrar la evidencia en la base de datos")
                    else:
                        st.error("❌ Error al subir el archivo")
    
    with tab2:
        st.header("Mis Evidencias")
        
        # Obtener evidencias del usuario
        evidencias_df = get_evidencias_data(client)
        
        if not evidencias_df.empty:
            # Filtrar por programa del usuario
            user_evidencias = evidencias_df[evidencias_df['programa'] == user_data['programa']]
            
            if not user_evidencias.empty:
                # Mostrar estadísticas
                st.metric("Total de Evidencias", len(user_evidencias))
                
                # Mostrar tabla
                st.dataframe(
                    user_evidencias[['fecha_hora', 'subido_por', 'url_cloudinary']],
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtro por programa
        programas_disponibles = ['Todos'] + sorted(evidencias_df['programa'].unique().tolist())
        programa_seleccionado = st.selectbox("Filtrar por Programa", programas_disponibles)
    
    with col2:
        # Filtro por fecha
        fecha_desde = st.date_input("Desde", value=(today - pd.Timedelta(days=30)).date())
        fecha_hasta = st.date_input("Hasta", value=today.date())
    
    # Aplicar filtros
    df_filtrado = evidencias_df.copy()
    
    if programa_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['programa'] == programa_seleccionado]
    
    # Filtrar por fecha
    if not df_filtrado.empty and 'fecha_hora' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (pd.to_datetime(df_filtrado['fecha_hora']).dt.date >= fecha_desde) & 
            (pd.to_datetime(df_filtrado['fecha_hora']).dt.date <= fecha_hasta)
        ]
    
    # Mostrar resultados
    st.header("📋 Evidencias Filtradas")
    
    if len(df_filtrado) > 0:
        st.write(f"Mostrando {len(df_filtrado)} evidencias")
        
        # Tabla con todas las evidencias
        st.dataframe(
            df_filtrado[['programa', 'subido_por', 'fecha_hora', 'url_cloudinary']],
            column_config={
                'programa': 'Programa',
                'subido_por': 'Subido por',
                'fecha_hora': 'Fecha y Hora',
                'url_cloudinary': st.column_config.LinkColumn(
                    'Enlace al Archivo',
                    display_text="Ver Archivo"
                )
            },
            use_container_width=True
        )
        
        # Gráfico por programa
        if len(df_filtrado) > 0:
            st.subheader("📈 Distribución por Programa")
            programa_counts = pd.Series(df_filtrado['programa']).value_counts()
            st.bar_chart(programa_counts)
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
