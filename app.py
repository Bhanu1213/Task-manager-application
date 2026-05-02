# app.py - Main Application File
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, date
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page'

# ============ MODELS ============

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='member')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    projects_created = db.relationship('Project', foreign_keys='Project.created_by', backref='creator')
    tasks_created = db.relationship('Task', foreign_keys='Task.created_by', backref='creator')
    tasks_assigned = db.relationship('Task', foreign_keys='Task.assigned_to', backref='assignee')
    project_memberships = db.relationship('ProjectMember', backref='user')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='active')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.Date, nullable=True)
    
    members = db.relationship('ProjectMember', backref='project', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='project', cascade='all, delete-orphan')

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    role = db.Column(db.String(50), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.String(20), default='medium')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

# ============ HELPER FUNCTIONS ============

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def member_of_project(project_id):
    if current_user.role == 'admin':
        return True
    member = ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first()
    return member is not None

# ============ ROUTES ============

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'member')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    if current_user.role == 'admin':
        total_projects = Project.query.count()
        total_tasks = Task.query.count()
        pending_tasks = Task.query.filter_by(status='pending').count()
        in_progress_tasks = Task.query.filter_by(status='in_progress').count()
        completed_tasks = Task.query.filter_by(status='completed').count()
        overdue_tasks = Task.query.filter(
            Task.due_date < date.today(),
            Task.status != 'completed'
        ).count()
        
        # Recent tasks
        recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    else:
        # Get user's projects
        user_projects = db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id).subquery()
        total_projects = Project.query.filter(Project.id.in_(user_projects)).count()
        total_tasks = Task.query.filter_by(assigned_to=current_user.id).count()
        pending_tasks = Task.query.filter_by(assigned_to=current_user.id, status='pending').count()
        in_progress_tasks = Task.query.filter_by(assigned_to=current_user.id, status='in_progress').count()
        completed_tasks = Task.query.filter_by(assigned_to=current_user.id, status='completed').count()
        overdue_tasks = Task.query.filter(
            Task.assigned_to == current_user.id,
            Task.due_date < date.today(),
            Task.status != 'completed'
        ).count()
        
        # Recent tasks
        recent_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).limit(5).all()
    
    stats = {
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks
    }
    
    return render_template('dashboard.html', stats=stats, recent_tasks=recent_tasks)

@app.route('/projects')
@login_required
def projects():
    if current_user.role == 'admin':
        projects = Project.query.order_by(Project.created_at.desc()).all()
        # Get member count for each project
        for project in projects:
            project.member_count = ProjectMember.query.filter_by(project_id=project.id).count()
            project.task_count = Task.query.filter_by(project_id=project.id).count()
    else:
        projects = db.session.query(Project).join(
            ProjectMember, Project.id == ProjectMember.project_id
        ).filter(
            ProjectMember.user_id == current_user.id
        ).order_by(Project.created_at.desc()).all()
        for project in projects:
            project.member_count = ProjectMember.query.filter_by(project_id=project.id).count()
            project.task_count = Task.query.filter_by(project_id=project.id).count()
    
    return render_template('projects.html', projects=projects)

@app.route('/projects/create', methods=['POST'])
@login_required
@admin_required
def create_project():
    name = request.form.get('name')
    description = request.form.get('description')
    deadline = request.form.get('deadline')
    
    if not name:
        flash('Project name is required', 'danger')
        return redirect(url_for('projects'))
    
    project = Project(
        name=name,
        description=description,
        created_by=current_user.id
    )
    
    if deadline:
        project.deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
    
    db.session.add(project)
    db.session.commit()
    
    # Add creator as member
    member = ProjectMember(project_id=project.id, user_id=current_user.id, role='admin')
    db.session.add(member)
    db.session.commit()
    
    flash('Project created successfully!', 'success')
    return redirect(url_for('projects'))

@app.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    
    if not member_of_project(project_id):
        flash('You do not have access to this project', 'danger')
        return redirect(url_for('projects'))
    
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.due_date.asc()).all()
    members = db.session.query(ProjectMember, User).join(
        User, ProjectMember.user_id == User.id
    ).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    # Get available users for adding members (admin only)
    available_users = []
    if current_user.role == 'admin':
        existing_member_ids = [m[0].user_id for m in members]
        available_users = User.query.filter(
            User.role == 'member',
            User.id.notin_(existing_member_ids)
        ).all()
    
    return render_template('project_detail.html', 
                         project=project, 
                         tasks=tasks, 
                         members=members,
                         available_users=available_users)

@app.route('/projects/<int:project_id>/add_member', methods=['POST'])
@login_required
@admin_required
def add_member(project_id):
    user_id = request.form.get('user_id')
    
    if not user_id:
        flash('Please select a user', 'danger')
        return redirect(url_for('project_detail', project_id=project_id))
    
    existing = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if existing:
        flash('User is already a member', 'warning')
        return redirect(url_for('project_detail', project_id=project_id))
    
    member = ProjectMember(project_id=project_id, user_id=user_id)
    db.session.add(member)
    db.session.commit()
    
    flash('Member added successfully!', 'success')
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/projects/<int:project_id>/delete')
@login_required
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully', 'success')
    return redirect(url_for('projects'))

@app.route('/tasks/create', methods=['POST'])
@login_required
def create_task():
    if current_user.role != 'admin':
        flash('Only admins can create tasks', 'danger')
        return redirect(request.referrer)
    
    title = request.form.get('title')
    description = request.form.get('description')
    project_id = request.form.get('project_id')
    assigned_to = request.form.get('assigned_to')
    due_date = request.form.get('due_date')
    priority = request.form.get('priority', 'medium')
    
    if not title or not project_id:
        flash('Task title and project are required', 'danger')
        return redirect(request.referrer)
    
    task = Task(
        title=title,
        description=description,
        project_id=project_id,
        created_by=current_user.id,
        priority=priority
    )
    
    if assigned_to:
        task.assigned_to = int(assigned_to)
    if due_date:
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    
    db.session.add(task)
    db.session.commit()
    
    flash('Task created successfully!', 'success')
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/tasks/<int:task_id>/update_status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check permissions
    if current_user.role != 'admin' and task.assigned_to != current_user.id:
        flash('You do not have permission to update this task', 'danger')
        return redirect(request.referrer)
    
    status = request.form.get('status')
    if status:
        task.status = status
        if status == 'completed':
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None
        db.session.commit()
        flash('Task status updated!', 'success')
    
    return redirect(request.referrer)

@app.route('/tasks/<int:task_id>/delete')
@login_required
@admin_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully', 'success')
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/my-tasks')
@login_required
def my_tasks():
    tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.due_date.asc()).all()
    return render_template('tasks.html', tasks=tasks)

# ============ CREATE DATABASE ============
with app.app_context():
    db.create_all()
    
    # Create default admin if not exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(name='Admin User', email='admin@example.com', password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: admin@example.com / admin123")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
