from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, TimeField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('faculty', 'Faculty')], validators=[DataRequired()])
    designation = SelectField('Designation', choices=[('', 'Select Designation'), ('Assistant Prof', 'Assistant Professor'), ('Associate Prof', 'Associate Professor'), ('Professor', 'Professor')], validators=[Optional()])
    department = StringField('Department', validators=[Optional()])
    employee_id = StringField('Employee ID', validators=[Optional()])

class FacultyForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    designation = SelectField('Designation', choices=[('Assistant Prof', 'Assistant Professor'), ('Associate Prof', 'Associate Professor'), ('Professor', 'Professor')], validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    employee_id = StringField('Employee ID', validators=[DataRequired()])

class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    code = StringField('Subject Code', validators=[DataRequired()])
    lecture_hours = IntegerField('Lecture Hours', validators=[Optional(), NumberRange(min=0)], default=0)
    tutorial_hours = IntegerField('Tutorial Hours', validators=[Optional(), NumberRange(min=0)], default=0)
    practical_hours = IntegerField('Practical Hours', validators=[Optional(), NumberRange(min=0)], default=0)
    subject_type = SelectField('Type', choices=[('Regular', 'Regular'), ('Elective', 'Elective')], validators=[DataRequired()])
    semester = IntegerField('Semester', validators=[DataRequired(), NumberRange(min=1, max=8)])
    department = StringField('Department', validators=[DataRequired()])
    division = StringField('Division', validators=[Optional()])

class AssignmentForm(FlaskForm):
    faculty_id = SelectField('Faculty', coerce=int, validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    lecture_hours = IntegerField('Lecture Hours', validators=[Optional(), NumberRange(min=0)], default=0)
    tutorial_hours = IntegerField('Tutorial Hours', validators=[Optional(), NumberRange(min=0)], default=0)
    practical_hours = IntegerField('Practical Hours', validators=[Optional(), NumberRange(min=0)], default=0)
    division = StringField('Division', validators=[Optional()])

class ExcelUploadForm(FlaskForm):
    file = FileField('Excel File', validators=[FileRequired(), FileAllowed(['xlsx', 'xls', 'csv'], 'Excel files only!')])
    data_type = SelectField('Data Type', choices=[('faculty', 'Faculty'), ('subjects', 'Subjects'), ('assignments', 'Assignments')], validators=[DataRequired()])

class ColumnMappingForm(FlaskForm):
    mapping_data = HiddenField('Mapping Data')
    skip_validation = BooleanField('Skip Validation Errors', default=False)
    create_missing_columns = BooleanField('Create Missing Database Columns', default=True)

class TimetableEntryForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    faculty_id = SelectField('Faculty', coerce=int, validators=[DataRequired()])
    day_of_week = SelectField('Day', choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday')], validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    room = StringField('Room', validators=[Optional()])
    division = StringField('Division', validators=[Optional()])
    semester = IntegerField('Semester', validators=[DataRequired(), NumberRange(min=1, max=8)])
    session_type = SelectField('Session Type', choices=[('Lecture', 'Lecture'), ('Tutorial', 'Tutorial'), ('Practical', 'Practical')], validators=[DataRequired()])
