import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_, func
from app import db
from models import User, Subject, Assignment, TimetableEntry, ImportedData, ImportedDataRow
from forms import (LoginForm, RegisterForm, FacultyForm, SubjectForm, AssignmentForm, 
                   ExcelUploadForm, ColumnMappingForm, TimetableEntryForm)
from utils import (save_uploaded_file, read_excel_file, get_column_suggestions, 
                   process_imported_data, get_dashboard_stats)

# Create blueprints
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
faculty_bp = Blueprint('faculty', __name__)
subjects_bp = Blueprint('subjects', __name__)
assignments_bp = Blueprint('assignments', __name__)
excel_bp = Blueprint('excel', __name__)
timetable_bp = Blueprint('timetable', __name__)

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            or_(User.username == form.username.data, User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=form.role.data,
                designation=form.designation.data if form.role.data == 'faculty' else None,
                department=form.department.data if form.role.data == 'faculty' else None,
                employee_id=form.employee_id.data if form.role.data == 'faculty' else None
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

# Main routes
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

# Faculty routes
@faculty_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    designation = request.args.get('designation', '')
    
    query = User.query.filter_by(role='faculty')
    
    if search:
        query = query.filter(
            or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search),
                User.employee_id.contains(search)
            )
        )
    
    if department:
        query = query.filter(User.department == department)
    
    if designation:
        query = query.filter(User.designation == designation)
    
    faculty_list = query.order_by(User.first_name).all()
    
    # Get filter options
    departments = db.session.query(User.department).filter(User.role == 'faculty').distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    designations = ['Assistant Prof', 'Associate Prof', 'Professor']
    
    return render_template('faculty/index.html', 
                         faculty_list=faculty_list,
                         departments=departments,
                         designations=designations,
                         current_search=search,
                         current_department=department,
                         current_designation=designation)

@faculty_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('faculty.index'))
    
    form = FacultyForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            or_(User.username == form.username.data, User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
        else:
            faculty = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash('password123'),  # Default password
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role='faculty',
                designation=form.designation.data,
                department=form.department.data,
                employee_id=form.employee_id.data
            )
            db.session.add(faculty)
            db.session.commit()
            flash('Faculty member added successfully!', 'success')
            return redirect(url_for('faculty.index'))
    
    return render_template('faculty/add.html', form=form)

@faculty_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('faculty.index'))
    
    faculty = User.query.get_or_404(id)
    if faculty.role != 'faculty':
        flash('Invalid faculty member', 'danger')
        return redirect(url_for('faculty.index'))
    
    form = FacultyForm(obj=faculty)
    if form.validate_on_submit():
        # Check if username or email already exists (excluding current user)
        existing_user = User.query.filter(
            or_(User.username == form.username.data, User.email == form.email.data),
            User.id != faculty.id
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
        else:
            faculty.username = form.username.data
            faculty.email = form.email.data
            faculty.first_name = form.first_name.data
            faculty.last_name = form.last_name.data
            faculty.designation = form.designation.data
            faculty.department = form.department.data
            faculty.employee_id = form.employee_id.data
            db.session.commit()
            flash('Faculty member updated successfully!', 'success')
            return redirect(url_for('faculty.view', id=faculty.id))
    
    return render_template('faculty/edit.html', form=form, faculty=faculty)

@faculty_bp.route('/view/<int:id>')
@login_required
def view(id):
    faculty = User.query.get_or_404(id)
    if faculty.role != 'faculty':
        flash('Invalid faculty member', 'danger')
        return redirect(url_for('faculty.index'))
    
    # Get assignments for this faculty
    assignments = Assignment.query.filter_by(faculty_id=faculty.id).all()
    
    return render_template('faculty/view.html', faculty=faculty, assignments=assignments)

@faculty_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('faculty.index'))
    
    faculty = User.query.get_or_404(id)
    if faculty.role != 'faculty':
        flash('Invalid faculty member', 'danger')
        return redirect(url_for('faculty.index'))
    
    # Check if faculty has assignments
    if faculty.assignments:
        flash('Cannot delete faculty member with existing assignments', 'danger')
    else:
        db.session.delete(faculty)
        db.session.commit()
        flash('Faculty member deleted successfully!', 'success')
    
    return redirect(url_for('faculty.index'))

