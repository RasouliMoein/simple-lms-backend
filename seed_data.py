from app import create_app
from models import db, User, Student, Professor, Lesson, Section, Exam, Question, ExamSubmission

def seed_database():
    app = create_app()
    with app.app_context():
        print("Seeding database with mock data...")
        
        # Ensure users exist (from init_db.py)
        admin = User.query.filter_by(username='admin').first()
        professor = User.query.filter_by(username='professor').first()
        student = User.query.filter_by(username='student').first()
        
        if not professor:
            professor = Professor(
                username='professor',
                first_name='John',
                last_name='Smith',
                role='professor'
            )
            professor.set_password('prof123')
            db.session.add(professor)
            
        if not student:
            student = Student(
                username='student',
                first_name='Jane',
                last_name='Doe',
                student_id='STU2024001',
                role='student'
            )
            student.set_password('student123')
            db.session.add(student)
            
        db.session.commit()
        
        # ----------------------------------------------------
        # Lesson 1: Introduction to Python
        # ----------------------------------------------------
        lesson1 = Lesson.query.filter_by(title="مقدمه‌ای بر برنامه‌نویسی پایتون").first()
        if not lesson1:
            lesson1 = Lesson(
                title="مقدمه‌ای بر برنامه‌نویسی پایتون",
                professor_id=professor.id
            )
            db.session.add(lesson1)
            db.session.commit()
            print("- Created Lesson: Introduction to Python")
            
            # Sections for Lesson 1
            sec1 = Section(
                lesson_id=lesson1.id,
                title="۱. متغیرها و انواع داده‌ها در پایتون",
                body_content="""
                <p>در پایتون متغیرها مکان‌هایی برای ذخیره‌سازی داده‌ها هستند. پایتون به صورت پویا نوع‌گذاری می‌شود (Dynamically Typed)؛ به این معنی که نیازی به تعریف صریح نوع متغیر ندارید.</p>
                <pre><code>x = 5
y = "Hello World"
print(type(x))  # output: &lt;class 'int'&gt;
print(type(y))  # output: &lt;class 'str'&gt;</code></pre>
                """,
                order_index=0
            )
            sec2 = Section(
                lesson_id=lesson1.id,
                title="۲. دستورات شرطی و حلقه‌ها",
                body_content="""
                <p>حلقه‌ها و دستورات شرطی ساختار کنترلی برنامه را تشکیل می‌دهند. پایتون از فواصل خالی (Indentation) برای مشخص کردن بلاک‌های کد استفاده می‌کند.</p>
                <pre><code>if x > 3:
    print("x is greater than 3")
    
for i in range(3):
    print(f"Iteration {i}")</code></pre>
                """,
                order_index=1
            )
            db.session.add(sec1)
            db.session.add(sec2)
            db.session.commit()
            print("  - Created sections for Lesson 1")
            
            # Exam for Lesson 1 (Required association!)
            exam1 = Exam(
                title="کوئیز مقدماتی پایتون",
                lesson_id=lesson1.id,
                professor_id=professor.id
            )
            db.session.add(exam1)
            db.session.commit()
            print("- Created Exam: Python Basics Quiz")
            
            # Questions for Exam 1
            q1 = Question(
                exam_id=exam1.id,
                question_text="<p>خروجی دستور <code>print(5 // 2)</code> در پایتون چیست؟</p>",
                option_a="2.5",
                option_b="2",
                option_c="3",
                option_d="هیچکدام",
                correct_option="B",
                order_index=0
            )
            q2 = Question(
                exam_id=exam1.id,
                question_text="<p>کدام یک از ساختارهای داده زیر در پایتون <b>غیرقابل تغییر (Immutable)</b> است؟</p>",
                option_a="List (لیست)",
                option_b="Dictionary (دیکشنری)",
                option_c="Tuple (تاپل)",
                option_d="Set (مجموعه)",
                correct_option="C",
                order_index=1
            )
            db.session.add(q1)
            db.session.add(q2)
            db.session.commit()
            print("  - Added questions for Exam 1")
            
        # ----------------------------------------------------
        # Lesson 2: Object-Oriented Programming (OOP)
        # ----------------------------------------------------
        lesson2 = Lesson.query.filter_by(title="برنامه‌نویسی شیءگرا در پایتون").first()
        if not lesson2:
            lesson2 = Lesson(
                title="برنامه‌نویسی شیءگرا در پایتون",
                professor_id=professor.id
            )
            db.session.add(lesson2)
            db.session.commit()
            print("- Created Lesson: Object-Oriented Programming (OOP)")
            
            # Sections for Lesson 2
            sec3 = Section(
                lesson_id=lesson2.id,
                title="۱. کلاس‌ها و اشیاء",
                body_content="""
                <p>کلاس‌ها نقشه‌ها و اشیاء نمونه‌های ساخته شده از کلاس‌ها هستند. کلمه کلیدی <code>class</code> برای تعریف کلاس استفاده می‌شود.</p>
                <pre><code>class Car:
    def __init__(self, brand):
        self.brand = brand

my_car = Car("Tesla")
print(my_car.brand)  # output: Tesla</code></pre>
                """,
                order_index=0
            )
            db.session.add(sec3)
            db.session.commit()
            print("  - Created sections for Lesson 2")
            
            # Exam for Lesson 2 (Required association!)
            exam2 = Exam(
                title="آزمون شیءگرایی پایتون",
                lesson_id=lesson2.id,
                professor_id=professor.id
            )
            db.session.add(exam2)
            db.session.commit()
            print("- Created Exam: Python OOP Exam")
            
            # Questions for Exam 2
            q3 = Question(
                exam_id=exam2.id,
                question_text="<p>کدام متد جادویی (Magic Method) به عنوان <b>سازنده کلاس (Constructor)</b> در پایتون عمل می‌کند؟</p>",
                option_a="<code>__new__</code>",
                option_b="<code>__init__</code>",
                option_c="<code>__del__</code>",
                option_d="<code>__str__</code>",
                correct_option="B",
                order_index=0
            )
            db.session.add(q3)
            db.session.commit()
            print("  - Added questions for Exam 2")
            
        print("\nDatabase successfully populated with high-quality mock data!")

if __name__ == '__main__':
    seed_database()
