from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.routes.auth import role_required
from app.models import db, Exam, Question, ExamSubmission

exams_bp = Blueprint('exams', __name__)

@exams_bp.route('', methods=['GET'])
@jwt_required()
def get_exams():
    """
    Get all exams
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: lesson_id
        in: query
        type: integer
        required: false
        description: Filter exams by lesson ID
    responses:
      200:
        description: A list of exams (without correct options)
    """
    lesson_id = request.args.get('lesson_id', type=int)
    
    if lesson_id:
        exams = Exam.query.filter_by(lesson_id=lesson_id).all()
    else:
        exams = Exam.query.all()
        
    claims = get_jwt()
    include_answers = claims.get('role') in ['professor', 'admin']
    
    return jsonify([exam.to_dict(include_answers=include_answers) for exam in exams]), 200


@exams_bp.route('/<int:exam_id>', methods=['GET'])
@jwt_required()
def get_exam(exam_id):
    """
    Get a specific exam by ID
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: exam_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Exam details with questions (correct options hidden for students)
      404:
        description: Exam not found
    """
    exam = Exam.query.get_or_404(exam_id)
    
    claims = get_jwt()
    include_answers = claims.get('role') in ['professor', 'admin']
    
    return jsonify(exam.to_dict(include_answers=include_answers)), 200


@exams_bp.route('', methods=['POST'])
@role_required(['professor', 'admin'])
def create_exam():
    """
    Create a new exam
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [title, lesson_id]
          properties:
            title:
              type: string
              example: "پایان‌ترم برنامه‌نویسی پایتون"
            lesson_id:
              type: integer
              example: 1
    responses:
      201:
        description: Exam created successfully
      400:
        description: Bad request
    """
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
        
    if 'lesson_id' not in data or data.get('lesson_id') is None:
        return jsonify({'error': 'lesson_id is required and cannot be null'}), 400
        
    user_id = get_jwt().get('user_id')
    
    exam = Exam(
        title=data['title'],
        lesson_id=data['lesson_id'],
        professor_id=user_id
    )
    
    db.session.add(exam)
    db.session.commit()
    
    return jsonify({'message': 'Exam created successfully', 'exam': exam.to_dict(include_answers=True)}), 201


@exams_bp.route('/<int:exam_id>', methods=['PUT'])
@role_required(['professor', 'admin'])
def update_exam(exam_id):
    """
    Update exam metadata
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: exam_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "پایان‌ترم برنامه‌نویسی پایتون (ویرایش شده)"
            lesson_id:
              type: integer
              example: 1
    responses:
      200:
        description: Exam updated successfully
      400:
        description: Bad request
      404:
        description: Exam not found
    """
    exam = Exam.query.get_or_404(exam_id)
    data = request.get_json()
    
    if data:
        if 'title' in data:
            if not data['title']:
                return jsonify({'error': 'Title cannot be empty'}), 400
            exam.title = data['title']
        if 'lesson_id' in data:
            if data['lesson_id'] is None:
                return jsonify({'error': 'lesson_id cannot be null'}), 400
            exam.lesson_id = data['lesson_id']
            
        db.session.commit()
        return jsonify({'message': 'Exam updated successfully', 'exam': exam.to_dict(include_answers=True)}), 200
    return jsonify({'error': 'No data provided to update'}), 400


@exams_bp.route('/<int:exam_id>', methods=['DELETE'])
@role_required(['professor', 'admin'])
def delete_exam(exam_id):
    """
    Delete an exam
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: exam_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Exam deleted successfully
      404:
        description: Exam not found
    """
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    
    return jsonify({'message': 'Exam deleted successfully'}), 200


# ==========================================
# Question Operations
# ==========================================

@exams_bp.route('/<int:exam_id>/questions', methods=['POST'])
@role_required(['professor', 'admin'])
def create_question(exam_id):
    """
    Add a question to an exam
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: exam_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [question_text, option_a, option_b, option_c, option_d, correct_option]
          properties:
            question_text:
              type: string
              example: "<p>خروجی کد <code>print(2 ** 3)</code> چیست؟</p>"
            option_a:
              type: string
              example: "6"
            option_b:
              type: string
              example: "8"
            option_c:
              type: string
              example: "9"
            option_d:
              type: string
              example: "هیچکدام"
            correct_option:
              type: string
              example: "B"
    responses:
      201:
        description: Question added successfully
      400:
        description: Bad request
      404:
        description: Exam not found
    """
    exam = Exam.query.get_or_404(exam_id)
    data = request.get_json()
    
    required_fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
    for field in required_fields:
        if not data or field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
            
    correct_opt = data['correct_option'].upper()
    if correct_opt not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'correct_option must be A, B, C, or D'}), 400
        
    # Auto determine order_index
    max_order = db.session.query(db.func.max(Question.order_index)).filter_by(exam_id=exam.id).scalar()
    next_index = 0 if max_order is None else max_order + 1
    
    question = Question(
        exam_id=exam.id,
        question_text=data['question_text'],
        option_a=data['option_a'],
        option_b=data['option_b'],
        option_c=data['option_c'],
        option_d=data['option_d'],
        correct_option=correct_opt,
        order_index=next_index
    )
    
    db.session.add(question)
    db.session.commit()
    
    return jsonify({'message': 'Question added successfully', 'question': question.to_dict(include_correct=True)}), 201


