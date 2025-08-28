import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import storage
import pandas as pd
from datetime import datetime
import json
import os
import io
import urllib.parse

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

# Función para inicializar Google Cloud Storage
@st.cache_resource
def init_google_cloud_storage():
    """Inicializa la conexión con Google Cloud Storage usando las credenciales de los secrets"""
    try:
        # Obtener credenciales desde los secrets de Replit
        google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_credentials:
            st.error("No se encontraron las credenciales de Google Cloud Storage en los secrets")
            return None

        # Crear archivo temporal con las credenciales
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write(google_credentials)
            temp_creds_path = f.name

        # Configurar la variable de entorno
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path

        # Inicializar el cliente de Google Cloud Storage
        client = storage.Client()

        return client
    except Exception as e:
        st.error(f"Error al inicializar Google Cloud Storage: {str(e)}")
        return None

# Función para obtener usuarios desde Google Sheets
@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_users_data(_client):
    """Obtiene los datos de usuarios desde la hoja de Google Sheets"""
    try:
        # Abrir la hoja de cálculo
        sheet = _client.open("sistema_evidencias")

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
        sheet = _client.open("sistema_evidencias")

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
        sheet = client.open("sistema_evidencias")

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

# Función para subir archivo a Google Cloud Storage
def upload_to_gcs(file, folder_name, gcs_client, dimension=None, criterio=None, bucket_name="mi-bucket-proyecto"):
    """Sube un archivo a Google Cloud Storage y retorna la URL pública"""
    try:
        # Crear la ruta del archivo con estructura de carpetas
        # Limpiar nombres para que sean compatibles con GCS
        clean_dimension = dimension.replace("/", "-").replace("\\", "-") if dimension else ""
        clean_criterio = criterio.replace("/", "-").replace("\\", "-") if criterio else ""
        clean_folder = folder_name.replace("/", "-").replace("\\", "-")

        # Crear la ruta: programa/dimension/criterio/archivo
        if dimension and criterio:
            file_path = f"{clean_folder}/{clean_dimension}/{clean_criterio}/{file.name}"
        else:
            file_path = f"{clean_folder}/{file.name}"

        # Obtener el bucket
        bucket = gcs_client.bucket(bucket_name)

        # Crear el blob (archivo en GCS)
        blob = bucket.blob(file_path)

        # Subir el archivo
        file.seek(0)  # Resetear el puntero del archivo
        blob.upload_from_file(file, content_type=file.type)

        # Intentar hacer el archivo público, si no se puede, usar URL autenticada
        try:
            blob.make_public()
            return blob.public_url
        except Exception as e:
            # Si no se puede hacer público, generar URL firmada válida por 7 días
            from datetime import timedelta
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=7),
                method="GET"
            )
            return url

    except Exception as e:
        st.error(f"Error al subir archivo a Google Cloud Storage: {str(e)}")
        return None

# Función de autenticación
def authenticate_user(email, password, users_df):
    """Autentica al usuario con email y contraseña y retorna sus datos"""
    if users_df.empty:
        return None

    user_data = users_df[users_df['correo'].str.lower() == email.lower()]

    if not user_data.empty:
        # Verificar contraseña (si no existe columna contraseña, permitir acceso)
        stored_password = user_data.iloc[0].get('contraseña', password)
        if stored_password == password:
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
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        submit_button = st.form_submit_button("Iniciar Sesión")

        if submit_button:
            if not email or not password:
                st.error("Por favor ingrese su correo electrónico y contraseña")
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
            user_data = authenticate_user(email, password, users_df)

            if user_data:
                st.session_state.user_data = user_data
                st.session_state.logged_in = True
                st.success(f"¡Bienvenido! Ingresando como {user_data['rol']}")
                st.rerun()
            else:
                st.error("Correo o contraseña incorrectos")

