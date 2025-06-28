import pandas as pd
import json
import os
import re
from werkzeug.utils import secure_filename
from flask import current_app
from models import User, Subject, Assignment, ImportedData, ImportedDataRow
from app import db

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

def get_column_suggestions(df, data_type):
    """Get suggested column mappings based on data type"""
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
    import_session = ImportedData(
        filename=filename,
        data_type=data_type,
        total_rows=len(df),
        mapping_config=json.dumps(mapping)
    )
    db.session.add(import_session)
    db.session.flush()  # Get the ID
    
    successful_rows = 0
    failed_rows = 0
    
    for index, row in df.iterrows():
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
            else:
                failed_rows += 1
                status = 'failed'
                error_msg = 'Processing failed'
                
        except Exception as e:
            failed_rows += 1
            status = 'failed'
            error_msg = str(e)
        
        # Save row data
        row_record = ImportedDataRow(
            import_id=import_session.id,
            row_data=json.dumps(row.to_dict()),
            status=status,
            error_message=error_msg
        )
        db.session.add(row_record)
    
    import_session.successful_rows = successful_rows
    import_session.failed_rows = failed_rows
    db.session.commit()
    
    return import_session

def import_faculty_row(row, mapping):
    """Import a single faculty row"""
    try:
        # Generate username from name if not provided
        first_name = str(row.get(mapping.get('first_name', ''), '')).strip()
        last_name = str(row.get(mapping.get('last_name', ''), '')).strip()
        
        if not first_name or not last_name:
            return False
        
        username = f"{first_name.lower()}.{last_name.lower()}".replace(' ', '.')
        email = str(row.get(mapping.get('email', ''), f"{username}@college.edu")).strip()
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return False
        
        from werkzeug.security import generate_password_hash
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash('password123'),  # Default password
            first_name=first_name,
            last_name=last_name,
            role='faculty',
            designation=str(row.get(mapping.get('designation', ''), 'Assistant Prof')).strip(),
            department=str(row.get(mapping.get('department', ''), '')).strip(),
            employee_id=str(row.get(mapping.get('employee_id', ''), '')).strip()
        )
        
        db.session.add(user)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing faculty row: {str(e)}")
        return False

def import_subject_row(row, mapping):
    """Import a single subject row"""
    try:
        name = str(row.get(mapping.get('name', ''), '')).strip()
        code = str(row.get(mapping.get('code', ''), '')).strip()
        
        if not name or not code:
            return False
        
        # Check if subject already exists
        existing_subject = Subject.query.filter_by(code=code).first()
        if existing_subject:
            return False
        
        # Helper function to safely convert to integer
        def safe_int_convert(value, default=0):
            if pd.isna(value) or value == '' or value is None:
                return default
            try:
                # Convert to string first, then try to extract numeric part
                str_val = str(value).strip()
                if str_val == '' or str_val.lower() == 'nan':
                    return default
                # Try direct conversion first
                return int(float(str_val))
            except (ValueError, TypeError):
                # If it's a roman numeral or contains non-numeric characters, try to extract numbers
                import re
                numbers = re.findall(r'\d+', str_val)
                if numbers:
                    return int(numbers[0])
                # Convert roman numerals to integers
                roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}
                if str_val.upper() in roman_map:
                    return roman_map[str_val.upper()]
                return default
        
        subject = Subject(
            name=name,
            code=code,
            lecture_hours=safe_int_convert(row.get(mapping.get('lecture_hours', ''), 0), 0),
            tutorial_hours=safe_int_convert(row.get(mapping.get('tutorial_hours', ''), 0), 0),
            practical_hours=safe_int_convert(row.get(mapping.get('practical_hours', ''), 0), 0),
            semester=safe_int_convert(row.get(mapping.get('semester', ''), 1), 1),
            department=str(row.get(mapping.get('department', ''), '')).strip(),
            subject_type=str(row.get(mapping.get('subject_type', ''), 'Regular')).strip()
        )
        
        db.session.add(subject)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing subject row: {str(e)}")
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
        
        assignment = Assignment(
            faculty_id=faculty.id,
            subject_id=subject.id,
            lecture_hours=int(row.get(mapping.get('lecture_hours', ''), 0) or 0),
            tutorial_hours=int(row.get(mapping.get('tutorial_hours', ''), 0) or 0),
            practical_hours=int(row.get(mapping.get('practical_hours', ''), 0) or 0),
            division=str(row.get(mapping.get('division', ''), '')).strip()
        )
        
        db.session.add(assignment)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error importing assignment row: {str(e)}")
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
