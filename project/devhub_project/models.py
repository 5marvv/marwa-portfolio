from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Snippet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    code = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200)) # Store as comma-separated
    is_favorite = db.Column(db.Boolean, default=False)