import os
import requests


class MailService:
    @classmethod
    def send(cls, recipient, body):
        print("MAIL sent to : ", recipient, " ", body)
        requests.post(os.environ.get("MAIL_URL")+"/api/mail",
                      json={"to": recipient, "from": "noreply@registration-demo.io", "body": body})
