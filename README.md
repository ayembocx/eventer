# eventer
An Event Tracking Web Application written by Ayem Kpenkaan to get familiar with Python and deploying full stack applications

Allows users with accounts to create new events, provide details on events as well as view all other events by other users and even sign up for said events

Web stack of Postgresql, Python with Flask Framework for Routing, Css, Html

For local deployment on windows 
1. Clone repo
2. Modify app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'events.db')
3. Set app by typing in CLI SET FLASK_APP = events.py
4. Initialize Database by typing in CLI flask initdb
5. Run web app by typing in CLI flask run

To view hosted web app visit
https://eventerbyayem.herokuapp.com/

