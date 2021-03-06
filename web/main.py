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
import urllib
from google.appengine.ext import deferred
import random
import logging

from pizzablaster.models import User

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ONE_DAY = timedelta(days=1)
ONE_HOUR = timedelta(hours=1)
EASTERN = pytz.timezone('US/Eastern')
EMAIL_DELAY = timedelta(days=14)
ALEC_EMAIL = "alec.james.c@gmail.com"

def makeUser(name, score):
    u = User(
        name=name,
        score=score,
        real_score=score,
        email=name + "@gmail.com",
        liar=False
    )
    u.put()

def secsToTime(secs):
    return str(timedelta(seconds=secs)).zfill(8)

def userModelToLeaderboardUser(user):
    real_score = user.real_score

    if user.play_start and user.play_end:
        time_diff = int((user.play_end - user.play_start).total_seconds())
        real_score = min(real_score, time_diff)

    return {
        'name': user.name,
        'score': secsToTime(user.score),
        'real_score': secsToTime(real_score),
    }

def timeToSecs(time):
    score_times = time.split(":")
    score_times.reverse()

    seconds = minutes = hours = days = 0

    if len(score_times) > 0:
        seconds = int(score_times[0])
    if len(score_times) > 1:
        minutes = int(score_times[1])
    if len(score_times) > 2:
        hours = int(score_times[2])
    if len(score_times) > 3:
        days = int(score_times[3])

    score_delta = timedelta(
        seconds=seconds,
        minutes=minutes,
        hours=hours,
        days=days
    )

    score_seconds = score_delta.total_seconds()

    return int(score_seconds)

def formatTime(dt):
    return dt.strftime("%I:%M %p %Z on %b %d, %Y")

def sendEmail(user_id):
    user = ndb.Key(User, user_id).get()

    if user.play_id:
        logging.info(u"User was already emailed! {0}".format(user.email))
        return

    user.play_id = str(uuid.uuid4())
    user.email_date = datetime.utcnow()

    user.put()

    if user.email == ALEC_EMAIL:
        play_link = "http://pizzablaster.website/r/%s" % user.play_id
    else:
        play_link = "http://pizzablaster.website/go/%s" % user.play_id
    # play_link = "pizza://whatever?" + urllib.urlencode({'page': play_link_text})
    expiration_date = formatTime(datetime.now(EASTERN) + ONE_HOUR)

    address = "%s <%s>" % (user.name, user.email)

    subject = "It's time to play Pizza Blaster"

    template = JINJA_ENVIRONMENT.get_template('email.html')
    html = template.render({
        'name': user.name,
        'play_link': play_link,
        'verification_code': user.verification_code,
        'expiration_date': expiration_date
    })

    template = JINJA_ENVIRONMENT.get_template('email_plain.txt')
    body = template.render({
        'name': user.name,
        'play_link': play_link,
        'verification_code': user.verification_code,
        'expiration_date': expiration_date
    })

    mail.send_mail("admin@pizza-blaster.appspotmail.com", address, subject, body, html=html)

    logging.info(u"Sent email to {0}".format(address))

    return html


class IndexPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())

# class StartPage(webapp2.RequestHandler):
#     def get(self):
#         template = JINJA_ENVIRONMENT.get_template('start.html')
#         self.response.write(template.render())

class ChoicePage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('choice.html')
        self.response.write(template.render())

class VerifyRedirect(webapp2.RequestHandler):
    def get(self, play_id):
        url = "http://pizza-blaster.appspot.com/go/%s" % play_id
        self.redirect("pizza://whatever?" + urllib.urlencode({'page': url}))

class VerifyPage(webapp2.RequestHandler):
    def get(self, play_id):
        user = User.query(User.play_id == play_id).get()

        if not user:
            self.response.write("Invalid play id")
            return

        template = JINJA_ENVIRONMENT.get_template('verify.html')
        self.response.write(template.render())

    def post(self, play_id):
        user = User.query(User.play_id == play_id).get()

        if not user:
            self.response.write("Invalid play id")
            return

        verification_code = self.request.get('verification_code')

        if verification_code != user.verification_code:
            template = JINJA_ENVIRONMENT.get_template('verify.html')
            self.response.write(template.render({'error': 'Incorrect Verification Code'}))
            return

        self.redirect('/play/' + play_id)

class SignupPage(webapp2.RequestHandler):
    def get(self):
        # upload_url = blobstore.create_upload_url('/signup/submit')
        template = JINJA_ENVIRONMENT.get_template('signup.html')
        self.response.write(template.render({'upload_url': '/signup/submit'}))

    def post(self):
        email = self.request.get('email')

        existing_user = User.query(User.email == email).get()

        if existing_user and email != ALEC_EMAIL:
            template = JINJA_ENVIRONMENT.get_template('signup.html')

            # User already started the game
            if existing_user.play_start:
                self.response.write(template.render({'error': u"You have already played Pizza Blaster."}))
                return

            # User has not been emailed yet
            if not existing_user.play_id:
                self.response.write(template.render({'error': u"You have already signed up. Your email is on its way."}))
                return

        name = self.request.get('name')

        now = datetime.utcnow()
        delay = timedelta(seconds=random.randint(0, EMAIL_DELAY.total_seconds()))
        send_task_date = now + delay

        verification_code = str(User.query().count()).zfill(5)

        user = User(
            email=email,
            name=name,
            send_task_date=send_task_date,
            verification_code=verification_code
        )

        user.put()

        if user.email != ALEC_EMAIL:
            deferred.defer(sendEmail, user.key.id(), _eta=send_task_date)
        else:
            deferred.defer(sendEmail, user.key.id(), _countdown=45)

        template = JINJA_ENVIRONMENT.get_template('signup_success.html')
        self.response.write(template.render())

