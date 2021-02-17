import time
import os
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

#from models import db, User, Event

app = Flask(__name__)

#configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'events.db')

#app.config.from_object(__name__)
#app.config.from_envvar('EVENTS_SETTINGS', silent=True)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #silence deprecation warning
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://akacuggfuggebg:b3bec0e1d92f2a7e973f1fe974838d349655a605b71ffdb66a6ae732ae394a13@ec2-34-192-58-41.compute-1.amazonaws.com:5432/doairivml5hh9'

db = SQLAlchemy(app)


class User(db.Model): 
    user_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(24), nullable=False)
    pw_hashed = db.Column(db.String(24), nullable=False)

    #1 to many with host and events
    #many to many with attendees and events

    def __init__(self,username,pw_hashed):
        self.username = username
        self.pw_hashed = pw_hashed
    
    def __repr__(self):
        return '<User {}>'.format(self.username)


#association table for events and attendees
attendees = db.Table('attendees',
    db.Column('attendee_id',db.Integer,db.ForeignKey('user.user_id')),
    db.Column('event_id',db.Integer,db.ForeignKey('event.event_id'))
)

#event has host id which we use to check if we can delete event
#to check users in event we use attendees relationship
class Event(db.Model):
    event_id = db.Column(db.Integer,primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.user_id'),nullable=False)
    title = db.Column(db.Text,nullable=False)
    description = db.Column(db.Text,nullable=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    attendees = db.relationship('User',secondary=attendees,backref=db.backref('event',lazy='dynamic'),lazy='dynamic')

    def __init__(self,host_id,title,description,start_date,end_date):
        self.host_id = host_id
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
            return '<Event {}>'.format(self.event_id)
    

def get_userId(username):
    rv = User.query.filter_by(username=username).first()
    return rv.user_id if rv else None

def get_eventId(title):
    rv = Event.query.filter_by(title=title).first()
    return rv.event_id if rv else None


def format_date(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


@app.before_request
def before_request():
    g.user=None
    if 'user_id' in session: 
        g.user = User.query.filter_by(user_id=session['user_id']).first()

@app.route('/')
def mainPage(): 
    #main page of app, if not logged in will just show all events
    #if logged in it will also show list of events user is registered for
    #u = User.query.filter_by(user_id=session['user_id']).first()

    return render_template('mainPage.html',events=Event.query.order_by(Event.start_date).all(),users=User.query.order_by(User.user_id))

@app.route('/<event_id>/attend')
def attend_event(event_id): 
    if not g.user: #if not logged in exit
        abort(401)

    if event_id is None: #if event id doesnt exist exit
        abort(404)
    
    #since event id exists get event
    event = Event.query.filter_by(event_id=event_id).first()

    #check if user trying to attend is host
    if g.user.user_id == event.host_id:
        abort(401)

    #everything here doesnt work yet
    attendeeList = event.attendees.filter_by(user_id=g.user.user_id).all()

    

    for u in attendeeList:
        if g.user.user_id == u.user_id:
            flash('You were already attending that event!')
            return redirect(url_for('mainPage'))

   
    event.attendees.append(g.user)
        #commit to database
    db.session.commit()
    flash('You are now registered for this event')
    return redirect(url_for('mainPage'))


  

    



@app.route('/<event_id>')
def cancel_event(event_id): 
    if not g.user: #if not logged in exit
        abort(401)

    if event_id is None: #if event id doesnt exist exit
        abort(404)


    #since event id exists get event
    event = Event.query.filter_by(event_id=event_id).first()

    #check if user trying to cancel is not host
    #if g.user.user_id != event.host_id:  
        #abort(401)


    return render_template('cancel_confirm.html',event=event)


@app.route('/<event_id>/cancel')
def cancel_confirm(event_id):
    Event.query.filter_by(event_id=event_id).delete()
    db.session.commit()
    flash('You have canceled the existence of this event')
    return redirect(url_for('mainPage'))



@app.route('/create_event', methods=['GET','POST'])
def create_event(): 
    if 'user_id' not in session: 
        abort(401)
    if request.method == 'POST':
        if not request.form['title']:
            error = 'No title given'
            return render_template('create_event.html',error=error)

        if not request.form['start-time']:
            error = 'No start date'
            return render_template('create_event.html',error=error)
        
        if not request.form['end-time']:
            error = 'No end date'
            return render_template('create_event.html',error=error)
        
        startdt = datetime.strptime(request.form['start-time'], '%Y-%m-%dT%H:%M')
        enddt = datetime.strptime(request.form['end-time'], '%Y-%m-%dT%H:%M')
        
      

        db.session.add(Event(session['user_id'],request.form['title'],request.form['description'],startdt,enddt))
        
        db.session.commit()
        flash("You have created a new event")
        return redirect(url_for('mainPage'))
    return render_template('create_event.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('mainPage'))
    error=None
    if request.method == 'POST':

        user = User.query.filter_by(username=request.form['username']).first()
        if user is None:
            error = 'Invalid username'
        elif request.form['password'] != user.pw_hashed:
            error = 'Invalid password'
        else:
            flash("You have been logged in!")
            session['user_id'] = user.user_id
            return redirect(url_for('mainPage'))
    return render_template('login.html',error=error)


@app.route('/register', methods=['GET','POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('mainPage'))
    error=None

    if request.method == 'POST':
        if not request.form['username']:
            error = 'Please enter a username'
        elif not request.form['password']:
            error = 'Please enter a password'
        elif get_userId(request.form['username']) is not None:
            error = 'Username not available'
        else:
            db.session.add(User(request.form['username'],request.form['password']))
            db.session.commit()
            flash('You have registered an account and can log in now!')
            return redirect(url_for('mainPage'))
    return render_template('register.html',error=error)


@app.route('/logout/')
def logout():
    flash("You have logged out")
    session.pop('user_id',None)
    return redirect(url_for('mainPage'))


#add filters to jinja
app.jinja_env.filters['datetimeformat'] = format_date