from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.routes.auth import role_required
from app.models import db, Lesson, Section, SectionProgress

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/me', methods=['GET'])
@role_required(['student'])
def get_my_progress():
    """
    Get current student's progress across all lessons
    ---
    tags:
      - Progress
    security:
      - Bearer: []
    responses:
      200:
        description: List of lesson progress objects for the student
        schema:
          type: array
          items:
            type: object
            properties:
              lesson_id:
                type: integer
                example: 1
              lesson_title:
                type: string
                example: "مقدمه‌ای بر برنامه‌نویسی پایتون"
              total_sections:
                type: integer
                example: 2
              completed_sections_count:
                type: integer
                example: 1
              progress_percentage:
                type: number
                example: 50.0
              completed_section_ids:
                type: array
                items:
                  type: integer
                example: [1]
              next_section_id:
                type: integer
                example: 2
      401:
        description: Unauthorized
      403:
        description: Forbidden (insufficient permissions, student role required)
    """
    try:
        user_id = get_jwt().get('user_id')
        
        # Get all lessons
        lessons = Lesson.query.all()
        
        # Get all progress records for this student to make querying efficient
        progress_records = SectionProgress.query.filter_by(student_id=user_id).all()
        completed_section_ids = {p.section_id for p in progress_records}
        
        progress_list = []
        
        for lesson in lessons:
            # Sort sections by order_index
            sorted_sections = sorted(lesson.sections, key=lambda s: s.order_index)
            total_sections = len(sorted_sections)
            
            completed_in_lesson = [s.id for s in sorted_sections if s.id in completed_section_ids]
            completed_count = len(completed_in_lesson)
            
            percentage = 0.0
            if total_sections > 0:
                percentage = round((completed_count / total_sections) * 100, 2)
                
            # Find next section: the first section that is not completed
            next_section_id = None
            for s in sorted_sections:
                if s.id not in completed_section_ids:
                    next_section_id = s.id
                    break
            
            progress_list.append({
                'lesson_id': lesson.id,
                'lesson_title': lesson.title,
                'total_sections': total_sections,
                'completed_sections_count': completed_count,
                'progress_percentage': percentage,
                'completed_section_ids': completed_in_lesson,
                'next_section_id': next_section_id
            })
            
        return jsonify(progress_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@progress_bp.route('', methods=['POST'])
@role_required(['student'])
def mark_progress():
    """
    Mark a lesson section as completed
    ---
    tags:
      - Progress
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - section_id
          properties:
            section_id:
              type: integer
              example: 1
    responses:
      201:
        description: Progress recorded successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Progress recorded successfully"
            progress:
              type: object
              properties:
                id: { type: integer, example: 1 }
                student_id: { type: integer, example: 3 }
                section_id: { type: integer, example: 1 }
                completed_at: { type: string, example: "2026-06-14T01:30:00" }
      200:
        description: Section already marked as completed
      400:
        description: Bad request (missing fields, section doesn't exist)
      401:
        description: Unauthorized
      403:
        description: Forbidden
    """
    try:
        data = request.get_json()
        if not data or 'section_id' not in data:
            return jsonify({'error': 'section_id is required'}), 400
            
        section_id = data['section_id']
        
        # Verify section exists
        section = Section.query.get(section_id)
        if not section:
            return jsonify({'error': f'Section with ID {section_id} not found'}), 404
            
        user_id = get_jwt().get('user_id')
        
        # Check if progress already exists
        existing = SectionProgress.query.filter_by(student_id=user_id, section_id=section_id).first()
        if existing:
            return jsonify({
                'message': 'Section already marked as completed',
                'progress': existing.to_dict()
            }), 200
            
        progress = SectionProgress(
            student_id=user_id,
            section_id=section_id
        )
        db.session.add(progress)
        db.session.commit()
        
        return jsonify({
            'message': 'Progress recorded successfully',
            'progress': progress.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
