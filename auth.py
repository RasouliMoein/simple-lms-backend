from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from models import db, User, Student
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new student
    ---
    tags: [Authentication]
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required: [first_name, last_name, student_id, username, password]
          properties:
            first_name: {type: string, example: John}
            last_name: {type: string, example: Doe}
            student_id: {type: string, example: STU2024001}
            username: {type: string, example: johndoe}
            password: {type: string, example: password123}
    responses:
      201: {description: Student registered successfully}
      400: {description: Bad request}
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'student_id', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Check if student_id already exists
        if User.query.filter_by(student_id=data['student_id']).first():
            return jsonify({'error': 'Student ID already exists'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Create new student
        student = Student(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            student_id=data['student_id'],
            role='student'
        )
        student.set_password(data['password'])
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify({
            'message': 'Student registered successfully',
            'user': student.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    ---
    tags: [Authentication]
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required: [username, password]
          properties:
            username: {type: string, example: admin}
            password: {type: string, example: admin123}
    responses:
      200: {description: Login successful}
      401: {description: Invalid credentials}
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        # Find user by username
        user = User.query.filter_by(username=data['username']).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create tokens with additional claims
        additional_claims = {
            'role': user.role,
            'user_id': user.id
        }
        
        access_token = create_access_token(
            identity=user.username,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=user.username)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    ---
    tags: [Authentication]
    security: [{Bearer: []}]
    responses:
      200: {description: New access token generated}
    """
    try:
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        additional_claims = {
            'role': user.role,
            'user_id': user.id
        }
        
        access_token = create_access_token(
            identity=current_user,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Get current user profile (Protected)
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Access granted. Returns current authenticated user profile.
      401:
        description: Missing or invalid JWT Access Token.
      404:
        description: Authenticated user not found in system.
    """
    try:
        current_username = get_jwt_identity()
        claims = get_jwt()
        
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': f'Hello {user.first_name}! You have {claims.get("role", "unknown")} access.',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Role-based access decorators
def role_required(roles):
    """Decorator to check user roles"""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# Example role-protected routes
@auth_bp.route('/admin/dashboard', methods=['GET'])
@role_required(['admin'])
def admin_dashboard():
    """
    Get Admin Dashboard Stats
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: System health and student/faculty registration statistics.
      403:
        description: Insufficient permissions (requires admin role).
    """
    return jsonify({
        'stats': {'total_students': 150, 'total_professors': 12},
        'system_status': 'healthy'
    }), 200

@auth_bp.route('/professor/classes', methods=['GET'])
@role_required(['professor', 'admin'])
def professor_classes():
    """
    Get Professor Class List
    ---
    tags:
      - Professor
    security:
      - Bearer: []
    responses:
      200:
        description: List of classes taught by professors.
      403:
        description: Insufficient permissions.
    """
    return jsonify({
        'classes': [
            {'id': 1, 'name': 'Introduction to CS', 'students': 35},
            {'id': 2, 'name': 'Advanced Algorithms', 'students': 20}
        ]
    }), 200

@auth_bp.route('/student/grades', methods=['GET'])
@role_required(['student'])
def student_grades():
    """
    Get Student Grades
    ---
    tags:
      - Student
    security:
      - Bearer: []
    responses:
      200:
        description: Current term grades for the student.
      403:
        description: Insufficient permissions (requires student role).
    """
    return jsonify({
        'grades': [
            {'course': 'Introduction to CS', 'grade': 'A'},
            {'course': 'Database Systems', 'grade': 'B+'}
        ]
    }), 200