# Subject routes
@subjects_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    semester = request.args.get('semester', '')
    subject_type = request.args.get('type', '')
    
    query = Subject.query
    
    if search:
        query = query.filter(
            or_(
                Subject.name.contains(search),
                Subject.code.contains(search)
            )
        )
    
    if department:
        query = query.filter(Subject.department == department)
    
    if semester:
        query = query.filter(Subject.semester == int(semester))
    
    if subject_type:
        query = query.filter(Subject.subject_type == subject_type)
    
    subjects = query.order_by(Subject.name).all()
    
    # Get filter options
    departments = db.session.query(Subject.department).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    semesters = list(range(1, 9))
    subject_types = ['Regular', 'Elective']
    
    return render_template('subjects/index.html',
                         subjects=subjects,
                         departments=departments,
                         semesters=semesters,
                         subject_types=subject_types,
                         current_search=search,
                         current_department=department,
                         current_semester=semester,
                         current_type=subject_type)

@subjects_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'faculty']:
        flash('Access denied.', 'danger')
        return redirect(url_for('subjects.index'))
    
    form = SubjectForm()
    if form.validate_on_submit():
        # Check if subject code already exists
        existing_subject = Subject.query.filter_by(code=form.code.data).first()
        if existing_subject:
            flash('Subject code already exists', 'danger')
        else:
            subject = Subject(
                name=form.name.data,
                code=form.code.data,
                lecture_hours=form.lecture_hours.data,
                tutorial_hours=form.tutorial_hours.data,
                practical_hours=form.practical_hours.data,
                subject_type=form.subject_type.data,
                semester=form.semester.data,
                department=form.department.data,
                division=form.division.data
            )
            db.session.add(subject)
            db.session.commit()
            flash('Subject added successfully!', 'success')
            return redirect(url_for('subjects.index'))
    
    return render_template('subjects/add.html', form=form)

@subjects_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'faculty']:
        flash('Access denied.', 'danger')
        return redirect(url_for('subjects.index'))
    
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    
    if form.validate_on_submit():
        # Check if subject code already exists (excluding current subject)
        existing_subject = Subject.query.filter(
            Subject.code == form.code.data,
            Subject.id != subject.id
        ).first()
        
        if existing_subject:
            flash('Subject code already exists', 'danger')
        else:
            subject.name = form.name.data
            subject.code = form.code.data
            subject.lecture_hours = form.lecture_hours.data
            subject.tutorial_hours = form.tutorial_hours.data
            subject.practical_hours = form.practical_hours.data
            subject.subject_type = form.subject_type.data
            subject.semester = form.semester.data
            subject.department = form.department.data
            subject.division = form.division.data
            db.session.commit()
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('subjects.index'))
    
    return render_template('subjects/edit.html', form=form, subject=subject)

@subjects_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('subjects.index'))
    
    subject = Subject.query.get_or_404(id)
    
    # Check if subject has assignments
    if subject.assignments:
        flash('Cannot delete subject with existing assignments', 'danger')
    else:
        db.session.delete(subject)
        db.session.commit()
        flash('Subject deleted successfully!', 'success')
    
    return redirect(url_for('subjects.index'))

