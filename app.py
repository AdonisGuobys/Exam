from flask import Flask, render_template, session, redirect, url_for, request, send_from_directory
from forms import RegistrationForm, LoginForm, NoteForm, CategoryForm
from models import User, db, Note, Category
from werkzeug.utils import secure_filename
import bcrypt
import os
import time



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = "uploads"



db.init_app(app)



with app.app_context():
    db.create_all()



def unique_filename(filename):
    basename, ext = os.path.splitext(filename)
    unique_name = f"{basename}_{int(time.time())}{ext}"
    return secure_filename(unique_name)



@app.before_request
def require_login():
    logged_routes = ['categories', 'categories_notes', 'edit_categories', 'edit_note', 'notes', 'search_notes']
    if request.endpoint in logged_routes and not session.get('logged_in'):
        return redirect(url_for('login'))



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        user = User(username=username, password=hashed_password.decode())
        db.session.add(user)
        db.session.commit()
        session['logged_in'] = True
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template('register.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('login.html', form=form)



@app.route('/categories', methods=['GET', 'POST'])
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, user_id=session['user_id'])
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('categories'))
    user_categories = Category.query.filter_by(user_id=session['user_id']).all()
    return render_template('categories.html', form=form, categories=user_categories)



@app.route('/notes', methods=['GET', 'POST'])
def notes():
    form = NoteForm()
    user_categories = Category.query.filter_by(user_id=session['user_id']).all()
    form.category.choices = [(-1, 'No Categoy')] + [(c.id, c.name) for c in user_categories]
    if form.validate_on_submit():
        category_id = form.category.data if form.category.data != -1 else None
        note = Note(title=form.title.data, content=form.content.data, category_id=category_id, user_id=session['user_id'])
        if form.image.data:
            image = form.image.data
            image_filename = image.filename.strip()
            if image_filename:
                image_filename = image_filename.replace(" ", "_")
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                print("Image path:", image_path)
                image.save(image_path)
                note.image_filename = image_filename
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('notes'))
    user_notes = Note.query.filter_by(user_id=session['user_id']).all()
    return render_template('notes.html', form=form, notes=user_notes)



@app.route('/edit_note/<note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note = Note.query.get(note_id)
    if not note or note.user_id != session['user_id']:
        return redirect(url_for('notes'))
    form = NoteForm()
    user_categories = Category.query.filter_by(user_id=session['user_id']).all()
    form.category.choices = [(-1, 'No Category')] + [(c.id, c.name) for c in user_categories]
    if form.validate_on_submit():
        category_id = form.category.data if form.category.data != -1 else None
        note.title = form.title.data
        note.content = form.content.data
        note.category_id = category_id
        if form.image.data:
            image = form.image.data
            image_filename = image.filename.strip()
            if image_filename:
                image_filename = image_filename.replace(" ", "_")
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image.save(image_path)
                if note.image_filename:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], note.image_filename)
                    other_notes_with_same_image = Note.query.filter(
                        Note.image_filename == note.image_filename,
                        Note.id != note_id
                    ).count()
                    if os.path.exists(old_image_path) and other_notes_with_same_image == 0:
                        os.remove(old_image_path)
                note.image_filename = image_filename
        db.session.commit()
        return redirect(url_for('notes'))
    if request.method == 'GET':
        form.title.data = note.title
        form.content.data = note.content
        form.category.data = note.category_id if note.category_id else -1
    return render_template('edit_note.html', form=form, note_id=note_id, note=note)



@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note.user_id != session['user_id']:
        return redirect(url_for('notes'))
    if note.image_filename:
        other_notes_with_same_image = Note.query.filter(
            Note.image_filename == note.image_filename,
            Note.id != note_id
        ).count()
        if other_notes_with_same_image == 0:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], note.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('notes'))



@app.route('/category/<int:category_id>/notes', methods=['GET'])
def view_category_notes(category_id):
    category_notes = Note.query.filter_by(category_id=category_id, user_id=session['user_id']).all()
    return render_template('category_notes.html', notes=category_notes, category_id=category_id)



@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get(category_id)
    if category.user_id != session['user_id']:
        return redirect(url_for('categories'))
    notes_in_category = Note.query.filter_by(category_id=category_id).all()
    for note in notes_in_category:
        if note.image_filename:
            other_notes_with_same_image = Note.query.filter(
                Note.image_filename == note.image_filename,
                Note.id != note.id
            ).count()
            if other_notes_with_same_image == 0:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], note.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
    Note.query.filter_by(category_id=category_id).delete()
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('categories'))



@app.route('/search_notes', methods=['GET'])
def search_notes():
    query = request.args.get('query')
    notes = Note.query.filter(Note.user_id == session['user_id'], Note.title.like(f'%{query}%')).all()
    return render_template('search_notes.html', notes=notes)



@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get(category_id)
    if category.user_id != session['user_id']:
        return redirect(url_for('index'))
    form = CategoryForm()
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        return redirect(url_for('categories'))
    form.name.data = category.name
    return render_template('edit_category.html', form=form, category=category)



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)