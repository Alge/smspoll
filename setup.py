from models import Poll, Choice, Answer, User
from models import create_db
from models import get_db
import os.path

db = get_db()


# Check if the DB file exists, if not, create it
if not os.path.isfile("db.sqlite"):
    create_db()

    # Lets add some sample data too

    u = User()
    u.displayname = "Testkonto 1"
    u.email = "test1@example.com"
    u.password = "supersecret"
    u.save()

    p1 = Poll()
    p1.name = "Testpoll 1"
    p1.number = "+46766862842"
    p1.allow_duplicate_answers = True
    p1.allow_multiple_choices = True
    p1.owner = u
    p1.save()

    c1 = Choice()
    c1.poll = p1
    c1.name = "01"
    c1.description = "Bidrag nr. 1 - Bä bä vita lamm"
    c1.save()

    c2 = Choice()
    c2.poll = p1
    c2.name = "02"
    c2.description = "Bidrag nr. 2 - Blinka lilla stjärna"
    c2.save()

    c3 = Choice()
    c3.poll = p1
    c3.name = "03"
    c3.description = "Bidrag nr. 3 - Björnen sover"
    c3.save()

    c4 = Choice()
    c4.poll = p1
    c4.name = "04"
    c4.description = "Bidrag nr. 4 - Små grodorna"
    c4.save()

    # Some answers
    p1.add_answer("01", "+46700000001")
    p1.add_answer("02", "+46700000002")
    p1.add_answer("01", "+46700000003")
    p1.add_answer("02", "+46700000004")
    p1.add_answer("01", "+46700000005")
