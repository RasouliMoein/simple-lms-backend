from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flasgger import Swagger
from app.config import Config
from app.models import db
from app.swagger_config import swagger_config, swagger_template

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for frontend developer connection
    CORS(app, supports_credentials=True)
    
    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Register blueprints (with routes package prefix)
    from app.routes.auth import auth_bp
    from app.routes.upload import upload_bp
    from app.routes.lessons import lessons_bp
    from app.routes.exams import exams_bp
    from app.routes.progress import progress_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(lessons_bp, url_prefix='/api/lessons')
    app.register_blueprint(exams_bp, url_prefix='/api/exams')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    
    with app.app_context():
        db.create_all()
        
        # Create default admin and professor if none exists
        from app.models import Admin, Professor
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', first_name='System', last_name='Admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
        if not Professor.query.filter_by(username='professor').first():
            prof = Professor(username='professor', first_name='John', last_name='Smith', role='professor')
            prof.set_password('prof123')
            db.session.add(prof)
            
        db.session.commit()
    
    return app