@exams_bp.route('/<int:exam_id>/questions/<int:question_id>', methods=['PUT'])
@role_required(['professor', 'admin'])
def update_question(exam_id, question_id):
    """
    Update a specific question
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: exam_id
        in: path
        type: integer
        required: true
      - name: question_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            question_text:
              type: string
            option_a:
              type: string
            option_b:
              type: string
            option_c:
              type: string
            option_d:
              type: string
            correct_option:
              type: string
            order_index:
              type: integer
    responses:
      200:
        description: Question updated successfully
      404:
        description: Question not found
    """
    question = Question.query.filter_by(id=question_id, exam_id=exam_id).first_or_404()
    data = request.get_json()
    
    if data:
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'option_a' in data:
            question.option_a = data['option_a']
        if 'option_b' in data:
            question.option_b = data['option_b']
        if 'option_c' in data:
            question.option_c = data['option_c']
        if 'option_d' in data:
            question.option_d = data['option_d']
        if 'correct_option' in data:
            correct_opt = data['correct_option'].upper()
            if correct_opt not in ['A', 'B', 'C', 'D']:
                return jsonify({'error': 'correct_option must be A, B, C, or D'}), 400
            question.correct_option = correct_opt
        if 'order_index' in data:
            question.order_index = data['order_index']
            
        db.session.commit()
        return jsonify({'message': 'Question updated successfully', 'question': question.to_dict(include_correct=True)}), 200
        
    return jsonify({'error': 'No data provided to update'}), 400


@exams_bp.route('/<int:exam_id>/questions/<int:question_id>', methods=['DELETE'])
@role_required(['professor', 'admin'])
def delete_question(exam_id, question_id):
    """
    Delete a specific question
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: exam_id
        in: path
        type: integer
        required: true
      - name: question_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Question deleted successfully
      404:
        description: Question not found
    """
    question = Question.query.filter_by(id=question_id, exam_id=exam_id).first_or_404()
    db.session.delete(question)
    
    # Auto reorder remaining questions
    remaining = Question.query.filter_by(exam_id=exam_id).order_by(Question.order_index).all()
    for index, q in enumerate(remaining):
        q.order_index = index
        
    db.session.commit()
    return jsonify({'message': 'Question deleted successfully, indices reordered'}), 200


# ==========================================
# Exam Submission & Grading
# ==========================================

@exams_bp.route('/<int:exam_id>/submit', methods=['POST'])
@jwt_required()
def submit_exam(exam_id):
    """
    Submit exam answers and get instant score
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: exam_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [answers]
          properties:
            answers:
              type: object
              description: A dictionary mapping question ID string to selected option A/B/C/D
              example: {"1": "B", "2": "C"}
    responses:
      200:
        description: Exam submitted successfully with grading details
      400:
        description: Bad request (no answers or no questions in exam)
      404:
        description: Exam not found
    """
    exam = Exam.query.get_or_404(exam_id)
    data = request.get_json()
    
    if not data or 'answers' not in data:
        return jsonify({'error': 'Answers are required'}), 400
        
    submitted_answers = data['answers'] # Dict mapping question_id (str) to option (str)
    
    questions = exam.questions
    if not questions:
        return jsonify({'error': 'This exam has no questions'}), 400
        
    total_questions = len(questions)
    correct_count = 0
    breakdown = []
    
    for q in questions:
        q_id_str = str(q.id)
        selected = submitted_answers.get(q_id_str)
        if selected:
            selected = selected.upper()
            
        correct = q.correct_option
        is_correct = (selected == correct)
        
        if is_correct:
            correct_count += 1
            
        breakdown.append({
            'question_id': q.id,
            'selected_option': selected,
            'correct_option': correct,
            'is_correct': is_correct
        })
        
    score = (correct_count / total_questions) * 100
    user_id = get_jwt().get('user_id')
    
    submission = ExamSubmission(
        exam_id=exam.id,
        student_id=user_id,
        score=score
    )
    db.session.add(submission)
    db.session.commit()
    
    return jsonify({
        'message': 'Exam submitted and graded successfully',
        'submission_id': submission.id,
        'score': score,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'breakdown': breakdown
    }), 200

@exams_bp.route('/submissions', methods=['GET'])
@jwt_required()
def get_submissions():
    """
    Get exam submissions/history for student or system
    ---
    tags:
      - Exams
    security: [{Bearer: []}]
    parameters:
      - name: student_id
        in: query
        type: integer
        required: false
        description: Filter history by a specific student ID (accessible by Professor or Admin roles only).
    responses:
      200:
        description: List of submissions successfully retrieved.
      403:
        description: Insufficient permissions.
    """
    claims = get_jwt()
    role = claims.get('role')
    user_id = claims.get('user_id')
    
    if role == 'student':
        # Students are forced to only see their own exam scores/submissions
        submissions = ExamSubmission.query.filter_by(student_id=user_id).all()
    else:
        # Admins & Professors can query any student's score history, or see all if student_id parameter is empty
        filter_student_id = request.args.get('student_id', type=int)
        if filter_student_id:
            submissions = ExamSubmission.query.filter_by(student_id=filter_student_id).all()
        else:
            submissions = ExamSubmission.query.all()
            
    return jsonify([sub.to_dict() for sub in submissions]), 200
