from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from flask_migrate import Migrate
from flask import render_template
from flask import Flask, session, redirect, url_for, request
import datetime
from flask_login import LoginManager,login_user,UserMixin
from sqlalchemy import create_engine
engine = create_engine('mysql://root:root@localhost/postdata', echo=True)
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
login_manager = LoginManager()
login_manager.init_app(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:root@localhost/postdata"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))
    created_at = db.Column(db.TIMESTAMP())
    posts = db.relationship("Post", backref='user',lazy=True)
    comments = db.relationship("Comment", backref='user',lazy=True)
    replies = db.relationship("Reply", backref='user',lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    title = db.Column(db.String(11))
    body = db.Column(db.Text(120))
    created_at = db.Column(db.TIMESTAMP())
    comments=db.relationship("Comment",backref="post",lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer,db.ForeignKey("post.id"),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    body = db.Column(db.Text(80))
    created_at = db.Column(db.TIMESTAMP())
    replies=db.relationship("Reply",backref="comment",lazy=True)
    @property
    def serialize(self):
       return {
           'id'         : self.id,
           'modified_at': self.created_at,
           'user_id'  : self.user_id,
           'body':self.body,
           'post_id':self.post_id,
       }

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    comment_id = db.Column(db.Integer,db.ForeignKey('comment.id'),nullable=False)
    body = db.Column(db.Text(80))
    created_at = db.Column(db.TIMESTAMP())
    @property
    def serialize(self):
       return {
           'id'         : self.id,
           'created_at': self.created_at,
           'user_id'  : self.user_id,
           'body':self.body,
           'comment_id':self.comment_id,
       }


from app import User

@app.route("/register",methods=('GET','POST'))
def register():
    ses = Session()
    if request.method=="POST":
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        confirm_password=request.form['password_confirm']
        currentDT = datetime.datetime.now()
        ins = User(username=username,email=email,password=password,created_at=currentDT)
        db.session.add(ins)
        db.session.commit()
        ses.close()
    return render_template('register.html')

@app.route("/",methods=('GET','POST'))
def main_view():
	return render_template('main_page.html',result="hey")

@app.route("/login",methods=('GET','POST'))
def login():
    ses = Session()
    if request.method=="POST":
        post=ses.query(Post).all()
        username=request.form['username']
        password=request.form['password']
        our_user = ses.query(User).filter_by(username=username).first()
        ses.close()
        if our_user is not None:
            login_user(our_user)
            return render_template('index.html',result=post)
    return render_template('login.html')

@app.route("/list",methods=('GET','POST'))
def list():
    ses = Session()
    post = ses.query(Post).all()
    if request.method=="POST":
        title=request.form['title']
        post_content=request.form['post_content']
        user_id=request.form['user_id']
        currentDT = datetime.datetime.now()
        ins = Post(user_id=user_id,title=title,body=post_content,created_at=currentDT)
        db.session.add(ins)
        db.session.commit()
        post = ses.query(Post).all()
        ses.close()
    return render_template("index.html",result=post)

@app.route("/detail/<id>",methods=('GET','POST'))
def detail(id):
    ses = Session()
    post=ses.query(Post).filter_by(id=id).first()
    ses.close()
    return render_template("detail.html",result=post)

@app.route("/create",methods=('GET','POST'))
def create():
    user_id=request.form['user_id']
    post_id=request.form['post_id']
    comment_text=request.form['comment_text']
    currentDT = datetime.datetime.now()
    ins = Comment(user_id=user_id,post_id=post_id,body=comment_text,created_at=currentDT)
    ses = Session()
    db.session.add(ins)
    db.session.commit()
    comments=ses.query(Comment).filter_by(post_id=post_id).all()
    ses.close()
    if comments is not None:    
        list=[x.serialize for x in comments]
        return jsonify(
            result=list
            )
    return render_template('detail.html')

@app.route("/comment",methods=('GET','POST'))
def comment():
    ses = Session()
    post_id=request.form['post_id']
    comments=ses.query(Comment).filter_by(post_id=post_id).all()
    user=[]
    for x in comments:
        user_id=x.serialize['user_id']
        user.append(ses.query(User).filter_by(id=user_id).first().username)
        # names=[x.serialize for x in comments]
    if comments is not None:    
        list=[x.serialize for x in comments]
        return jsonify(
            result=[list,user]
        )
    return render_template('detail.html')

@app.route("/reply",methods=('GET','POST'))
def reply():
    comment_id=request.form['comment_id']
    reply_content=request.form['reply_content']
    user_id=request.form['current_user']
    currentDT = datetime.datetime.now()
    ses = Session()
    reply=Reply(comment_id=comment_id,user_id=user_id,body=reply_content,created_at=currentDT)
    ses.add(reply)
    ses.commit()
    reply=ses.query(Reply).order_by(Reply.id.desc()).filter_by(comment_id=comment_id).first()
    user_pk=ses.query(Reply).order_by(Reply.id.desc()).filter_by(comment_id=comment_id).first().user_id
    user=ses.query(User).filter_by(id=user_pk).first().username
    ses.close()
    if reply is not None:
        list=reply.serialize
        return jsonify(
            result=[list,user]
        )
    return render_template('detail.html')

@app.route("/replyall",methods=('GET','POST'))
def replyall():
    comment_id=request.form['comment_id']
    ses = Session()
    reply=ses.query(Reply).filter_by(comment_id=comment_id).all()
    user=[]
    for x in reply:
        user_id=x.serialize['user_id']
        print(user_id)
        user.append(ses.query(User).filter_by(id=user_id).first().username)
    ses.close()
    if reply is not None:
        list=[x.serialize for x in reply]
        return jsonify(
                result=[list,user]
            )
    return render_template('detail.html')



if __name__ == '__main__':
    app.run()