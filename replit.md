# College CMS - Replit Project Documentation

## Overview

This is a comprehensive College Content Management System (CMS) built with Flask, designed to manage faculty workloads, subject assignments, and timetable scheduling. The system supports role-based access control for administrators, faculty, and students, with capabilities for Excel data import and comprehensive reporting.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **UI Framework**: Bootstrap 5 with custom CSS
- **JavaScript**: Vanilla JavaScript for interactive features
- **Icons**: Font Awesome for consistent iconography
- **Charts**: Chart.js for data visualization

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (configured via environment variables)
- **Authentication**: Flask-Login with session management
- **Forms**: Flask-WTF for form handling and validation
- **File Upload**: Werkzeug for secure file handling

### Application Structure
```
├── app.py              # Main Flask application setup
├── main.py             # Application entry point
├── models.py           # Database models
├── forms.py            # Form definitions
├── routes.py           # Application routes
├── utils.py            # Utility functions
├── templates/          # HTML templates
├── static/            # Static assets (CSS, JS)
└── uploads/           # File upload directory
```

## Key Components

### 1. User Management System
- **Role-based access**: Admin, Faculty, Student roles
- **Authentication**: Secure login/logout with password hashing
- **User profiles**: Complete faculty information including designation and department

### 2. Faculty Management
- Faculty CRUD operations
- Workload tracking based on designation:
  - Assistant Professor: 18 hours limit
  - Associate Professor: 16 hours limit  
  - Professor: 14 hours limit
- Department and employee ID management

### 3. Subject Management
- Subject creation with detailed information
- Lecture, tutorial, and practical hour allocation
- Subject type classification (Regular/Elective)
- Semester and department association

### 4. Assignment System
- Faculty-subject assignment management
- Workload calculation and validation
- Division-based assignments
- Assignment tracking and reporting

### 5. Timetable Management
- Class schedule creation and management
- Faculty availability tracking
- Conflict detection and resolution
- Semester and division-based filtering

### 6. Excel Import System
- Multi-format support (XLSX, XLS, CSV)
- Dynamic column mapping
- Data validation and error handling
- Import history and tracking

## Data Flow

### 1. Authentication Flow
1. User login via LoginForm
2. Credentials validated against User model
3. Session created via Flask-Login
4. Role-based redirect to appropriate dashboard

### 2. Faculty Assignment Flow
1. Admin selects faculty and subject
2. System validates workload limits
3. Assignment created with hour allocation
4. Workload automatically calculated and updated

### 3. Excel Import Flow
1. File upload and validation
2. Data preview and column mapping
3. Data processing and validation
4. Batch import with error handling
5. Import session tracking

### 4. Timetable Creation Flow
1. Subject and faculty selection
2. Time slot and day selection
3. Conflict detection with existing schedules
4. Schedule entry creation and validation

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: ORM for database operations
- **Flask-Login**: User session management
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation
- **Werkzeug**: WSGI utilities and security
- **pandas**: Excel file processing
- **openpyxl**: Excel file manipulation

### Frontend Dependencies
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization
- **jQuery**: JavaScript utilities (implicit)

### Database
- **PostgreSQL**: Primary database (configurable via DATABASE_URL)
- **SQLAlchemy**: Database abstraction layer

## Deployment Strategy

### Environment Configuration
- **SESSION_SECRET**: Flask session encryption key
- **DATABASE_URL**: PostgreSQL connection string
- **UPLOAD_FOLDER**: File upload directory path
- **MAX_CONTENT_LENGTH**: File size limit (16MB)

### Database Setup
- Automatic table creation via SQLAlchemy
- Migration support through Flask-Migrate (can be added)
- Connection pooling with automatic reconnection

### Production Considerations
- ProxyFix middleware for deployment behind reverse proxy
- Configurable logging levels
- File upload size limits
- Secure file handling with filename sanitization

### Deployment Requirements
- Python 3.8+ runtime
- PostgreSQL database
- File system access for uploads
- Environment variable configuration

## Changelog
- June 28, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.