# class SignupSuccessPage(webapp2.RequestHandler):
#     def get(self):
#         template = JINJA_ENVIRONMENT.get_template('signup_success.html')
#         self.response.write(template.render())

class SorryPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('sorry.html')
        self.response.write(template.render())

# class SignupHandler(webapp2.RequestHandler):
#     def post(self):
#         email = self.request.get('email')
#         name = self.request.get('name')
#
#         now = datetime.utcnow()
#         delay = timedelta(seconds=random.randint(0, EMAIL_DELAY.total_seconds()))
#         send_task_date = now + delay
#
#         user = User(
#             email=email,
#             name=name,
#             send_task_date=send_task_date
#         )
#
#         user.put()
#
#         deferred.defer(sendEmail, user.key.id(), _eta=send_task_date)
#
#         self.redirect('/signup/success')

# class SignupHandlerBlob(blobstore_handlers.BlobstoreUploadHandler):
#     def post(self):
#         image_key = None
#         try:
#             upload = self.get_uploads()[0]
#             image_key = upload.key()
#         except:
#             pass
#
#         email = self.request.get('email')
#         name = self.request.get('name')
#
#         user = User(
#             email=email,
#             name=name,
#             image=image_key
#         )
#
#         user.put()
#
#         self.redirect('/signup/success')

class PlayPage(webapp2.RequestHandler):
    def get(self, play_id):
        user = User.query(User.play_id == play_id).get()

        if user is None:
            self.response.write("Invalid play id")
            return

        # if user.play_start:
        #     template = JINJA_ENVIRONMENT.get_template('error.html')
        #     self.response.write(template.render({'error': u"Sorry {0}. You can only play Pizza Blaster once.".format(user.email)}))
        #     return

        now = datetime.utcnow()
        expiration_date = user.email_date + ONE_HOUR

        if now > expiration_date:
            template = JINJA_ENVIRONMENT.get_template('expired.html')
            self.response.write(template.render({'error': u"Sorry {0}. Your game expired.".format(user.email)}))
            return

        user.play_start = now
        user.put()

        template = JINJA_ENVIRONMENT.get_template('play.html')
        self.response.write(template.render({'name': user.name, 'play_id': play_id}))

    def post(self, play_id):
        user = User.query(User.play_id == play_id, User.score == None).get()

        if user is None:
            self.redirect('/leaders')
            return

        score = int(self.request.get('input_score'))
        real_score = int(self.request.get('real_score'))
        user.play_end = datetime.utcnow()
        liar = False

        time_diff = (user.play_end - user.play_start).total_seconds()

        if score - real_score > 10:
            liar = True

        if score - time_diff > 10:
            liar = True

        user.real_score = real_score
        user.score = score
        user.liar = liar

        user.put()

        sleep(0.5)

        if liar:
            self.redirect('/liars')
        else:
            self.redirect('/leaders')

# class PlaySubmitPage(webapp2.RequestHandler):
#     def post(self, play_id):
#         user = User.query(User.play_id == play_id, User.score == None).get()
#
#         if user is None:
#             self.redirect('/leaders')
#             return
#
#         time = self.request.get('score')
#         score_seconds = timeToSecs(time)
#
#         user.score = score_seconds
#         user.play_end = datetime.utcnow()
#         user.put()
#
#         sleep(0.5)
#
#         self.redirect('/leaders')

class LeadersPage(webapp2.RequestHandler):
    def get(self):
        users = User.query(User.score > 0, User.liar == False).order(-User.score).fetch(100)

        render_users = map(userModelToLeaderboardUser, users)

        template = JINJA_ENVIRONMENT.get_template('leaders.html')
        self.response.write(template.render({'users': render_users}))

class LiarsPage(webapp2.RequestHandler):
    def get(self):
        users = User.query(User.score > 0, User.liar == True).order(-User.score).fetch(100)

        render_users = map(userModelToLeaderboardUser, users)

        template = JINJA_ENVIRONMENT.get_template('liars.html')
        self.response.write(template.render({'users': render_users}))


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

        html = sendEmail(user.key.id())

        self.response.write(u"Sent email to {0}<p>{1}".format(user.email, html))


class ImageHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)

class MakeUsersPage(webapp2.RequestHandler):
    def get(self):
        mike = User.query(User.name == "Mike").get()

        if mike is None:
            makeUser("Mike", 3600 + 45 * 60 + 20)
            makeUser("Uli", 17*60 + 18)
            makeUser("Tracy", 73)
            makeUser("Adrian F", 64)
            makeUser("Sara", 2*60 + 10)
            makeUser("Victor", 11)
            self.response.write("Wrote users!")
        else:
            self.response.write("Users already written")

app = webapp2.WSGIApplication([('/', IndexPage),
                            #    ('/start', StartPage),
                               ('/choice', ChoicePage),
                               ('/sorry', SorryPage),
                               ('/signup', SignupPage),
                            #    ('/signup/success', SignupSuccessPage),
                            #    ('/signup/submit', SignupHandler),
                               ('/image/([^/]+)?', ImageHandler),
                               ('/r/([^/]+)?', VerifyRedirect),
                               ('/go/([^/]+)?', VerifyPage),
                               ('/play/([^/]+)?', PlayPage),
                            #    ('/submit/([^/]+)?', PlaySubmitPage),
                               ('/leaders', LeadersPage),
                               ('/liars', LiarsPage),
                               ('/make_users', MakeUsersPage),
                               ('/send/([^/]+)?', SendPage)
                              ], debug=True)
