from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore, ndb
import webapp2
import os
import jinja2
import uuid
from datetime import datetime, timedelta
from google.appengine.api import mail
from time import sleep

from pizzablaster.models import User

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ONE_DAY = timedelta(days=1)

class IndexPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())

class SignupPage(webapp2.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/signup/submit')
        template = JINJA_ENVIRONMENT.get_template('signup.html')
        self.response.write(template.render({'upload_url': upload_url}))

class SorryPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('sorry.html')
        self.response.write(template.render())

class SignupHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        image_key = None
        try:
            upload = self.get_uploads()[0]
            image_key = upload.key()
        except:
            pass

        email = self.request.get('email')
        name = self.request.get('name')

        user = User(
            email=email,
            name=name,
            image=image_key
        )

        user.put()

        self.redirect("/")

class PlayPage(webapp2.RequestHandler):
    def get(self, play_id):
        user = User.query(User.play_id == play_id).get()

        if user is None:
            self.response.write("invalid user")
            return

        now = datetime.utcnow()
        delta = user.email_date - now

        if delta > ONE_DAY:
            self.response.write("too late!")
            return

        user.play_start = now
        user.put()

        template = JINJA_ENVIRONMENT.get_template('play.html')
        self.response.write(template.render({'name': user.name, 'play_id': play_id}))

class PlaySubmitPage(webapp2.RequestHandler):
    def post(self, play_id):
        user = User.query(User.play_id == play_id, User.score == None).get()

        if user is None:
            self.response.write("invalid user")
            return

        score = self.request.get('score')

        try:
            score = int(score)
        except:
            score = 0

        user.score = score
        user.play_end = datetime.utcnow()
        user.put()

        sleep(0.5)

        self.redirect('/leaders')

class LeadersPage(webapp2.RequestHandler):
    def get(self):
        users = User.query(User.score != None).order(-User.score).fetch(5)

        template = JINJA_ENVIRONMENT.get_template('leaders.html')
        self.response.write(template.render({'users': users}))

class SendPage(webapp2.RequestHandler):
    def get(self, email):
        print "Email: " + email
        if not mail.is_email_valid(email):
            self.response.write("bad email")
            return

        user = User.query(User.email == email, User.play_id == None).get()

        if user is None:
            self.response.write("no user")
            return

        template = JINJA_ENVIRONMENT.get_template('send.html')
        self.response.write(template.render({'email': user.email, 'name': user.name}))

    def post(self, email):
        if not mail.is_email_valid(email):
            self.response.write("bad email")
            return

        user = User.query(User.email == email, User.play_id == None).get()

        if user is None:
            self.response.write("no user")
            return

        user.play_id = str(uuid.uuid4())
        user.email_date = datetime.utcnow()

        user.put()

        play_link = "http://localhost:8080/play/%s" % user.play_id

        address = "%s <%s>" % (user.name, user.email)

        subject = "It's time to play Pizza Blaster"
        body = """
Congratulations, %s!

It's your turn to play Pizza Blaster.

Click this link: %s
""" % (user.name, play_link)

        mail.send_mail("adrienip@gmail.com", address, subject, body)
        self.response.write("Sent! <p> " + address + "<p>" + body + "<p>" + play_link)


class ImageHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)


app = webapp2.WSGIApplication([('/', IndexPage),
                               ('/sorry', SorryPage),
                               ('/signup', SignupPage),
                               ('/signup/submit', SignupHandler),
                               ('/image/([^/]+)?', ImageHandler),
                               ('/play/([^/]+)?', PlayPage),
                               ('/submit/([^/]+)?', PlaySubmitPage),
                               ('/leaders', LeadersPage),
                               ('/send/([^/]+)?', SendPage)
                              ], debug=True)
