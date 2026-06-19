from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///company.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# --- Модели (Таблицы БД) ---
class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    location = db.Column(db.String(100), nullable=False)
    employees = db.relationship('Employee', backref='department', lazy=True)


class Position(db.Model):
    __tablename__ = 'positions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    salary = db.Column(db.Float, nullable=False)
    employees = db.relationship('Employee', backref='position', lazy=True)


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    birth_date = db.Column(db.String(20), nullable=False, default='01.01.2000')
    hire_date = db.Column(db.String(20), nullable=False, default='01.01.2020')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False)


# --- 1. СОЗДАНИЕ ТАБЛИЦ И ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ ---
with app.app_context():
    db.create_all()

    # Проверяем, пустая ли БД
    if Department.query.count() == 0:
        print("📌 Заполняем базу данных тестовыми данными...")

        # 1. Отделы
        depts = [
            Department(name='IT-отдел', location='Офис 101'),
            Department(name='Отдел продаж', location='Офис 202'),
            Department(name='Бухгалтерия', location='Офис 303')
        ]
        db.session.add_all(depts)

        # 2. Должности
        pos = [
            Position(title='Разработчик', salary=120000),
            Position(title='Менеджер', salary=80000),
            Position(title='Бухгалтер', salary=70000),
            Position(title='Тестировщик', salary=50000)
        ]
        db.session.add_all(pos)

        # Сохраняем отделы и должности, чтобы получить их ID
        db.session.commit()

        # 3. Сотрудники (ПРАВИЛЬНО: передаем объекты Employee)
        employees = [
            Employee(
                full_name='Иван Иванов',
                birth_date='15.05.1990',
                hire_date='01.03.2020',
                department_id=1,  # IT-отдел
                position_id=1  # Разработчик
            ),
            Employee(
                full_name='Петр Петров',
                birth_date='22.11.1988',
                hire_date='15.06.2019',
                department_id=2,  # Отдел продаж
                position_id=2  # Менеджер
            ),
            Employee(
                full_name='Сергей Сергеев',
                birth_date='03.09.1995',
                hire_date='10.01.2021',
                department_id=3,  # Бухгалтерия
                position_id=3  # Бухгалтер
            ),
            Employee(
                full_name='Анна Смирнова',
                birth_date='07.04.1992',
                hire_date='20.11.2020',
                department_id=1,  # IT-отдел
                position_id=4  # Тестировщик
            )
        ]
        db.session.add_all(employees)
        db.session.commit()

        print("✅ База данных успешно заполнена!")
        print(f"   - Отделов: {Department.query.count()}")
        print(f"   - Должностей: {Position.query.count()}")
        print(f"   - Сотрудников: {Employee.query.count()}")


# --- МАРШРУТЫ (СТРАНИЦЫ) ---

@app.route('/')
def index():
    total_employees = Employee.query.count()
    total_departments = Department.query.count()
    total_positions = Position.query.count()
    return render_template('index.html',
                           total_employees=total_employees,
                           total_departments=total_departments,
                           total_positions=total_positions)


# ---------- ОТДЕЛЫ ----------
@app.route('/departments')
def departments():
    depts = Department.query.all()
    return render_template('departments.html', departments=depts)


@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        new_dept = Department(name=name, location=location)
        db.session.add(new_dept)
        db.session.commit()
        flash('Отдел успешно добавлен!', 'success')
        return redirect(url_for('departments'))
    return render_template('add_department.html')


@app.route('/delete_department/<int:id>')
def delete_department(id):
    dept = Department.query.get_or_404(id)
    if Employee.query.filter_by(department_id=id).count() > 0:
        flash('Нельзя удалить отдел, в котором есть сотрудники!', 'danger')
    else:
        db.session.delete(dept)
        db.session.commit()
        flash('Отдел удален!', 'success')
    return redirect(url_for('departments'))


# ---------- ДОЛЖНОСТИ ----------
@app.route('/positions')
def positions():
    pos = Position.query.all()
    return render_template('positions.html', positions=pos)


@app.route('/add_position', methods=['GET', 'POST'])
def add_position():
    if request.method == 'POST':
        title = request.form['title']
        salary = float(request.form['salary'])
        new_pos = Position(title=title, salary=salary)
        db.session.add(new_pos)
        db.session.commit()
        flash('Должность успешно добавлена!', 'success')
        return redirect(url_for('positions'))
    return render_template('add_position.html')


@app.route('/delete_position/<int:id>')
def delete_position(id):
    pos = Position.query.get_or_404(id)
    if Employee.query.filter_by(position_id=id).count() > 0:
        flash('Нельзя удалить должность, которая назначена сотрудникам!', 'danger')
    else:
        db.session.delete(pos)
        db.session.commit()
        flash('Должность удалена!', 'success')
    return redirect(url_for('positions'))


# ---------- СОТРУДНИКИ ----------
@app.route('/employees')
def employees():
    all_employees = db.session.query(
        Employee.id,
        Employee.full_name,
        Employee.birth_date,
        Employee.hire_date,
        Department.name.label('dept_name'),
        Position.title.label('pos_title'),
        Position.salary
    ).join(Department, Employee.department_id == Department.id) \
        .join(Position, Employee.position_id == Position.id) \
        .all()
    return render_template('employees.html', employees=all_employees)


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    depts = Department.query.all()
    positions = Position.query.all()
    if request.method == 'POST':
        full_name = request.form['full_name']
        birth_date = request.form['birth_date']
        hire_date = request.form['hire_date']
        dept_id = int(request.form['department_id'])
        pos_id = int(request.form['position_id'])

        new_emp = Employee(
            full_name=full_name,
            birth_date=birth_date,
            hire_date=hire_date,
            department_id=dept_id,
            position_id=pos_id
        )
        db.session.add(new_emp)
        db.session.commit()
        flash('Сотрудник успешно добавлен!', 'success')
        return redirect(url_for('employees'))
    return render_template('add_employee.html', departments=depts, positions=positions)


@app.route('/delete_employee/<int:id>')
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    flash('Сотрудник удален!', 'success')
    return redirect(url_for('employees'))


# ---------- ПОИСК ----------
@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        query = request.form['query'].strip()
        if query:
            results = db.session.query(
                Employee.full_name,
                Department.name.label('dept_name'),
                Position.title.label('pos_title')
            ).join(Department, Employee.department_id == Department.id) \
                .join(Position, Employee.position_id == Position.id) \
                .filter(Employee.full_name.contains(query)) \
                .all()
    return render_template('search.html', results=results)


if __name__ == '__main__':
    # Для Windows используем порт 5001 (чтобы избежать конфликта с системным процессом)
    app.run(debug=True, host='127.0.0.1', port=5001)