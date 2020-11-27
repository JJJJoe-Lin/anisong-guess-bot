import random

class Gamers(object):
    def __init__(self):
        self.info = {}  # name -> info

    def add(self, user):
        # check dup
        if user.name in self.info:
            raise ValueError

        gamer = {"user": user, "score": 0}
        self.info[user.name] = gamer

    def remove(self, username):
        # check exist
        if username not in self.info:
            raise ValueError

        del self.info[username]

    def check_if_gamer(self, username):
        return True if username in self.info else False

    def random_choose(self):
        return random.choice(list(self.info.keys()))

    def add_points(self, username, points):
        # check exist
        if username not in self.info:
            raise ValueError

        self.info[username]["score"] += points

    def deduct_points(self, username, points):
        # check exist
        if username not in self.info:
            raise ValueError

        self.info[username]["score"] -= points

    def set_score(self, username, score):
        # check exist
        if username not in self.info:
            raise ValueError

        self.info[username]["score"] = score

    def get_score(self, username):
        # check exist
        if username not in self.info:
            raise ValueError

        return self.info[username]["score"]

    def get_all_scores(self):
        scores = {}
        for k, v in self.info.items():
            scores[k] = v["score"]
        return scores

    def reset_all_scores(self):
        for k in self.info:
            self.info[k]["score"] = 0
            
    async def send_to_all_gamers(self, msg=None, exclusion=[], *, embed=None):
        # check msg exist
        if not msg and not embed:
            raise ValueError

        for k, v in self.info.items():
            if k not in exclusion:
                await v["user"].send(msg, embed=embed)

