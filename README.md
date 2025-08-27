# Sistema de Evidencias de Acreditación Universitaria

Una aplicación web desarrollada con Streamlit para la gestión de evidencias académicas basada en criterios de acreditación universitaria.

## Características

- **Autenticación segura**: Login con email y contraseña almacenados en Google Sheets
- **Gestión de roles**: Usuarios regulares y administradores con diferentes niveles de acceso
- **Organización por criterios**: Sistema de 5 dimensiones y 14 criterios de acreditación
- **Almacenamiento en la nube**: Archivos almacenados en Google Cloud Storage
- **Base de datos**: Google Sheets como base de datos para usuarios y evidencias
- **Interfaz intuitiva**: Filtros, métricas y visualizaciones

## Tecnologías utilizadas

- **Frontend**: Streamlit
- **Almacenamiento**: Google Cloud Storage
- **Base de datos**: Google Sheets API
- **Autenticación**: Google OAuth2
- **Lenguaje**: Python 3.11

## Configuración

### Variables de entorno requeridas

En Replit Secrets, configurar:

- `GOOGLE_SHEETS_CREDENTIALS`: JSON con credenciales de service account de Google Sheets
- `GOOGLE_APPLICATION_CREDENTIALS`: JSON con credenciales de Google Cloud Storage

### Estructura de Google Sheets

Crear una hoja llamada "sistema_evidencias" con dos pestañas:

#### Pestaña "usuarios"
```
correo | programa | rol | contraseña
```

#### Pestaña "evidencias"  
```
programa | subido_por | url_cloudinary | fecha_hora | criterio | dimension | nombre_archivo
```

## Instalación y ejecución

1. Instalar dependencias:
```bash
pip install streamlit gspread google-auth google-cloud-storage pandas
```

2. Configurar las credenciales de Google en los secrets

3. Ejecutar la aplicación:
```bash
streamlit run main.py --server.port 5000
```

## Funcionalidades

### Para usuarios regulares:
- Subir evidencias por criterios específicos
- Ver sus propias evidencias organizadas por dimensión/criterio
- Cambiar su contraseña
- Eliminar archivos propios

### Para administradores:
- Ver todas las evidencias del sistema
- Filtrar por programa, dimensión y criterio  
- Análisis y métricas globales
- Gestión completa de evidencias

## Estructura del proyecto

```
├── main.py              # Aplicación principal
├── .streamlit/
│   └── config.toml      # Configuración de Streamlit
├── requirements.txt     # Dependencias Python
└── README.md           # Documentación
```

## Contribución

Este proyecto está diseñado para instituciones educativas que requieren un sistema de gestión de evidencias para procesos de acreditación.