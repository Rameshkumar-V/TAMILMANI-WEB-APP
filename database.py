from flask import request, Flask
import os
# ADMIN HANDLER
from flask_admin import Admin
from flask_admin.form.upload import FileUploadField
from flask_admin.contrib.sqla import ModelView

# ADMIN INSIDE FORM EDITORS
from wtforms.fields import SelectField
from flask_admin.form import Select2Widget

# DATABASE HANDLER
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)

# CONFIGURATIONS
app.config['SECRET_KEY'] = 'your_secret_key' # secret key
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmproject.db' # db path

app.config['SQLALCHEMY_DATABASE_URI'] ="mysql://rk:rk@localhost/blog"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Temporary upload folder

db = SQLAlchemy(app)

# NOTE : This line help me for temporarily filefieldupload pdf stored and upl to db.
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# CONTACT MODEL
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# CATEGORY MODEL
class Category(db.Model):
    c_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(30), unique=True, nullable=False)

    def __repr__(self):
        return f"Category('{self.category}')"

# DOCUMENT MODEL
class Document(db.Model):
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_filename = db.Column(db.String(100), nullable=False)  # Storing original filename
    document = db.Column(db.LargeBinary, nullable=False)  # Storing document content directly
    category_id = db.Column(db.Integer, db.ForeignKey('category.c_id'), nullable=False)
    upl_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category = db.relationship('Category', backref=db.backref('documents', lazy=True))

    def __repr__(self):
        return f"Document('{self.document_filename}', '{self.upl_date}', '{self.category.category}')"
   

    def delete_file(self):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], self.document_filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File '{self.document_filename}' deleted successfully.")
            else:
                print(f"File '{self.document_filename}' does not exist.")
        except Exception as e:
            print(f"Error deleting file '{self.document_filename}': {str(e)}")


# PAGE INFORMATION MODEL
class PageInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    job = db.Column(db.String(100), nullable=False)
    slogan = db.Column(db.Text, nullable=False)
    aboutme = db.Column(db.Text, nullable=False)
    profile_url = db.Column(db.String(255), nullable=False)
    about_me_url = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"PageInformation('{self.name}', '{self.job}')"



# CONTACT INFO MODEL
class ContactInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"ContactInfo('{self.app_name}', '{self.link}')"
    

# PROFILE ABOUT MODEL
class ProfileAbout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text, nullable=False)


'''
 CUSTOMLY I AM SHOWING 
 ----------------------
'''


# for DOCUMENT
class DocumentView(ModelView):
    form_overrides = {
        'document': FileUploadField
    }
    form_args = {
        'document': {
            'base_path': app.config['UPLOAD_FOLDER']
        }
    }
    column_exclude_list = ['document']
    form_excluded_columns = ['upl_date','document_filename']  # Excluded items

    def scaffold_form(self):
        # THIS FUNCTION SHOWING CATEGORY
        form_class = super(DocumentView, self).scaffold_form()
        form_class.category_id = SelectField('Category', widget=Select2Widget())
        return form_class

    def edit_form(self, obj=None):
        # THIS FUNCTION FOR EDITING AREA CATEGORY SHOWING
        form = super(DocumentView, self).edit_form(obj)
        form.category_id.choices = [(c.c_id, c.category) for c in Category.query.all()]
        return form

    def create_form(self, obj=None):
        # CATEGORIES VALUES CHOICES FOR INPUt OR CREATE AREA
        form = super(DocumentView, self).create_form(obj)
        form.category_id.choices = [(c.c_id, c.category) for c in Category.query.all()]
        return form

    def on_model_change(self, form, model, is_created):
        # AFTER FORM SUBMISSTION
        file = request.files.get('document')
        if file:
            # NOTE :  seek is imp on file getting area without this you can store empty file. 
            
            file.seek(0)  
            file_data = file.read()  
           
            model.document = file_data 
            model.document_filename = file.filename  
            # THIS HELPS ME DELETE TEMPORARY FILES NAME IN UPLOADS/
            model.delete_file()







