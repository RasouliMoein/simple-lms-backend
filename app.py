from flask import Flask
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from config import Config
from models import db
from auth import auth_bp
from upload import upload_bp
from lessons import lessons_bp
from exams import exams_bp
from swagger_config import swagger_config, swagger_template

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    JWTManager(app)
    Swagger(app, config=swagger_config, template=swagger_template)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(lessons_bp, url_prefix='/api/lessons')
    app.register_blueprint(exams_bp, url_prefix='/api/exams')
    
    with app.app_context():
        db.create_all()
        
        # Create default admin and professor if none exists
        from models import Admin, Professor
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

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)