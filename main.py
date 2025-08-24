import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader
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

# Función para inicializar Cloudinary
def init_cloudinary():
    """Inicializa Cloudinary usando las credenciales de los secrets"""
    try:
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        api_key = os.getenv("CLOUDINARY_API_KEY")
        api_secret = os.getenv("CLOUDINARY_API_SECRET")
        
        if not all([cloud_name, api_key, api_secret]):
            st.error("No se encontraron todas las credenciales de Cloudinary en los secrets")
            return False
            
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        return True
    except Exception as e:
        st.error(f"Error al inicializar Cloudinary: {str(e)}")
        return False

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

# Función para subir archivo a Cloudinary
def upload_to_cloudinary(file, folder_name):
    """Sube un archivo a Cloudinary y retorna la URL"""
    try:
        # Subir archivo
        result = cloudinary.uploader.upload(
            file,
            folder=f"evidencias/{folder_name}",
            resource_type="auto"
        )
        
        return result.get("secure_url")
    except Exception as e:
        st.error(f"Error al subir archivo a Cloudinary: {str(e)}")
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
    cloudinary_ok = init_cloudinary()
    
    if not client or not cloudinary_ok:
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
                    # Subir a Cloudinary
                    url_cloudinary = upload_to_cloudinary(uploaded_file, user_data['programa'])
                    
                    if url_cloudinary:
                        # Registrar en Google Sheets
                        success = add_evidencia(
                            client, 
                            user_data['programa'], 
                            user_data['correo'], 
                            url_cloudinary
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
        fecha_desde = st.date_input("Desde", value=today.date() - pd.Timedelta(days=30))
        fecha_hasta = st.date_input("Hasta", value=today.date())
    
    # Aplicar filtros
    df_filtrado = evidencias_df.copy()
    
    if programa_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['programa'] == programa_seleccionado]
    
    # Filtrar por fecha
    if not df_filtrado.empty:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha_hora'].dt.date >= fecha_desde) & 
            (df_filtrado['fecha_hora'].dt.date <= fecha_hasta)
        ]
    
    # Mostrar resultados
    st.header("📋 Evidencias Filtradas")
    
    if not df_filtrado.empty:
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
            programa_counts = df_filtrado['programa'].value_counts()
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
