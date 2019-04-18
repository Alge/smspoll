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

define("port", default=8888, help="run on the given port", type=int)

# we gonna store clients in dictionary..
clients = dict()

def update_all_pollclients(poll):
    print("Clients")
    pprint.pprint(clients)
    for client in clients[poll.id]:
        send_update(poll, client)

def send_update(poll, client):
    try:
        print("Sending update to client: {} with poll: {}".format(client, poll.id))
        data = {"result": "success", "type": "poll", "data":poll.to_dict()}
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
            if not poll:
                self.write("No poll with that number")
            else:
                if poll.add_answer(sms["message"], sms["from"]):
                    self.write("Success")
                    update_all_pollclients(poll)
                else:
                    self.write("Failed to add answer")
        except Exception as e:
            print(e)
            self.write("Failed tot parse request")

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

        self.render("templates/poll.html", poll = poll)

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
                self.write_message(json.dumps({"result": "success", "message": "subscribed to poll"}))
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
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
