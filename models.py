from flask_sqlalchemy import SQLAlchemy
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True)
    
    def __repr__(self):
        return '<User %r>' % self.username

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password.encode())



class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text(5000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return '<Note %r>' % self.title



class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='categories')
    notes = db.relationship('Note', backref='category')
    