# Assignment routes
@assignments_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    faculty_id = request.args.get('faculty_id', '')
    
    query = Assignment.query.join(User).join(Subject)
    
    if search:
        query = query.filter(
            or_(
                Subject.name.contains(search),
                Subject.code.contains(search),
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        )
    
    if faculty_id:
        query = query.filter(Assignment.faculty_id == int(faculty_id))
    
    assignments = query.order_by(User.first_name, Subject.name).all()
    
    # Get faculty list for filter
    faculty_list = User.query.filter_by(role='faculty').order_by(User.first_name).all()
    
    return render_template('assignments/index.html',
                         assignments=assignments,
                         faculty_list=faculty_list,
                         current_search=search,
                         current_faculty_id=faculty_id)

@assignments_bp.route('/assign', methods=['GET', 'POST'])
@login_required
def assign():
    if current_user.role not in ['admin', 'faculty']:
        flash('Access denied.', 'danger')
        return redirect(url_for('assignments.index'))
    
    form = AssignmentForm()
    
    # Populate choices
    form.faculty_id.choices = [(f.id, f.full_name) for f in User.query.filter_by(role='faculty').order_by(User.first_name).all()]
    form.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Subject.query.order_by(Subject.name).all()]
    
    if form.validate_on_submit():
        # Check if assignment already exists
        existing_assignment = Assignment.query.filter_by(
            faculty_id=form.faculty_id.data,
            subject_id=form.subject_id.data
        ).first()
        
        if existing_assignment:
            flash('Assignment already exists for this faculty and subject', 'danger')
        else:
            # Check workload limit
            faculty = User.query.get(form.faculty_id.data)
            total_hours = form.lecture_hours.data + form.tutorial_hours.data + form.practical_hours.data
            
            if not faculty.can_assign_workload(total_hours):
                flash(f'Cannot assign {total_hours} hours. Faculty workload limit exceeded. Current: {faculty.get_current_workload()}, Limit: {faculty.get_workload_limit()}', 'danger')
            else:
                assignment = Assignment(
                    faculty_id=form.faculty_id.data,
                    subject_id=form.subject_id.data,
                    lecture_hours=form.lecture_hours.data,
                    tutorial_hours=form.tutorial_hours.data,
                    practical_hours=form.practical_hours.data,
                    division=form.division.data
                )
                db.session.add(assignment)
                db.session.commit()
                flash('Assignment created successfully!', 'success')
                return redirect(url_for('assignments.index'))
    
    return render_template('assignments/assign.html', form=form)

@assignments_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('assignments.index'))
    
    assignment = Assignment.query.get_or_404(id)
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment deleted successfully!', 'success')
    
    return redirect(url_for('assignments.index'))

# Excel import routes
@excel_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_data():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = ExcelUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        data_type = form.data_type.data
        
        # Save uploaded file
        filepath = save_uploaded_file(file)
        if not filepath:
            flash('Error saving file', 'danger')
            return redirect(url_for('excel.import_data'))
        
        # Read Excel file
        df = read_excel_file(filepath)
        if df is None:
            flash('Error reading Excel file', 'danger')
            return redirect(url_for('excel.import_data'))
        
        # Store file info in session for mapping
        from flask import session
        session['excel_file'] = filepath
        session['data_type'] = data_type
        session['columns'] = df.columns.tolist()
        session['preview_data'] = df.head(10).to_dict('records')
        
        return redirect(url_for('excel.column_mapping'))
    
    return render_template('excel/import.html', form=form)

@excel_bp.route('/mapping', methods=['GET', 'POST'])
@login_required
def column_mapping():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    from flask import session
    from utils import get_available_db_fields, get_column_suggestions, infer_data_type, process_imported_data_universal
    
    # Check if session data exists
    if 'excel_file' not in session:
        flash('No file uploaded. Please upload a file first.', 'warning')
        return redirect(url_for('excel.import_data'))
    
    filepath = session['excel_file']
    data_type = session['data_type']
    columns = session['columns']
    
    # Read file again for processing
    df = read_excel_file(filepath)
    if df is None:
        flash('Error reading Excel file', 'danger')
        return redirect(url_for('excel.import_data'))
    
    form = ColumnMappingForm()
    
    if form.validate_on_submit():
        # Parse mapping data from form
        mapping = {}
        for col in columns:
            field_name = f"mapping_{col}"
            if field_name in request.form:
                value = request.form[field_name]
                if value:
                    mapping[col] = value
        
        if not mapping:
            flash('Please map at least one column before importing.', 'warning')
            return render_column_mapping_page(form, df, data_type, columns)
        
        # Start import process with universal system
        skip_validation = form.skip_validation.data
        create_missing_columns = form.create_missing_columns.data
        
        import_session = process_imported_data_universal(
            df, mapping, data_type, filepath, skip_validation, create_missing_columns
        )
        
        if import_session:
            flash(f'Import completed! {import_session.successful_rows} rows imported successfully, {import_session.failed_rows} rows failed.', 'success')
            # Clean up session
            session.pop('excel_file', None)
            session.pop('data_type', None)
            session.pop('columns', None)
            session.pop('preview_data', None)
            return redirect(url_for('excel.imported_data'))
        else:
            flash('Import failed. Please check your data and try again.', 'danger')
    
    return render_column_mapping_page(form, df, data_type, columns)

