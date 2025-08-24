# Overview

This is a university accreditation evidence management system built with Streamlit. The application allows users to upload, store, and manage academic evidence files based on their role and program affiliation. It features role-based access control where regular users can only manage evidence for their own program, while administrators have access to all programs with filtering capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit-based web application with a single-page architecture
- **Layout**: Wide layout configuration for better content display
- **Session Management**: Uses `st.session_state` for maintaining user authentication across page interactions
- **UI Components**: Form-based login, file upload interface, and admin dashboard with filtering capabilities

## Backend Architecture
- **Structure**: Monolithic architecture contained in a single `main.py` file
- **Authentication System**: Email-based login validation against Google Sheets user database
- **Role-Based Access Control**: Two-tier system with "usuario" (user) and "admin" roles implementing row-level security
- **File Processing**: Direct file upload handling with metadata extraction

## Data Storage Solutions
- **Primary Database**: Google Sheets acting as the main data store with two worksheets:
  - "usuarios" worksheet: Contains user data (correo, programa, rol)
  - "evidencias" worksheet: Stores evidence records (programa, subido_por, url_cloudinary, fecha_hora)
- **File Storage**: Cloudinary cloud service for storing uploaded files (PDFs, images, etc.)
- **Caching**: Streamlit's `@st.cache_resource` decorator for optimizing Google Sheets connections

## Authentication and Authorization
- **Authentication Method**: Email-based validation against Google Sheets user database
- **Session Management**: Streamlit session state for maintaining login status
- **Authorization Logic**:
  - Regular users: Can only view/upload evidence for their assigned program
  - Admin users: Full access to all programs with filtering capabilities
- **Security**: Row-level security implementation based on user program affiliation

# External Dependencies

## Cloud Services
- **Google Sheets API**: Primary database for user management and evidence tracking
- **Google Drive API**: Required for Google Sheets access permissions
- **Cloudinary**: Cloud-based file storage and management service

## Authentication Services
- **Google OAuth2**: Service account authentication for Google Sheets access
- **Google Service Account**: Credential management through JSON key files

## API Integrations
- **gspread**: Python library for Google Sheets API interaction
- **google-auth**: OAuth2 authentication library for Google services
- **cloudinary**: Python SDK for Cloudinary file upload and management

## Configuration Management
- **Replit Secrets**: Environment variable storage for sensitive credentials
- **Environment Variables**:
  - `GOOGLE_SHEETS_CREDENTIALS`: JSON service account credentials
  - Cloudinary configuration (cloud_name, api_key, api_secret)