from flask import *
from config import *
from forms import TeacherForm
from models import db, Teachers

app = Flask(__name__)
app.config.from_object(DevelopmentConfig())
db.init_app(app)


@app.route('/')
def home():
    return render_template('list.html', teachers = Teachers.query.all() )


@app.route('/teacher', methods = ['GET', 'POST'])
def add_teacher():
    form = TeacherForm()
   
    if request.method == 'POST':
        if form.validate():
            teacher = Teachers(request.form['name'], request.form['gender'],
            request.form['address'], request.form['email'], request.form['age'], request.form['lang'])
         
            db.session.add(teacher)
            db.session.commit()
         
            flash('Record was successfully added')
            return render_template('list.html', teachers=Teachers.query.all())
        else:
            flash('All fields are required.')
            return render_template('form.html', form = form, form_name = 'add')
    return render_template('form.html', form = form, form_name = 'add')


@app.route('/teacher/<int:id>', methods=["GET", "POST"])
def teacher_details(id):
    teacher = Teachers.query.get_or_404(id)
    if request.method == 'POST':
        form = TeacherForm(formdata=request.form, obj=teacher)
        if form.validate():
            teacher.name = request.form['name'],
            teacher.gender = request.form['gender'],
            teacher.address = request.form['address'],
            teacher.email = request.form['email'],
            teacher.age = request.form['age'],
            teacher.lang = request.form['lang']

            db.session.add(teacher)
            db.session.commit()

            flash('Record was successfully added')
            return redirect(url_for('home'))
    else:
        form = TeacherForm(obj=teacher)

    return render_template('form.html', form=form, form_name = 'edit', teacher_id=teacher.id)


@app.route('/teacher/<int:id>/delete', methods=["GET"])
def delete_teacher(id):
    teacher = Teachers.query.get_or_404(id)
    db.session.delete(teacher)
    db.session.commit()
    return jsonify(result=True)

if __name__ == '__main__':
    # To run this app, hit following commands on terminal-
    # export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/test_flask'
    # flask run
    app.run()

