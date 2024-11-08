import requests

import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options, parse_command_line

import json
import os

import pprint

from models import Poll
from models import Choice
from models import Answer

from models import get_db

db = get_db()

define("port", default=7445, help="run on the given port", type=int)
define("hostname", default="poll.alge.se", help="domain that the server is reachable on", type=str)

# we gonna store clients in dictionary..
clients = dict()

def update_all_pollclients(poll):
    if poll.id in clients:
      for client in clients[poll.id]:
          send_update(poll, client)

def send_update(poll, client):
    try:
        print("Sending update to client: {} with poll: {}".format(client, poll.id))
        data = {"type": "poll", "data":poll.to_dict()}
        client.write_message(json.dumps(data))
    except:
        print("failed to send update")
        client.close()

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        #self.write("This is your response")
        polls = Poll.select()
        self.render("templates/index.html", polls = polls)
        #we don't need self.finish() because self.render() is fallowed by self.finish() inside tornado
        #self.finish()

class IncomingSMSHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            sms = {}
            sms["to"] = self.get_argument("to")
            sms["from"] = self.get_argument("from")
            sms["message"] = self.get_argument("message")
            poll = Poll.get_or_none(Poll.number == sms["to"])
            if poll is None:
                print("No poll with that number")
                #self.write("No poll with that number")
            else:
                if poll.add_answer(sms["message"], sms["from"]):
                    #self.write("Success")
                    update_all_pollclients(poll)
                else:
                    pass
                    #self.write("Failed to add answer")
        except Exception as e:
            print(f"Failed parsing request: {e}")
            raise e
            #self.write("Failed to parse request")

        self.finish()

    def get(self):
        self.write("Use a POST request!")
        self.finnish()

class CreatePollHandler(tornado.web.RequestHandler):
    def post(self):
        print(self.get_arguments("name"))
        pprint.pprint(self.request.arguments)
        self.redirect("/")
    def get(self):
        polls = Poll.select()
        self.render("templates/create_poll.html", polls = polls)

class PollHandler(tornado.web.RequestHandler):
    def get(self, poll_id):
        poll = Poll.get_or_none(Poll.id==poll_id)
        if poll == None:
            raise tornado.web.HTTPError(404)

        self.render("templates/poll.html", poll=poll, hostname=options.hostname)

class PollSocketHandler(tornado.websocket.WebSocketHandler):
    #def __init__(self):
    #    tornado.websocket.WebSocketHandler.__init__(self)
    #    self.subscriptions = []

    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened for poll")
        self.subscriptions = []

    def on_message(self, message):
        print("Message recieved: {}".format(message))

        data = {}
        try:
            data = json.loads(message)

        except:
            self.write_message(json.dumps({"error":"not valid json"}))

        if "subscribe_poll" in data.keys():
            poll = Poll.get_or_none(Poll.id == data["subscribe_poll"])
            if not poll:
                self.write_message(json.dumps({"result": "error", "message": "unable to find poll with id: {}".format(data["subscribe_poll"])}))
            else:
                self.subscriptions.append(poll)
                if poll.id not in clients.keys():
                    clients[poll.id] = []
                clients[poll.id].append(self)
                r = {
                        'type': 'response',
                        'response': 'success',
                        'message': "subscribed to poll {}".format(poll.id)
                    }
                self.write_message(json.dumps(r))
                send_update(poll, self)
        else:
            self.write_message(json.dumps({"error":"unknown command"}))

    def on_close(self):
        for poll in self.subscriptions:
            clients[poll.id].remove(self)
        print("WebSocket closed")

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "login_url": "/login",
    # "xsrf_cookies": True,
    "debug": True
}

app = tornado.web.Application(
    [
        (r'/', IndexHandler),
        (r'/create_poll', CreatePollHandler),
        (r'/sms_in', IncomingSMSHandler),
        (r'/poll/(?P<poll_id>\w+)', PollHandler),
        (r'/sockets/poll', PollSocketHandler),
    ],
    **settings
)

if __name__ == '__main__':
    parse_command_line()
    print(f"Starting server on port {options.port}")
    try:
      # Force use of ipv4
      requests.packages.urllib3.util.connection.HAS_IPV6 = False
      external_ip = requests.get('https://ident.me', timeout=1).text
    except Exception as e:
      print(f"Failed fetching external IP: {e}")
      external_ip = "127.0.0.1"

    print(f"Configure incoming SMS to be sent to: https://{options.hostname}/sms_in and make sure your ports are open!")


    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
