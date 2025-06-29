import pandas as pd
import json
import os
import re
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask import current_app
from models import User, Subject, Assignment, ImportedData, ImportedDataRow
from app import db
from sqlalchemy import text, inspect

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls', 'csv'}

def save_uploaded_file(file):
    """Save uploaded file and return the path"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Create upload directory if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(filepath)
        return filepath
    return None

def read_excel_file(filepath):
    """Read Excel file and return DataFrame"""
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        return df
    except Exception as e:
        current_app.logger.error(f"Error reading file {filepath}: {str(e)}")
        return None

def sanitize_column_name(name):
    """Convert column name to valid database column name"""
    # Remove special characters and convert to lowercase
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name).lower())
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = 'col_' + sanitized
    return sanitized or 'unnamed_column'

def get_available_db_fields(data_type):
    """Get all available database fields for a given data type"""
    fields = {
        'faculty': {
            'username': 'Username',
            'email': 'Email',
            'first_name': 'First Name', 
            'last_name': 'Last Name',
            'designation': 'Designation',
            'department': 'Department',
            'employee_id': 'Employee ID'
        },
        'subjects': {
            'name': 'Subject Name',
            'code': 'Subject Code',
            'lecture_hours': 'Lecture Hours',
            'tutorial_hours': 'Tutorial Hours',
            'practical_hours': 'Practical Hours',
            'subject_type': 'Subject Type',
            'semester': 'Semester',
            'department': 'Department',
            'division': 'Division'
        },
        'assignments': {
            'faculty_id': 'Faculty ID',
            'subject_id': 'Subject ID',
            'lecture_hours': 'Lecture Hours',
            'tutorial_hours': 'Tutorial Hours',
            'practical_hours': 'Practical Hours',
            'division': 'Division',
            'academic_year': 'Academic Year'
        }
    }
    return fields.get(data_type, {})

def get_column_suggestions(df, data_type):
    """Get suggested column mappings based on data type with smart matching"""
    columns = df.columns.tolist()
    available_fields = get_available_db_fields(data_type)
    
    suggestions = {}
    
    # Smart matching patterns
    patterns = {
        'faculty': {
            'first_name': ['first', 'fname', 'firstname', 'given', 'name'],
            'last_name': ['last', 'lname', 'lastname', 'surname', 'family'],
            'email': ['email', 'mail', 'e_mail', 'email_id'],
            'username': ['username', 'user', 'login', 'id'],
            'designation': ['designation', 'position', 'rank', 'title', 'post'],
            'department': ['department', 'dept', 'division', 'branch'],
            'employee_id': ['employee_id', 'emp_id', 'staff_id', 'id', 'number']
        },
        'subjects': {
            'name': ['name', 'subject_name', 'title', 'subject', 'course'],
            'code': ['code', 'subject_code', 'course_code', 'id'],
            'lecture_hours': ['lecture', 'lectures', 'lec_hours', 'theory'],
            'tutorial_hours': ['tutorial', 'tutorials', 'tut_hours', 'practice'],
            'practical_hours': ['practical', 'practicals', 'lab', 'lab_hours'],
            'subject_type': ['type', 'subject_type', 'category'],
            'semester': ['semester', 'sem', 'level', 'year'],
            'department': ['department', 'dept', 'branch', 'division'],
            'division': ['division', 'div', 'section', 'batch']
        },
        'assignments': {
            'faculty_id': ['faculty_id', 'teacher_id', 'instructor_id'],
            'subject_id': ['subject_id', 'course_id'],
            'lecture_hours': ['lecture', 'lectures', 'lec_hours', 'theory'],
            'tutorial_hours': ['tutorial', 'tutorials', 'tut_hours', 'practice'],
            'practical_hours': ['practical', 'practicals', 'lab', 'lab_hours'],
            'division': ['division', 'div', 'section', 'batch'],
            'academic_year': ['academic_year', 'year', 'session']
        }
    }
    
    # Match columns to database fields
    for col in columns:
        col_lower = col.lower().strip()
        best_match = None
        best_score = 0
        
        pattern_set = patterns.get(data_type, {})
        for db_field, keywords in pattern_set.items():
            for keyword in keywords:
                if keyword in col_lower or col_lower in keyword:
                    score = len(keyword) if keyword in col_lower else len(col_lower)
                    if score > best_score:
                        best_match = db_field
                        best_score = score
        
        suggestions[col] = best_match
    
    return suggestions

def infer_data_type(series):
    """Infer the data type of a pandas series"""
    # Remove null values for analysis
    clean_series = series.dropna()
    if len(clean_series) == 0:
        return 'TEXT'
    
    # Try to convert to numeric
    try:
        pd.to_numeric(clean_series)
        # Check if all values are integers
        if all(float(x).is_integer() for x in clean_series if pd.notnull(x)):
            return 'INTEGER'
        else:
            return 'REAL'
    except:
        pass
    
    # Check for boolean values
    unique_values = set(str(x).lower() for x in clean_series.unique())
    if unique_values.issubset({'true', 'false', '1', '0', 'yes', 'no'}):
        return 'BOOLEAN'
    
    return 'TEXT'

def create_missing_columns_helper(table_name, columns_to_add):
    """Dynamically add missing columns to database table"""
    try:
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                sql_type = {
                    'TEXT': 'VARCHAR(255)',
                    'INTEGER': 'INTEGER',
                    'REAL': 'REAL',
                    'BOOLEAN': 'BOOLEAN'
                }.get(col_type, 'VARCHAR(255)')
                
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sql_type}"
                db.session.execute(text(alter_sql))
                current_app.logger.info(f"Added column {col_name} to table {table_name}")
        
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"Error adding columns to {table_name}: {str(e)}")
        db.session.rollback()
        return False

def process_imported_data_universal(df, mapping, data_type, filename, skip_validation=False, create_missing_columns=True):
    """Universal process imported data with dynamic column creation and error tolerance"""
    # Validate and prepare mapping
    cleaned_mapping = {}
    columns_to_create = {}
    
    for excel_col, db_field in mapping.items():
        if db_field and db_field != 'skip' and excel_col in df.columns:
            # Sanitize database field name
            clean_field = sanitize_column_name(db_field) if db_field.startswith('custom_') else db_field
            cleaned_mapping[excel_col] = clean_field
            
            # Check if this is a custom field that needs creation
            if db_field.startswith('custom_'):
                columns_to_create[clean_field] = infer_data_type(df[excel_col])
    
    # Create missing columns if requested
    if create_missing_columns and columns_to_create:
        table_name = {'faculty': 'user', 'subjects': 'subject', 'assignments': 'assignment'}.get(data_type)
        if table_name:
            create_missing_columns_helper(table_name, columns_to_create)
    
    # Create import session
    import_session = ImportedData()
    import_session.filename = filename
    import_session.data_type = data_type
    import_session.total_rows = len(df)
    import_session.successful_rows = 0
    import_session.failed_rows = 0
    import_session.mapping_config = json.dumps(cleaned_mapping)
    
    try:
        db.session.add(import_session)
        db.session.commit()
        
        successful_rows = 0
        failed_rows = 0
        
        for index, row in df.iterrows():
            try:
                # Process row based on data type
                if data_type == 'faculty':
                    success = import_faculty_row_universal(row, cleaned_mapping, skip_validation)
                elif data_type == 'subjects':
                    success = import_subject_row_universal(row, cleaned_mapping, skip_validation)
                elif data_type == 'assignments':
                    success = import_assignment_row_universal(row, cleaned_mapping, skip_validation)
                else:
                    success = False
                
                if success:
                    successful_rows += 1
                    status = 'success'
                    error_msg = None
                else:
                    failed_rows += 1
                    status = 'failed'
                    error_msg = 'Import validation failed'
                
            except Exception as e:
                failed_rows += 1
                status = 'failed'
                error_msg = str(e)
                current_app.logger.error(f"Error importing row {index}: {str(e)}")
                if not skip_validation:
                    db.session.rollback()
            
            # Log row result
            row_log = ImportedDataRow()
            row_log.import_id = import_session.id
            row_log.row_data = json.dumps(row.to_dict(), default=str)
            row_log.status = status
            row_log.error_message = error_msg
            db.session.add(row_log)
        
        # Update import session statistics
        import_session.successful_rows = successful_rows
        import_session.failed_rows = failed_rows
        db.session.commit()
        
        return import_session
        
    except Exception as e:
        current_app.logger.error(f"Error during import: {str(e)}")
        db.session.rollback()
        return None

def import_faculty_row_universal(row, mapping, skip_validation=False):
    """Import faculty row with universal mapping and error tolerance"""
    try:
        # Extract mapped values with NaN filtering
        data = {}
        for excel_col, db_field in mapping.items():
            value = row.get(excel_col)
            if value is not None and pd.notna(value) and str(value).strip() and str(value).lower() != 'nan':
                data[db_field] = str(value).strip()
        
        # Required fields with fallbacks
        username = data.get('username') or data.get('email', '').split('@')[0] or f"user_{row.name}"
        email = data.get('email') or f"{username}@college.edu"
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if skip_validation:
                return True  # Skip duplicate
            else:
                return False  # Fail on duplicate
        
        # Create new faculty user
        faculty = User()
        faculty.username = username
        faculty.email = email
        faculty.password_hash = generate_password_hash('default123')
        faculty.first_name = data.get('first_name', 'Unknown')
        faculty.last_name = data.get('last_name', 'User')
        faculty.role = 'faculty'
        faculty.designation = data.get('designation', 'Assistant Prof')
        faculty.department = data.get('department', 'General')
        faculty.employee_id = data.get('employee_id')
        
        db.session.add(faculty)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing faculty: {str(e)}")
        return False

def import_subject_row_universal(row, mapping, skip_validation=False):
    """Import subject row with universal mapping and error tolerance"""
    try:
        # Extract mapped values with NaN filtering
        data = {}
        for excel_col, db_field in mapping.items():
            value = row.get(excel_col)
            if value is not None and pd.notna(value) and str(value).lower() != 'nan':
                data[db_field] = value
        
        # Required fields with defaults and NaN checking
        name = data.get('name')
        if not name or pd.isna(name) or str(name).strip() == '' or str(name).lower() == 'nan':
            name = f"Subject_{row.name}"
        else:
            name = str(name).strip()
            
        code = data.get('code')
        if not code or pd.isna(code) or str(code).strip() == '' or str(code).lower() == 'nan':
            code = f"SUB{row.name:03d}"
        else:
            code = str(code).strip()
        
        # Check if subject already exists
        existing_subject = Subject.query.filter(
            (Subject.name == name) | (Subject.code == code)
        ).first()
        
        if existing_subject:
            if skip_validation:
                return True  # Skip duplicate
            else:
                return False  # Fail on duplicate
        
        # Create new subject with proper NaN handling
        subject = Subject()
        subject.name = name
        subject.code = code
        
        # Handle numeric fields with NaN checking
        def safe_int(value, default=0):
            if value is None or pd.isna(value) or str(value).lower() == 'nan':
                return default
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default
        
        subject.lecture_hours = safe_int(data.get('lecture_hours'), 0)
        subject.tutorial_hours = safe_int(data.get('tutorial_hours'), 0)
        subject.practical_hours = safe_int(data.get('practical_hours'), 0)
        subject.semester = safe_int(data.get('semester'), 1)
        
        # Handle string fields with NaN checking
        def safe_str(value, default=None):
            if value is None or pd.isna(value) or str(value).lower() == 'nan':
                return default
            return str(value).strip()
        
        subject.subject_type = safe_str(data.get('subject_type'), 'Regular')
        subject.department = safe_str(data.get('department'), 'General')
        subject.division = safe_str(data.get('division'), None)
        
        db.session.add(subject)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing subject: {str(e)}")
        return False

def import_assignment_row_universal(row, mapping, skip_validation=False):
    """Import assignment row with universal mapping and error tolerance"""
    try:
        # Extract mapped values with NaN filtering
        data = {}
        for excel_col, db_field in mapping.items():
            value = row.get(excel_col)
            if value is not None and pd.notna(value) and str(value).lower() != 'nan':
                data[db_field] = value
        
        # Find faculty and subject by various methods
        faculty = None
        subject = None
        
        # Find faculty
        if 'faculty_id' in data:
            faculty = User.query.filter_by(id=data['faculty_id'], role='faculty').first()
        elif 'faculty_name' in data or 'faculty_email' in data:
            faculty_name = data.get('faculty_name', '')
            faculty_email = data.get('faculty_email', '')
            faculty = User.query.filter(
                User.role == 'faculty',
                (User.first_name.ilike(f"%{faculty_name}%") | 
                 User.last_name.ilike(f"%{faculty_name}%") |
                 User.email == faculty_email)
            ).first()
        
        # Find subject
        if 'subject_id' in data:
            subject = Subject.query.filter_by(id=data['subject_id']).first()
        elif 'subject_name' in data or 'subject_code' in data:
            subject_name = data.get('subject_name', '')
            subject_code = data.get('subject_code', '')
            subject = Subject.query.filter(
                (Subject.name.ilike(f"%{subject_name}%") |
                 Subject.code == subject_code)
            ).first()
        
        if not faculty or not subject:
            if skip_validation:
                return True  # Skip if references not found
            else:
                return False
        
        # Check for existing assignment
        existing_assignment = Assignment.query.filter_by(
            faculty_id=faculty.id,
            subject_id=subject.id
        ).first()
        
        if existing_assignment:
            if skip_validation:
                return True  # Skip duplicate
            else:
                return False
        
        # Create new assignment with zero-allowed values
        assignment = Assignment()
        assignment.faculty_id = faculty.id
        assignment.subject_id = subject.id
        assignment.lecture_hours = int(data.get('lecture_hours', 0) or 0)
        assignment.tutorial_hours = int(data.get('tutorial_hours', 0) or 0)
        assignment.practical_hours = int(data.get('practical_hours', 0) or 0)
        assignment.division = data.get('division')
        assignment.academic_year = data.get('academic_year', '2024-25')
        
        db.session.add(assignment)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing assignment: {str(e)}")
        return False

# Legacy functions - keeping for backward compatibility but removing duplicate process_imported_data

def old_get_column_suggestions_backup(df, data_type):
    """Backup of original function"""
    columns = df.columns.tolist()
    
    mappings = {
        'faculty': {
            'first_name': ['first_name', 'firstname', 'fname', 'name'],
            'last_name': ['last_name', 'lastname', 'lname', 'surname'],
            'email': ['email', 'email_id', 'mail'],
            'designation': ['designation', 'position', 'rank', 'title'],
            'department': ['department', 'dept', 'division'],
            'employee_id': ['employee_id', 'emp_id', 'id', 'staff_id']
        },
        'subjects': {
            'name': ['name', 'subject_name', 'subject', 'course_name'],
            'code': ['code', 'subject_code', 'course_code'],
            'lecture_hours': ['lecture_hours', 'lectures', 'l_hours'],
            'tutorial_hours': ['tutorial_hours', 'tutorials', 't_hours'],
            'practical_hours': ['practical_hours', 'practicals', 'p_hours'],
            'semester': ['semester', 'sem'],
            'department': ['department', 'dept'],
            'subject_type': ['type', 'subject_type', 'course_type']
        },
        'assignments': {
            'faculty_name': ['faculty_name', 'faculty', 'instructor', 'teacher'],
            'subject_name': ['subject_name', 'subject', 'course'],
            'lecture_hours': ['lecture_hours', 'lectures', 'l_hours'],
            'tutorial_hours': ['tutorial_hours', 'tutorials', 't_hours'],
            'practical_hours': ['practical_hours', 'practicals', 'p_hours'],
            'division': ['division', 'div', 'section']
        }
    }
    
    suggestions = {}
    if data_type in mappings:
        for field, possible_names in mappings[data_type].items():
            for col in columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    suggestions[field] = col
                    break
    
    return suggestions

def process_imported_data(df, mapping, data_type, filename):
    """Process imported data and save to database"""
    # Create import session
    import_session = ImportedData()
    import_session.filename = filename
    import_session.data_type = data_type
    import_session.total_rows = len(df)
    import_session.successful_rows = 0
    import_session.failed_rows = 0
    import_session.mapping_config = json.dumps(mapping)
    
    try:
        db.session.add(import_session)
        db.session.commit()
        
        successful_rows = 0
        failed_rows = 0
        
        for index, row in df.iterrows():
            status = 'failed'
            error_msg = 'Processing failed'
            
            try:
                if data_type == 'faculty':
                    success = import_faculty_row(row, mapping)
                elif data_type == 'subjects':
                    success = import_subject_row(row, mapping)
                elif data_type == 'assignments':
                    success = import_assignment_row(row, mapping)
                else:
                    success = False
                
                if success:
                    successful_rows += 1
                    status = 'success'
                    error_msg = None
                    db.session.commit()  # Commit successful import
                else:
                    failed_rows += 1
                    db.session.rollback()  # Rollback failed import
                    
            except Exception as e:
                failed_rows += 1
                error_msg = str(e)
                db.session.rollback()
            
            # Save row data record
            try:
                row_record = ImportedDataRow()
                row_record.import_id = import_session.id
                row_record.row_data = json.dumps(row.to_dict())
                row_record.status = status
                row_record.error_message = error_msg
                db.session.add(row_record)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Failed to save row record: {e}")
        
        # Update import session with final counts
        import_session.successful_rows = successful_rows
        import_session.failed_rows = failed_rows
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Failed to create import session: {e}")
        raise e
    
    return import_session

def import_faculty_row(row, mapping):
    """Import a single faculty row"""
    try:
        # Generate username from name if not provided
        first_name = str(row.get(mapping.get('first_name', ''), '')).strip()[:64]
        last_name = str(row.get(mapping.get('last_name', ''), '')).strip()[:64]
        
        if not first_name or not last_name:
            return False
        
        username = f"{first_name.lower()}.{last_name.lower()}".replace(' ', '.')[:64]
        email = str(row.get(mapping.get('email', ''), f"{username}@college.edu")).strip()[:120]
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return False
        
        from werkzeug.security import generate_password_hash
        
        designation = str(row.get(mapping.get('designation', ''), 'Assistant Prof')).strip()[:50]
        department = str(row.get(mapping.get('department', ''), '')).strip()[:100]
        employee_id = str(row.get(mapping.get('employee_id', ''), '')).strip()[:20]
        
        user = User()
        user.username = username
        user.email = email
        user.password_hash = generate_password_hash('password123')  # Default password
        user.first_name = first_name
        user.last_name = last_name
        user.role = 'faculty'
        user.designation = designation
        user.department = department
        user.employee_id = employee_id
        
        db.session.add(user)
        db.session.flush()  # Flush to catch any constraint violations early
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing faculty row: {str(e)}")
        db.session.rollback()
        return False

def import_subject_row(row, mapping):
    """Import a single subject row"""
    try:
        name = str(row.get(mapping.get('name', ''), '')).strip()
        code = str(row.get(mapping.get('code', ''), '')).strip()
        
        if not name or not code:
            return False
        
        # Truncate long names to fit database constraints
        name = name[:255] if len(name) > 255 else name
        code = code[:50] if len(code) > 50 else code
        
        # Check if subject already exists
        existing_subject = Subject.query.filter_by(code=code).first()
        if existing_subject:
            return False
        
        # Validate and convert numeric fields
        try:
            lecture_hours = int(float(row.get(mapping.get('lecture_hours', ''), 0) or 0))
            tutorial_hours = int(float(row.get(mapping.get('tutorial_hours', ''), 0) or 0))
            practical_hours = int(float(row.get(mapping.get('practical_hours', ''), 0) or 0))
            semester = int(float(row.get(mapping.get('semester', ''), 1) or 1))
        except (ValueError, TypeError):
            lecture_hours = tutorial_hours = practical_hours = 0
            semester = 1
        
        department = str(row.get(mapping.get('department', ''), '')).strip()[:100]
        subject_type = str(row.get(mapping.get('subject_type', ''), 'Regular')).strip()[:20]
        
        subject = Subject()
        subject.name = name
        subject.code = code
        subject.lecture_hours = lecture_hours
        subject.tutorial_hours = tutorial_hours
        subject.practical_hours = practical_hours
        subject.semester = semester
        subject.department = department
        subject.subject_type = subject_type
        
        db.session.add(subject)
        db.session.flush()  # Flush to catch any constraint violations early
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing subject row: {str(e)}")
        db.session.rollback()
        return False

def import_assignment_row(row, mapping):
    """Import a single assignment row"""
    try:
        faculty_name = str(row.get(mapping.get('faculty_name', ''), '')).strip()
        subject_name = str(row.get(mapping.get('subject_name', ''), '')).strip()
        
        if not faculty_name or not subject_name:
            return False
        
        # Find faculty and subject
        faculty = User.query.filter(
            User.role == 'faculty',
            (User.first_name + ' ' + User.last_name).like(f'%{faculty_name}%')
        ).first()
        
        subject = Subject.query.filter(Subject.name.like(f'%{subject_name}%')).first()
        
        if not faculty or not subject:
            return False
        
        # Check if assignment already exists
        existing_assignment = Assignment.query.filter_by(
            faculty_id=faculty.id,
            subject_id=subject.id
        ).first()
        
        if existing_assignment:
            return False
        
        # Validate and convert numeric fields
        try:
            lecture_hours = int(float(row.get(mapping.get('lecture_hours', ''), 0) or 0))
            tutorial_hours = int(float(row.get(mapping.get('tutorial_hours', ''), 0) or 0))
            practical_hours = int(float(row.get(mapping.get('practical_hours', ''), 0) or 0))
        except (ValueError, TypeError):
            lecture_hours = tutorial_hours = practical_hours = 0
        
        division = str(row.get(mapping.get('division', ''), '')).strip()[:10]
        
        assignment = Assignment()
        assignment.faculty_id = faculty.id
        assignment.subject_id = subject.id
        assignment.lecture_hours = lecture_hours
        assignment.tutorial_hours = tutorial_hours
        assignment.practical_hours = practical_hours
        assignment.division = division
        
        db.session.add(assignment)
        db.session.flush()  # Flush to catch any constraint violations early
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing assignment row: {str(e)}")
        db.session.rollback()
        return False

def get_dashboard_stats():
    """Get dashboard statistics"""
    stats = {
        'total_faculty': User.query.filter_by(role='faculty').count(),
        'total_subjects': Subject.query.count(),
        'total_assignments': Assignment.query.count(),
        'total_students': User.query.filter_by(role='student').count(),
    }
    
    # Get workload statistics
    faculty_workloads = []
    for faculty in User.query.filter_by(role='faculty').all():
        workload = faculty.get_current_workload()
        limit = faculty.get_workload_limit()
        faculty_workloads.append({
            'name': faculty.full_name,
            'workload': workload,
            'limit': limit,
            'percentage': (workload / limit * 100) if limit > 0 else 0
        })
    
    stats['faculty_workloads'] = faculty_workloads
    
    # Get department statistics
    from sqlalchemy import func
    dept_stats = db.session.query(
        User.department,
        func.count(User.id).label('count')
    ).filter(User.role == 'faculty').group_by(User.department).all()
    
    stats['department_stats'] = [{'department': dept, 'count': count} for dept, count in dept_stats]
    
    return stats
