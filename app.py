
# FLASK ATTRIBUTES
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    flash
)
# IMAGE BYTES HANDLER
import io

# DATABASE ORM HANDLER
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# PAGINATION HANDLER
from flask_paginate import Pagination, get_page_args

# SECURITY HASH PASSWORD HANDLER
from werkzeug.security import check_password_hash, generate_password_hash

# DATABASE MODULE HANDLER ( OUR MODULE )
from database import db, Contact, Document, Category, ContactInfo, PageInformation,DocumentView,ProfileAbout

# AUTHENTICATION AND LOGIN HANDLER
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user,login_required

# FLASK ADMIN HANDLER
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, Admin
# NOTE : FORM OPERATION 
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

app = Flask(__name__, template_folder='template')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmproject.db'
# app.config['SQLALCHEMY_DATABASE_URI'] ="mysql://rk:rk@localhost/blog"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecret'

# INITIALIZE DB
db.init_app(app)

migrate = Migrate(app, db)
login = LoginManager(app)



'''
ADMIN SECTION

'''
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# RE CONFIGURE MODELVIEW
class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class MyAdminIndexView(AdminIndexView):
    @login_required
    def is_accessible(self):
        return current_user.is_authenticated
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


# ADMIN INITIALIZING
db_admin = Admin(app, name='microblog', template_mode='bootstrap3',index_view=MyAdminIndexView())

# NOTE : add_view used to add db_admin pannel inside model based CRUD operations.

db_admin.add_view(DocumentView(Document, db.session))
db_admin.add_view(ModelView(Category, db.session))
db_admin.add_view(ModelView(Contact, db.session))
db_admin.add_view(ModelView(PageInformation, db.session))
db_admin.add_view(ModelView(ContactInfo, db.session))
db_admin.add_view(ModelView(ProfileAbout, db.session))
db_admin.add_view(MyModelView(User, db.session))



@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)
'''
END OF ADMIN SECTION

'''


# HOME PAGE
@app.route('/')
def home():
    page_data = PageInformation.query.first()
    contact_info_data = ContactInfo.query.all()
    categories = Category.query.all()
    return render_template('home.html', categories=categories, contact=contact_info_data, page_info=page_data)






# THANKYOU FOR CONTACT US
@app.route('/thank_you')
def thank_you():
    return "Thank you for your message! We'll get back to you soon."


# DOCUMENT GETTING
def get_documents(page, per_page, category_id=None, search_term=None):
    query = Document.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search_term:
        query = query.filter(Document.document_filename.ilike(f'%{search_term}%'))
    return query.paginate(page=page, per_page=per_page, error_out=False)



# DOWNLOAD PAGE
@app.route('/download_page')
def download_page():
    category_id = request.args.get('category_id', type=int)
    page, per_page, _ = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page_default=4)
    documents = get_documents(page, per_page, category_id)
    categories = Category.query.all()
    return render_template('download_page.html', documents=documents.items, pagination=documents, categories=categories, current_category=category_id)


# SEARCH ROUTE
@app.route('/search')
def search_documents():
    search_term = request.args.get('q', '').strip()
    if not search_term:
        return render_template('document_list.html', documents=None)
    
    page, per_page, _ = get_page_args(page_parameter='page', per_page_parameter='per_page')
    documents = get_documents(page, per_page, search_term=search_term)
    pagination = Pagination(page=page, total=documents.total, per_page=per_page, css_framework='bootstrap4')
    return render_template('document_list.html', documents=documents.items, pagination=pagination)


# DOCUMENT GETTING WITH ID FOR DOWNLOAD
@app.route('/get_document', methods=['GET'])
def get_document():
    document_id = request.args.get('document_id')
    if not document_id:
        return jsonify({'error': 'No document ID provided'}), 400
    
    document = Document.query.get(document_id)
    if not document:
        return jsonify({'error': 'Document not found'}), 404

    return send_file(
        io.BytesIO(document.document),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=document.document_filename
    )

# CONTACT US PAGE TO DB ROUTE
@app.route('/submit_contact_form', methods=['POST'])
def submit_contact_form():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    if name and email and message:
        new_contact = Contact(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()
        return redirect(url_for('thank_you'))
    return redirect(url_for('contact'))

# NOTE : PROFILE ABOUT PAGE
# -------------------------
@app.route('/profile')
def profile():

    profiles = ProfileAbout.query.all()
    
    formatted_profiles = []
    

    for profile in profiles:
        formatted_profile = {
            'title': profile.title,
            # Replace \n with <br> tags
            'detail': profile.detail.split('/n')
        }
        print(formatted_profile)
        formatted_profiles.append(formatted_profile)
    
    return render_template('profile.html', profiles=formatted_profiles)


# NOTE : LOGIN FORM
# ------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=25)])
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            
            return redirect(url_for('admin.index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)



# LOGOUT ROUTE
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home')) 



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='tm').first():
            new_user = User(username='tm', password=generate_password_hash('1234'))
            db.session.add(new_user)
            db.session.commit()
    app.run(debug=True)
