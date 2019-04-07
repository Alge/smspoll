from flask import Flask
from flask import render_template
from flask import request
import peewee

from models import Poll
from models import User
from models import Choice
from models import Answer

db = peewee.SqliteDatabase("db.sqlite")

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template("base.html", message="Hejsan!!")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create_poll", methods=['GET'])
def create_poll():
    return render_template("create_poll.html")

@app.route("/create_poll", methods=['POST'])
def submit_poll():
    return render_template("create_poll.html")


@app.route("/poll/<poll_id>")
def show_poll(poll_id):
    print("Trying to show poll: {}".format(poll_id))
    poll = Poll.get_or_none(Poll.uid == poll_id)
    if not poll:
        return render_template('error.html', code=404, message="Poll not found"), 404

    return render_template("show_poll.html", poll=poll)

@app.route("/sms_in", methods = ['POST'])
def sms_in():
    f = request.form.get('from')
    t = request.form.get('to')
    m = request.form.get('message')

    poll = Poll.get_or_none(Poll.number==t)
    if not poll:
        words = m.split(" ")
        if len(words) >= 2:
            poll = Poll.get_or_none(Poll.number=="{}{}".format(t, words[0].upper()))
    if not poll: # Still no poll found 
        return "No such poll found"
    result = poll.add_answer(m, f)

    if result == True:
        return poll.answer_response

    print("Yay, got an SMS; from: {}, to: {}, message: {}".format(f, t, m))
    return ""

if __name__ == "__main__":
  app.run()
