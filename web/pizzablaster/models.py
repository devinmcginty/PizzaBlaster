from google.appengine.ext import ndb

class User(ndb.Model):
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)

    name = ndb.StringProperty()
    email = ndb.StringProperty(required=True)
    image = ndb.BlobKeyProperty()

    play_id = ndb.StringProperty()
    email_date = ndb.DateTimeProperty()

    score = ndb.IntegerProperty()
    play_start = ndb.DateTimeProperty()
    play_end = ndb.DateTimeProperty()