# Función para cambiar contraseña
def change_password_page():
    """Página para cambiar contraseña"""
    st.title("🔐 Cambiar Contraseña")

    with st.form("change_password_form"):
        current_password = st.text_input("Contraseña actual", type="password")
        new_password = st.text_input("Nueva contraseña", type="password")
        confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
        submit_button = st.form_submit_button("Cambiar Contraseña")

        if submit_button:
            if not all([current_password, new_password, confirm_password]):
                st.error("Por favor complete todos los campos")
                return

            if new_password != confirm_password:
                st.error("Las contraseñas nuevas no coinciden")
                return

            if len(new_password) < 6:
                st.error("La nueva contraseña debe tener al menos 6 caracteres")
                return

            # Inicializar Google Sheets
            client = init_google_sheets()
            if not client:
                st.error("Error al conectar con la base de datos")
                return

            # Obtener datos de usuarios
            users_df = get_users_data(client)
            if users_df.empty:
                st.error("No se pudieron cargar los datos de usuarios")
                return

            # Verificar contraseña actual
            user_email = st.session_state.user_data['correo']
            user_data = authenticate_user(user_email, current_password, users_df)

            if not user_data:
                st.error("Contraseña actual incorrecta")
                return

            # Actualizar contraseña en Google Sheets
            try:
                worksheet = client.open("sistema_evidencias").worksheet("usuarios")
                all_records = worksheet.get_all_records()

                # Encontrar la fila del usuario
                for i, record in enumerate(all_records):
                    if str(record['correo']).lower() == user_email.lower():
                        row_num = i + 2  # +2 porque las filas empiezan en 1 y hay encabezado

                        # Verificar si existe la columna contraseña
                        headers = worksheet.row_values(1)
                        if 'contraseña' not in headers:
                            # Agregar columna contraseña si no existe
                            worksheet.update_cell(1, len(headers) + 1, 'contraseña')
                            col_num = len(headers) + 1
                        else:
                            col_num = headers.index('contraseña') + 1

                        # Actualizar contraseña
                        worksheet.update_cell(row_num, col_num, new_password)
                        st.success("✅ Contraseña actualizada exitosamente")

                        # Limpiar cache para recargar datos
                        get_users_data.clear()
                        return

                st.error("Usuario no encontrado")

            except Exception as e:
                st.error(f"Error al actualizar contraseña: {str(e)}")

# Función mejorada para eliminar archivo de Google Cloud Storage
def delete_from_gcs(file_url, gcs_client, bucket_name="mi-bucket-proyecto"):
    """Elimina un archivo de Google Cloud Storage usando su URL"""
    try:
        if not file_url:
            st.warning("URL del archivo vacía")
            return False

        # Múltiples formas de extraer el path del archivo
        file_path = None

        # Método 1: URL de la API de Storage
        if "/storage/v1/b/" in file_url:
            try:
                parts = file_url.split("/storage/v1/b/")[1].split("/o/")
                file_path = parts[1].split("?")[0]
                file_path = urllib.parse.unquote(file_path)
            except:
                pass

        # Método 2: URL pública con nombre del bucket
        if not file_path and bucket_name in file_url:
            try:
                file_path = file_url.split(f"{bucket_name}/")[1].split("?")[0]
                file_path = urllib.parse.unquote(file_path)
            except:
                pass

        # Método 3: URL googleapis
        if not file_path and "googleapis.com" in file_url:
            try:
                # Para URLs como https://storage.googleapis.com/bucket/path
                if f"storage.googleapis.com/{bucket_name}/" in file_url:
                    file_path = file_url.split(f"storage.googleapis.com/{bucket_name}/")[1].split("?")[0]
                    file_path = urllib.parse.unquote(file_path)
            except:
                pass

        if not file_path:
            st.error(f"No se pudo determinar la ruta del archivo desde la URL: {file_url}")
            return False

        # Obtener el bucket y eliminar el archivo
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        if blob.exists():
            blob.delete()
            st.success(f"Archivo eliminado de Google Cloud Storage: {file_path}")
            return True
        else:
            st.warning(f"El archivo no existe en Google Cloud Storage: {file_path}")
            return True  # Consideramos esto como éxito ya que el objetivo es que no exista

    except Exception as e:
        st.error(f"Error al eliminar archivo de Google Cloud Storage: {str(e)}")
        return False

