import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options, parse_command_line

import json

import pprint

from models import Poll
from models import Choice
from models import Answer

from models import get_db

db = get_db()

define("port", default=8888, help="run on the given port", type=int)

# we gonna store clients in dictionary..
clients = dict()

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        #self.write("This is your response")
        polls = Poll.select()
        self.render("templates/index.html", polls = polls)
        #we don't need self.finish() because self.render() is fallowed by self.finish() inside tornado
        #self.finish()

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
    def open(self):
        print("WebSocket opened for poll")

    def on_message(self, message):
        print("Message recieved: {}".format(message))

        data = {}
        try:
            data = json.loads(message)

        except:
            self.write_message(json.dumps({"error":"not valid json"}))

        if "subscribe" in data.keys():
            self.write_message(json.dumps({"success":"subscribed to poll"}))

        else:
            self.write_message(json.dumps({"error":"unknown command"}))

    def on_close(self):
        print("WebSocket closed")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print("WebSocket closed")

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/', WebSocketHandler),
    (r'/create_poll', CreatePollHandler),
    (r'/poll/(?P<poll_id>\w+)', PollHandler),
    (r'/sockets/poll', PollSocketHandler),
], debug=True)

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
