import peewee
import sys
import datetime


database = peewee.SqliteDatabase("db.sqlite")

class BaseModel(peewee.Model):
    class Meta:
        database = database

class User(BaseModel):
    displayname = peewee.CharField()
    email = peewee.CharField(unique=True)
    password = peewee.CharField()
    created = peewee.DateTimeField(default=datetime.datetime.utcnow())

class Poll(BaseModel):
    name = peewee.CharField()
    description = peewee.CharField(default="")
    number = peewee.CharField(unique=True)
    owner = peewee.ForeignKeyField(User, backref="polls")
    created = peewee.DateTimeField(default=datetime.datetime.utcnow())
    public = peewee.BooleanField(default=True)
    published = peewee.DateTimeField(default=datetime.datetime.utcnow())
    allow_multiple_choices = peewee.BooleanField(default=True)
    allow_duplicate_answers = peewee.BooleanField(default=False)
    answer_response = peewee.CharField(default="Thank you for your vote")

    def add_answer(self, choice, number):
        print("adding vote to choice: '{}' from number: '{}'".format(self.name, number))
        c = Choice.get_or_none(Choice.poll == self, Choice.name == choice)

        if not c:
            print("No such choice '{}' on poll: '{}'".format(choice, self.name))
            return False

        if not self.allow_multiple_choices:
            duplicate = Answer.get_or_none(Answer.number == number, Answer.poll == self, Answer.choice != c)
            if duplicate:
                print("Found answer on another coice: {}".format(duplicate))
                return False
            else:
                print("No other answers found, proceding")

        if not self.allow_duplicate_answers:
            duplicate = Answer.get_or_none(Answer.number == number, Answer.choice == c)
            if duplicate:
                print("Found duplicate of answer from number {} on choice: {}".format(duplicate.number, duplicate.choice.name))
                return False
            else:
                print("No other duplicates found, proceding")
        c.add_answer(number)
        print("Done adding vote from number: {} on choice: {}".format(number, c))
        return True

    def to_dict(self):
        data = {}
        data["id"] = self.id
        data["name"] = self.name
        data["description"] = self.description
        data["owner"] = self.owner.id
        data["number"] = self.number
        #data["created"] = self.created
        data["choices"] = []
        for c in self.choices:
            data["choices"].append(c.to_dict())

        return data

class Choice(BaseModel):
    poll = peewee.ForeignKeyField(Poll, backref='choices')
    created = peewee.DateTimeField(default=datetime.datetime.utcnow())
    name = peewee.CharField()
    description = peewee.CharField()
    class Meta:
        indexes = (
            (("name", "poll"), True),
        )

    def add_answer(self, number):
        answer = Answer()
        answer.choice = self
        answer.poll = self.poll
        answer.number = number
        answer.save()

    def to_dict(self):
        data = {}
        data["id"] = self.id
        data["name"] = self.name
        data["description"] = self.description
        data["votes"] = len(self.answers)
        return data

class Answer(BaseModel):
    choice = peewee.ForeignKeyField(Choice, backref='answers')
    poll = peewee.ForeignKeyField(Poll)
    created = peewee.DateTimeField(default=datetime.datetime.utcnow())
    number = peewee.CharField()

def create_db():
    database.create_tables([Poll, Choice, Answer, User])

def get_db():
    return database