# Función mejorada para eliminar evidencia de Google Sheets
def delete_evidencia(client, evidencia_data):
    """Elimina una evidencia específica de Google Sheets usando un identificador único"""
    try:
        sheet = client.open("sistema_evidencias")
        evidencias_worksheet = sheet.worksheet("evidencias")

        # Obtener todos los registros
        all_records = evidencias_worksheet.get_all_records()

        # Buscar la fila que coincida con todos los campos
        for i, record in enumerate(all_records):
            match = True
            for key, value in evidencia_data.items():
                if str(record.get(key, '')).strip() != str(value).strip():
                    match = False
                    break

            if match:
                # Eliminar la fila (i + 2 porque las filas empiezan en 1 y hay encabezado)
                evidencias_worksheet.delete_rows(i + 2)

                # Limpiar cache
                get_evidencias_data.clear()

                st.success("Evidencia eliminada de la base de datos")
                return True

        st.error("No se encontró la evidencia para eliminar en la base de datos")
        return False

    except Exception as e:
        st.error(f"Error al eliminar evidencia de la base de datos: {str(e)}")
        return False

# Función para eliminar múltiples archivos (nueva funcionalidad)
def delete_multiple_files(selected_files, client, gcs_client):
    """Elimina múltiples archivos seleccionados"""
    if not selected_files:
        st.warning("No hay archivos seleccionados para eliminar")
        return

    success_count = 0
    error_count = 0

    progress_bar = st.progress(0)
    total_files = len(selected_files)

    for i, file_data in enumerate(selected_files):
        progress_bar.progress((i + 1) / total_files)

        with st.spinner(f"Eliminando {file_data.get('nombre_archivo', 'archivo')}..."):
            # Eliminar de Google Sheets
            sheets_success = delete_evidencia(client, file_data)

            # Eliminar de Google Cloud Storage
            gcs_success = True
            if file_data.get('url_cloudinary'):
                gcs_success = delete_from_gcs(file_data['url_cloudinary'], gcs_client)

            if sheets_success and gcs_success:
                success_count += 1
            else:
                error_count += 1

    if success_count > 0:
        st.success(f"✅ {success_count} archivo(s) eliminado(s) exitosamente")

    if error_count > 0:
        st.error(f"❌ {error_count} archivo(s) no pudieron ser eliminados completamente")

    progress_bar.empty()

