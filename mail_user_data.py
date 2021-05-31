from os import getenv
from mongoengine import Document, connect
from mongoengine.fields import StringField, ReferenceField, DateTimeField, ObjectIdField


class Adoptable(Document):
    meta = {
        "collection": "adoptables",
    }
    repository = StringField(required=True)
    description = StringField(required=False)
    owner = StringField(required=True)
    new_owner = StringField(required=False)


class ChatMessage(Document):
    meta = {"collection": "chatmessages"}

    user = StringField(required=True)
    message = StringField(required=True)
    timestamp = DateTimeField(required=False)
    chat_id = ObjectIdField(required=True)


class Match(Document):
    meta = {
        "collection": "matches",
    }

    user = StringField(required=True)
    adoptable = ReferenceField(Adoptable)


import smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sender_email = "repoadopt@gmail.com"
receiver_email = "niek.sleddens@gmail.com"
password = "Mortality.Footage9.Refreeze"

import base64
import json


def handler(context, event):
    token = json.load(
        base64.b64decode(event.headers.get("Authorization").split(".")[1])
    )

    # Create message
    message = MIMEMultipart()
    message["From"] = getenv("from_email")
    message["To"] = token["email"]
    message["Subject"] = "RepoAdopt user data"
    message.attach(
        MIMEText("The attachment on this email contains your user data.", "plain")
    )

    # Get data
    connect(
        getenv("db_name"),
        host=getenv("mongo_url"),
        port=int(getenv("mongo_port")),
        alias="default",
    )

    json_body = {}
    json_body.matches = Match.objects(user=token["login"]).all()
    json_body.chat_messages = ChatMessage.objects(user=token["login"]).all()
    json_body.adoptables = Adoptable.objects(owner=token["login"]).all()

    # Add attachment
    part = MIMEBase("application", "json")
    part.set_payload(json.dumps(json_body))

    encoders.encode_base64(part)

    filename = "Repoadopt-userdata.json"
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    message.attach(part)

    # Send message
    text = message.as_string()
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(getenv("from_email"), getenv("password_email"))
        server.sendmail(sender_email, receiver_email, text)
