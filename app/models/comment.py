from user import user
from incident import incident
from datetime import datetime

class Comment():
    def __init__(self, content, user_author: user, ticket: incident):
        self.content = content
        self.author = user_author.id
        self.ticket = ticket.id
        self.timestamp = datetime.now()


    def __repr__(self):
        return f"<Comment by {self.author}: {self.content}>"