# Función para mostrar panel de usuario con eliminación mejorada
def show_user_panel():
    """Muestra el panel para usuarios regulares con funcionalidad de eliminación mejorada"""
    user_data = st.session_state.user_data

    st.title(f"📋 Panel de Usuario - {user_data['programa']}")
    st.write(f"Bienvenido, {user_data['correo']}")

    # Sidebar con información del usuario
    with st.sidebar:
        st.header("Información del Usuario")
        st.write(f"**Correo:** {user_data['correo']}")
        st.write(f"**Programa:** {user_data['programa']}")
        st.write(f"**Rol:** {user_data['rol']}")

        if st.button("🔐 Cambiar Contraseña"):
            st.session_state.show_change_password = True
            st.rerun()

        if st.button("Cerrar Sesión"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    # Verificar si se debe mostrar la página de cambio de contraseña
    if st.session_state.get('show_change_password', False):
        change_password_page()

        if st.button("⬅️ Volver al Panel"):
            st.session_state.show_change_password = False
            st.rerun()
        return

    # Inicializar servicios
    client = init_google_sheets()
    gcs_client = init_google_cloud_storage()

    if not client or not gcs_client:
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
                        # Subir a Google Cloud Storage
                        url_drive = upload_to_gcs(
                            uploaded_file, 
                            user_data['programa'], 
                            gcs_client,
                            dimension_seleccionada,
                            criterio_seleccionado
                        )

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

                    # Opción de eliminación múltiple
                    st.subheader("🗑️ Eliminación de Archivos")

                    # Checkbox para seleccionar modo de eliminación múltiple
                    multiple_delete_mode = st.checkbox("Modo eliminación múltiple")

                    if multiple_delete_mode:
                        st.info("Seleccione los archivos que desea eliminar y use el botón 'Eliminar Seleccionados'")

                        # Crear lista de archivos para selección múltiple
                        files_to_select = []
                        selected_files = []

                        for idx, row in df_mostrar.iterrows():
                            file_info = {
                                'nombre_archivo': row.get('nombre_archivo', 'Sin nombre'),
                                'criterio': row.get('criterio', ''),
                                'fecha_hora': row.get('fecha_hora', ''),
                                'programa': row.get('programa', user_data['programa']),
                                'subido_por': row.get('subido_por', user_data['correo']),
                                'url_cloudinary': row.get('url_cloudinary', ''),
                                'dimension': row.get('dimension', '')
                            }

                            file_display_name = f"{file_info['nombre_archivo']} - {file_info['criterio']} ({file_info['fecha_hora']})"

                            if st.checkbox(file_display_name, key=f"select_file_{idx}"):
                                selected_files.append(file_info)

                        # Botón para eliminar archivos seleccionados
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("🗑️ Eliminar Seleccionados", type="primary", disabled=len(selected_files) == 0):
                                if selected_files:
                                    st.session_state['confirm_delete_multiple'] = selected_files
                                    st.rerun()

                        with col2:
                            if selected_files:
                                st.info(f"{len(selected_files)} archivo(s) seleccionado(s)")

                        # Confirmación de eliminación múltiple
                        if st.session_state.get('confirm_delete_multiple'):
                            files_to_delete = st.session_state['confirm_delete_multiple']
                            st.error(f"¿Estás seguro de eliminar {len(files_to_delete)} archivo(s)?")

                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("✅ Sí, eliminar todos", key="confirm_multiple_yes"):
                                    delete_multiple_files(files_to_delete, client, gcs_client)
                                    del st.session_state['confirm_delete_multiple']
                                    st.rerun()

                            with col_no:
                                if st.button("❌ Cancelar", key="confirm_multiple_no"):
                                    del st.session_state['confirm_delete_multiple']
                                    st.rerun()

                    # Mostrar evidencias agrupadas por criterio
                    st.subheader("📋 Evidencias por Criterio")

                    if len(df_mostrar) > 0:
                        for criterio in sorted(pd.Series(df_mostrar['criterio']).unique()):
                            criterio_evidencias = df_mostrar[df_mostrar['criterio'] == criterio]

                            # Mantener estado del expander usando session_state
                            expander_key = f"expander_{criterio.replace(' ', '_').replace('.', '_')}"
                            if expander_key not in st.session_state:
                                st.session_state[expander_key] = False

                            # Verificar si hay alguna confirmación pendiente para este criterio
                            has_pending_confirmation = False
                            for idx, row in criterio_evidencias.iterrows():
                                file_name = row.get('nombre_archivo', 'archivo')
                                unique_key = f"{row.get('programa', user_data['programa'])}_{row.get('subido_por', user_data['correo'])}_{file_name}_{idx}".replace(" ", "_").replace("/", "_").replace(".", "_")
                                if st.session_state.get(f'confirm_delete_{unique_key}'):
                                    has_pending_confirmation = True
                                    st.session_state[expander_key] = True
                                    break

                            with st.expander(f"{criterio} ({len(criterio_evidencias)} archivo(s))", expanded=st.session_state[expander_key]):
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

                                # Solo mostrar botones individuales si no está en modo eliminación múltiple
                                if not multiple_delete_mode:
                                    st.subheader("🔧 Acciones Individuales")

                                    for idx, row in criterio_evidencias.iterrows():
                                        file_name = row.get('nombre_archivo', 'archivo')
                                        file_url = row.get('url_cloudinary', '')

                                        # Crear datos completos para eliminación
                                        evidencia_data = {
                                            'programa': row.get('programa', user_data['programa']),
                                            'subido_por': row.get('subido_por', user_data['correo']),
                                            'url_cloudinary': file_url,
                                            'criterio': row.get('criterio', ''),
                                            'dimension': row.get('dimension', ''),
                                            'nombre_archivo': file_name
                                        }

                                        # Crear key único basado en el contenido del archivo
                                        unique_key = f"{evidencia_data['programa']}_{evidencia_data['subido_por']}_{file_name}_{idx}".replace(" ", "_").replace("/", "_").replace(".", "_")

                                        # Contenedor para cada archivo
                                        file_container = st.container()

                                        with file_container:
                                            col_file, col_delete = st.columns([3, 1])

                                            with col_file:
                                                st.write(f"📄 {file_name}")

                                            with col_delete:
                                                if st.button(f"🗑️", key=f"delete_{unique_key}", help="Eliminar archivo"):
                                                    st.session_state[f'confirm_delete_{unique_key}'] = evidencia_data
                                                    # Mantener el expander abierto
                                                    st.session_state[expander_key] = True
                                                    st.rerun()

                                            # Confirmación de eliminación individual
                                            if st.session_state.get(f'confirm_delete_{unique_key}'):
                                                delete_info = st.session_state[f'confirm_delete_{unique_key}']

                                                st.warning(f"¿Estás seguro de eliminar **{delete_info['nombre_archivo']}**?")
                                                st.info("Esta acción no se puede deshacer.")

                                                col_yes, col_no = st.columns(2)

                                                with col_yes:
                                                    if st.button("✅ Sí, eliminar", key=f"confirm_yes_{unique_key}", type="primary"):
                                                        with st.spinner(f"Eliminando {delete_info['nombre_archivo']}..."):
                                                            # Eliminar de Google Sheets
                                                            success_sheets = delete_evidencia(client, delete_info)

                                                            # Eliminar de GCS
                                                            success_gcs = True
                                                            if delete_info['url_cloudinary']:
                                                                success_gcs = delete_from_gcs(delete_info['url_cloudinary'], gcs_client)

                                                            if success_sheets and success_gcs:
                                                                st.success(f"✅ {delete_info['nombre_archivo']} eliminado exitosamente")
                                                                # Mantener expander abierto después de eliminación exitosa
                                                                st.session_state[expander_key] = True
                                                            elif success_sheets and not success_gcs:
                                                                st.warning("⚠️ Archivo eliminado de la base de datos, pero no del almacenamiento")
                                                                st.session_state[expander_key] = True
                                                            else:
                                                                st.error("❌ Error al eliminar el archivo")
                                                                st.session_state[expander_key] = True

                                                            # Limpiar confirmación
                                                            del st.session_state[f'confirm_delete_{unique_key}']
                                                            st.rerun()

                                                with col_no:
                                                    if st.button("❌ Cancelar", key=f"confirm_no_{unique_key}"):
                                                        del st.session_state[f'confirm_delete_{unique_key}']
                                                        # Mantener expander abierto al cancelar
                                                        st.session_state[expander_key] = True
                                                        st.rerun()

                                                # Separador visual
                                                st.divider()
                    else:
                        st.info("No hay evidencias para la dimensión seleccionada.")

                else:
                    # Formato antiguo - mostrar tabla simple con funcionalidad básica de eliminación
                    st.warning("Algunas evidencias están en formato anterior. Funcionalidad de eliminación limitada.")
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

                    # Botones de eliminación para formato antiguo
                    st.subheader("🔧 Eliminar Archivos")
                    for idx, row in user_evidencias.iterrows():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📄 Archivo del {row.get('fecha_hora', 'fecha desconocida')}")
                        with col2:
                            if st.button(f"🗑️", key=f"delete_old_{idx}"):
                                evidencia_data = {
                                    'programa': row.get('programa', user_data['programa']),
                                    'subido_por': row.get('subido_por', user_data['correo']),
                                    'url_cloudinary': row.get('url_cloudinary', ''),
                                    'fecha_hora': row.get('fecha_hora', '')
                                }
                                st.session_state[f'confirm_delete_old_{idx}'] = evidencia_data
                                st.rerun()

                        # Confirmación para formato antiguo
                        if st.session_state.get(f'confirm_delete_old_{idx}'):
                            delete_info = st.session_state[f'confirm_delete_old_{idx}']
                            st.warning(f"¿Eliminar archivo del {delete_info.get('fecha_hora', 'fecha desconocida')}?")
                            col_yes, col_no = st.columns(2)

                            with col_yes:
                                if st.button("✅ Sí", key=f"confirm_old_yes_{idx}"):
                                    with st.spinner("Eliminando archivo..."):
                                        success_sheets = delete_evidencia(client, delete_info)
                                        success_gcs = True

                                        if delete_info.get('url_cloudinary'):
                                            success_gcs = delete_from_gcs(delete_info['url_cloudinary'], gcs_client)

                                        if success_sheets and success_gcs:
                                            st.success("✅ Archivo eliminado exitosamente")
                                        else:
                                            st.error("❌ Error al eliminar el archivo")

                                        del st.session_state[f'confirm_delete_old_{idx}']
                                        st.rerun()

                            with col_no:
                                if st.button("❌ No", key=f"confirm_old_no_{idx}"):
                                    del st.session_state[f'confirm_delete_old_{idx}']
                                    st.rerun()
            else:
                st.info("No hay evidencias registradas para tu programa aún.")
        else:
            st.info("No se pudieron cargar las evidencias.")

# Función para mostrar panel de admin con eliminación mejorada
def show_admin_panel():
    """Muestra el panel para administradores con funcionalidad de eliminación"""
    user_data = st.session_state.user_data

    st.title("👨‍💼 Panel de Administrador")
    st.write(f"Bienvenido, {user_data['correo']}")

    # Sidebar con información del usuario
    with st.sidebar:
        st.header("Información del Usuario")
        st.write(f"**Correo:** {user_data['correo']}")
        st.write(f"**Programa:** {user_data['programa']}")
        st.write(f"**Rol:** {user_data['rol']}")

        if st.button("🔐 Cambiar Contraseña", key="admin_change_password"):
            st.session_state.show_change_password = True
            st.rerun()

        if st.button("Cerrar Sesión"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    # Verificar si se debe mostrar la página de cambio de contraseña
    if st.session_state.get('show_change_password', False):
        change_password_page()

        if st.button("⬅️ Volver al Panel", key="admin_back_to_panel"):
            st.session_state.show_change_password = False
            st.rerun()
        return

    # Inicializar servicios
    client = init_google_sheets()
    gcs_client = init_google_cloud_storage()

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

    # Pestañas para organizar funcionalidades de admin
    tab1, tab2 = st.tabs(["📋 Visualizar Evidencias", "🗑️ Gestión de Archivos"])

    with tab1:
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

    with tab2:
        st.header("🗑️ Gestión de Archivos (Solo Administradores)")
        st.warning("⚠️ Esta sección permite eliminar archivos de cualquier programa. Use con precaución.")

        if gcs_client:
            # Mostrar funcionalidad de eliminación para administradores
            admin_delete_mode = st.checkbox("Activar modo eliminación de administrador")

            if admin_delete_mode:
                st.error("🔴 MODO ELIMINACIÓN ACTIVO - Los cambios son irreversibles")

                # Selector de evidencias para eliminar
                if len(evidencias_df) > 0:
                    # Crear lista de archivos para selección múltiple por administrador
                    selected_admin_files = []

                    st.subheader("Seleccionar archivos para eliminar:")

                    # Agrupar por programa para mejor organización
                    for programa in sorted(evidencias_df['programa'].unique()):
                        with st.expander(f"📁 {programa}"):
                            programa_files = evidencias_df[evidencias_df['programa'] == programa]

                            for idx, row in programa_files.iterrows():
                                file_info = {
                                    'programa': row.get('programa', ''),
                                    'subido_por': row.get('subido_por', ''),
                                    'url_cloudinary': row.get('url_cloudinary', ''),
                                    'fecha_hora': row.get('fecha_hora', ''),
                                    'criterio': row.get('criterio', ''),
                                    'dimension': row.get('dimension', ''),
                                    'nombre_archivo': row.get('nombre_archivo', 'Sin nombre')
                                }

                                file_display = f"{file_info['nombre_archivo']} - {file_info['subido_por']} ({file_info['fecha_hora']})"

                                if st.checkbox(file_display, key=f"admin_select_{idx}"):
                                    selected_admin_files.append(file_info)

                    # Botón de eliminación para administrador
                    if selected_admin_files:
                        st.error(f"⚠️ {len(selected_admin_files)} archivo(s) seleccionado(s) para eliminación")

                        if st.button("🗑️ ELIMINAR ARCHIVOS SELECCIONADOS", type="primary"):
                            st.session_state['admin_confirm_delete'] = selected_admin_files
                            st.rerun()

                        # Confirmación de eliminación de administrador
                        if st.session_state.get('admin_confirm_delete'):
                            files_to_delete = st.session_state['admin_confirm_delete']
                            st.error(f"🚨 CONFIRMACIÓN REQUERIDA: ¿Eliminar {len(files_to_delete)} archivo(s)?")
                            st.write("Esta acción NO se puede deshacer.")

                            col_confirm, col_cancel = st.columns(2)

                            with col_confirm:
                                if st.button("✅ CONFIRMAR ELIMINACIÓN", key="admin_confirm_yes"):
                                    delete_multiple_files(files_to_delete, client, gcs_client)
                                    del st.session_state['admin_confirm_delete']
                                    st.rerun()

                            with col_cancel:
                                if st.button("❌ CANCELAR", key="admin_confirm_no"):
                                    del st.session_state['admin_confirm_delete']
                                    st.rerun()
                else:
                    st.info("No hay archivos para gestionar")
        else:
            st.error("Error al conectar con el sistema de almacenamiento")

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