def render_column_mapping_page(form, df, data_type, columns):
    """Helper function to render column mapping page"""
    from utils import get_available_db_fields, get_column_suggestions, infer_data_type
    
    # Get available database fields for this data type
    available_fields = get_available_db_fields(data_type)
    
    # Get smart column suggestions
    suggestions = get_column_suggestions(df, data_type)
    
    # Get sample data for preview (first 3 non-null values per column)
    preview_data = {}
    for col in columns:
        non_null_values = df[col].dropna().astype(str).tolist()
        preview_data[col] = non_null_values[:3] if non_null_values else ['(empty)']
    
    # Infer data types for each column
    inferred_types = {}
    for col in columns:
        inferred_types[col] = infer_data_type(df[col])
    
    return render_template('excel/column_mapping.html',
                         form=form,
                         filename=os.path.basename(session.get('excel_file', '')),
                         data_type=data_type,
                         columns=columns,
                         available_fields=available_fields,
                         suggestions=suggestions,
                         preview_data=preview_data,
                         inferred_types=inferred_types,
                         total_rows=len(df))

# Legacy mapping route removed - now using universal system

@excel_bp.route('/imported-data')
@login_required
def imported_data():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    imports = ImportedData.query.order_by(ImportedData.import_date.desc()).all()
    return render_template('excel/imported_data.html', imports=imports)

# Timetable routes
@timetable_bp.route('/')
@login_required
def index():
    semester = request.args.get('semester', '1')
    division = request.args.get('division', '')
    
    query = TimetableEntry.query.join(Subject).join(User)
    
    if semester:
        query = query.filter(TimetableEntry.semester == int(semester))
    
    if division:
        query = query.filter(TimetableEntry.division == division)
    
    timetable_entries = query.order_by(
        TimetableEntry.day_of_week,
        TimetableEntry.start_time
    ).all()
    
    # Get filter options
    divisions = db.session.query(TimetableEntry.division).distinct().all()
    divisions = [div[0] for div in divisions if div[0]]
    
    semesters = list(range(1, 9))
    
    return render_template('timetable/index.html',
                         timetable_entries=timetable_entries,
                         divisions=divisions,
                         semesters=semesters,
                         current_semester=semester,
                         current_division=division)

@timetable_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'faculty']:
        flash('Access denied.', 'danger')
        return redirect(url_for('timetable.index'))
    
    form = TimetableEntryForm()
    
    # Populate choices
    form.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Subject.query.order_by(Subject.name).all()]
    form.faculty_id.choices = [(f.id, f.full_name) for f in User.query.filter_by(role='faculty').order_by(User.first_name).all()]
    
    if form.validate_on_submit():
        # Check for conflicts
        conflict = TimetableEntry.query.filter(
            TimetableEntry.faculty_id == form.faculty_id.data,
            TimetableEntry.day_of_week == form.day_of_week.data,
            TimetableEntry.start_time <= form.end_time.data,
            TimetableEntry.end_time >= form.start_time.data
        ).first()
        
        if conflict:
            flash('Time conflict detected! Faculty is already scheduled during this time.', 'danger')
        else:
            timetable_entry = TimetableEntry(
                subject_id=form.subject_id.data,
                faculty_id=form.faculty_id.data,
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                room=form.room.data,
                division=form.division.data,
                semester=form.semester.data,
                session_type=form.session_type.data
            )
            db.session.add(timetable_entry)
            db.session.commit()
            flash('Timetable entry created successfully!', 'success')
            return redirect(url_for('timetable.index'))
    
    return render_template('timetable/create.html', form=form)

@timetable_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('timetable.index'))
    
    timetable_entry = TimetableEntry.query.get_or_404(id)
    db.session.delete(timetable_entry)
    db.session.commit()
    flash('Timetable entry deleted successfully!', 'success')
    
    return redirect(url_for('timetable.index'))
