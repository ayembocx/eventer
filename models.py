from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model): 
    user_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(24), nullable=False)
    pw_hashed = db.Column(db.String(64), nullable=False)

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
