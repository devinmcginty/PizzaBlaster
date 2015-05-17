import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from pizzablaster import models

package = 'Hello'


class NewUser(messages.Message):
    """Greeting that stores a message."""
    email = messages.StringField(1, required=True)
    image = messages.BytesField(2)

 class User(messages.Message):
     key = messages.StringField(1, required=True)
    #  email = messages.StringField(1, required=True)

 class NewUserResponse(messages.Message):
     success = messages.BooleanField(1, required=True)
     error = messages.StringField(2)


class GreetingCollection(messages.Message):
  """Collection of Greetings."""
  items = messages.MessageField(Greeting, 1, repeated=True)


STORED_GREETINGS = GreetingCollection(items=[
  Greeting(message='hello world!'),
  Greeting(message='goodbye world!'),
])


@endpoints.api(name='pizzablaster', version='v1')
class PizzaBlasterApi(remote.Service):
  """Helloworld API v1."""

  @endpoints.method(message_types.VoidMessage, GreetingCollection,
                    path='hellogreeting', http_method='GET',
                    name='greetings.listGreeting')
  def lead(self, unused_request):
    return STORED_GREETINGS

  NEW_USER_RESOURCE = endpoints.ResourceContainer(
      message_types.VoidMessage,
      times=messages.IntegerField(2, variant=messages.Variant.INT32,
                                  required=True))

  @endpoints.method(NewUser, User,
                    path='users', http_method='POST',
                    name='users.new')
  def new_user(self, request):
      user = models.User(email=)
    return Greeting(message=request.message * request.times)

  ID_RESOURCE = endpoints.ResourceContainer(
      message_types.VoidMessage,
      id=messages.IntegerField(1, variant=messages.Variant.INT32))

  @endpoints.method(ID_RESOURCE, Greeting,
                    path='hellogreeting/{id}', http_method='GET',
                    name='greetings.getGreeting')
  def greeting_get(self, request):
    try:
      return STORED_GREETINGS.items[request.id]
    except (IndexError, TypeError):
      raise endpoints.NotFoundException('Greeting %s not found.' %
                                        (request.id,))


APPLICATION = endpoints.api_server([HelloWorldApi])
