from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 
from hashutils import make_pw_hash, check_pw_hash, make_salt

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
app.static_folder = 'static'
db = SQLAlchemy(app)

app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    blog_title = db.Column(db.String(120))
    blog_body = db.Column(db.String(500))
    blog_date = db.Column(db.DateTime, nullable=False,
        default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))    
    

    def __init__(self, blog_title, blog_body, owner):
       
        self.blog_title = blog_title 
        self.blog_body = blog_body 
        self.owner = owner
          
         
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'list_blogs', 'index', 'portfolio', 'static']
    # 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/portfolio')

@app.route('/portfolio', methods=['GET', 'POST'])
def folio():
    return render_template('portfolio.html')

@app.route('/', methods=['GET', 'POST'])        
def index(): 
    users = User.query.all()
    existing_blogs = Blog.query.all()
    return render_template('index.html', users=users, existing_blogs=existing_blogs)  

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            flash("Logged in", 'info')
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'danger')
    else: 
        #flash('User password incorrect, or user does not exist', 'danger')
        return render_template('login.html')  


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        # todo - validate user's data

        existing_user = User.query.filter_by(username=username).all()
        
        if username == '':
            username = ''
            flash('Username blank, please enter a valid username greater than 2 characters without spaces.', 'danger')

        elif ' ' in username or len(username) < 3:
            username = ''
            flash('Username invalid, please enter a valid username greater than 2 characters without spaces.', 'danger')

        elif password == '':
            password = ''
            flash('Password blank, please enter a valid username greater than 2 characters without spaces.', 'danger')

        elif ' ' in password or len(password) < 3:
            password = ''
            flash('Username invalid, please enter a valid username greater than 2 characters without spaces.', 'danger')

        elif verify == '' or verify != password: 
            verify = ''
            flash('Passwords do not match', 'danger')  

        elif username == existing_user: 
            flash('User already exists', 'danger')

        elif not existing_user and password == verify:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            flash("Logged in", 'info')
            return redirect('/newpost')
      
    return render_template("signup.html") 
    

@app.route('/logout', methods=['POST'])
def logout():
    del session['username']
    return redirect('/blog')


@app.route('/blog', methods=['POST', 'GET'])
def list_blogs():

    blog_id = request.args.get('id')
    blog_user = request.args.get('user')

    if request.args.get('user') is not None:
        user = User.query.filter_by(username=str(blog_user)).all()
        user_id = user[0].id
        user_blogs = Blog.query.join(User).filter(Blog.owner_id==user_id).all()
        username = user[0].username
        
        return render_template('singleUser.html', 
                username=username, user_blogs=user_blogs, blog_user=blog_user)

    if request.args.get('id') is not None: 
        
        blog = Blog.query.get(blog_id)  
        blog_title = blog.blog_title
        blog_body = blog.blog_body
        owner_id = blog.owner_id
        owner = blog.owner
        user_name = blog.owner.username

        return render_template('id_blog.html', 
            blog_body=blog_body, blog_title=blog_title, 
            owner_id=owner_id, owner=owner, 
            blog_id=blog_id, user_name=user_name)
    
    else: 
        existing_blogs = Blog.query.order_by(Blog.blog_date.desc()).all()
        
        return render_template('blog.html', 
            existing_blogs=existing_blogs)
    


@app.route('/newpost', methods=['GET', 'POST'])
def newpost(): 
    owner = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        
        blog_title = request.form['blog_title']
        blog_body = request.form['blog_body']
        newpost = Blog(blog_title, blog_body, owner) 
        db.session.add(newpost)
        db.session.commit()
        db.session.flush()
        blog_id = newpost.id
        owner_id = newpost.owner_id
        
        
        # add code to test if blog entry, body & title, are empty. Return error message and newpost form.

        if blog_title == '' or blog_body == '': 
            flash('Oops! You forgot to input a Title for your piece.', 'danger')
            flash('Oops! You forgot to jot down your next masterpiece.', 'danger')
            #title_error = 'Oops! You forgot to input a Title for your piece.'
            #body_error = 'Oops! You forgot to jot down your next masterpiece.'

            return render_template('newpost.html', 
                blog_title=blog_title, blog_body=blog_body)

        else: 
            
            blog_id = newpost.id
            return redirect('/blog?id={0}'.format(blog_id))

    else: 
            
        return render_template('newpost.html')

if __name__ == '__main__':
    app.run()
