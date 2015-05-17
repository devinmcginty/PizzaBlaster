from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore, ndb
import webapp2
import os
import jinja2
import uuid
from datetime import datetime, timedelta
from google.appengine.api import mail
from time import sleep
import pytz

from pizzablaster.models import User

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ONE_DAY = timedelta(days=1)
ONE_HOUR = timedelta(hours=1)
VERIFICATION_CODE = '00023'
EASTERN = pytz.timezone('US/Eastern')


class IndexPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())

class ChoicePage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('choice.html')
        self.response.write(template.render())

class VerifyPage(webapp2.RequestHandler):
    def get(self, play_id):
        template = JINJA_ENVIRONMENT.get_template('verify.html')
        self.response.write(template.render())

    def post(self, play_id):
        verification_code = self.request.get('verification_code')

        if verification_code != VERIFICATION_CODE:
            template = JINJA_ENVIRONMENT.get_template('verify.html')
            self.response.write(template.render({'error': True}))
            return

        self.redirect('/play/' + play_id)

class SignupPage(webapp2.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/signup/submit')
        template = JINJA_ENVIRONMENT.get_template('signup.html')
        self.response.write(template.render({'upload_url': upload_url}))

class SignupSuccessPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('signup_success.html')
        self.response.write(template.render())

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

        self.redirect('/signup/success')

class PlayPage(webapp2.RequestHandler):
    def get(self, play_id):
        user = User.query(User.play_id == play_id).get()

        if user is None:
            template = JINJA_ENVIRONMENT.get_template('play.html')
            self.response.write(template.render({'name': 'not a person', 'play_id': play_id}))
            # self.response.write("invalid user")
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

        play_link = "http://pizza-blaster.appspot.com/go/%s" % user.play_id
        verification_code = '00023'
        expiration_date = (datetime.now(EASTERN) + ONE_HOUR).strftime("%I:%M %p on %b %d, %Y")

        address = "%s <%s>" % (user.name, user.email)

        subject = "It's time to play Pizza Blaster"

        template = JINJA_ENVIRONMENT.get_template('email.html')
        html = template.render({
            'name': user.name,
            'play_link': play_link,
            'verification_code': verification_code,
            'expiration_date': expiration_date
        })

        template = JINJA_ENVIRONMENT.get_template('email_plain.txt')
        body = template.render({
            'name': user.name,
            'play_link': play_link,
            'verification_code': verification_code,
            'expiration_date': expiration_date
        })

        mail.send_mail("admin@pizza-blaster.appspot.com", address, subject, body, html=html)
        self.response.write("Sent! <p> " + address + "<p>" + html + "<p>" + play_link)


class ImageHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)


app = webapp2.WSGIApplication([('/', IndexPage),
                               ('/choice', ChoicePage),
                               ('/sorry', SorryPage),
                               ('/signup', SignupPage),
                               ('/signup/success', SignupSuccessPage),
                               ('/signup/submit', SignupHandler),
                               ('/image/([^/]+)?', ImageHandler),
                               ('/go/([^/]+)?', VerifyPage),
                               ('/play/([^/]+)?', PlayPage),
                               ('/submit/([^/]+)?', PlaySubmitPage),
                               ('/leaders', LeadersPage),
                               ('/send/([^/]+)?', SendPage)
                              ], debug=True)
