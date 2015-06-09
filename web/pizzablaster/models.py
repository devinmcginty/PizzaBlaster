from google.appengine.ext import ndb

class User(ndb.Model):
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)

    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    image = ndb.BlobKeyProperty()

    send_task_date = ndb.DateTimeProperty(required=True)

    play_id = ndb.StringProperty()
    verification_code = ndb.StringProperty()
    email_date = ndb.DateTimeProperty()

    score = ndb.IntegerProperty()
    real_score = ndb.IntegerProperty()
    play_start = ndb.DateTimeProperty()
    play_end = ndb.DateTimeProperty()

    liar = ndb.BooleanProperty()


class Email(ndb.Model):
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)

    email = ndb.StringProperty(required=True)
