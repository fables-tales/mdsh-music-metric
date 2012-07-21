import sqlite3
import collections


from random import shuffle
from recsys.algorithm.factorize import SVD, SVDNeighbourhood
from recsys.evaluation.prediction import RMSE, MAE

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = sqlite3.connect("db.sqlite") 
conn.row_factory = dict_factory
class Bin:
    def __init__(self, gender = None, age_range=None, region=None,music=None,time=None):
        self.gender = gender
        self.age_range = age_range
        self.region = region
        self.music = music
        self.train_items = []
        self.test_items  = []
        self.svd = SVDNeighbourhood()
        self.everything_average = 0
        self.time = time


    def _load(self, table, items):
        cur  = conn.cursor()
        query = "SELECT * FROM " + table + " t, users u WHERE u.user = t.user " 
        if self.age_range is not None:
            if self.age_range != "''":
                r_list = list(self.age_range)
                query += "AND u.age >= " + str(r_list[0]) + " AND u.age <= " + str(r_list[-1]) + " " 
            else:
                query += "AND u.age = '' "

        if self.music is not None:
            query += "AND u.music='" + self.music + "' "

        if self.time is not None:
            query += "AND t.time=" + str(self.time) + " "

        if self.region is not None: 
            query += "AND u.region='" + str(self.region) + "' "

        if self.gender is not None:
            query += "AND u.gender='" + str(self.gender) + "' "

        cur.execute(query)

        for x in cur:
            items.append(x)

    def load_no_demo(self,time=None):
        query = "SELECT * FROM train t where t.user not in (select user from users)"
        if time is not None:
            query += " AND t.time=" + str(time)
        cur = conn.cursor()
        for item in cur.execute(query):
            self.train_items.append(item)

        query2 = "SELECT * FROM test t where t.user not in (select user from users)"
        if time is not None:
            query2 += " AND t.time=" + str(time)

        for item in cur.execute(query2):
            self.test_items.append(item)


    def load_train_items(self):
        self._load("train", self.train_items)

    def load_test_items(self):
        self._load("test", self.test_items)


    def _train(self,items,svd):
        everything_average = 0
        svd_rows = []
        for item in items:
            everything_average += item["rating"]
            svd_rows.append((item["rating"], item["track"],item["user"]))


        self.everything_average /= len(items)

        svd.set_data(svd_rows)
        k = 1000
        svd.compute(k=k, 
                         min_values=0.0, 
                         pre_normalize=None,
                         mean_center=True, 
                         post_normalize=True)



    def _predict(self, item, svd):
        track = item["track"]
        user  = item["user"]
        try:
            r = svd.predict(track,user) 
        except: 
            r = self.everything_average
        
        if r > 100:
            r = 100
        if r < 0:
            r = 0

        return r

    def train(self):
        print "train start"
        self._train(self.train_items, self.svd)
        print "train end"


    def ten_fold(self):
        pairs = []
        for i in range(0,10):
            print "fold"
            items = self.train_items[:]
            shuffle(items)
            svd = SVDNeighbourhood()
            self._train(items[0:int(len(items)*0.7)], svd)
            for item in items[int(len(items)*0.7):]:
                predicted = self._predict(item, svd) 
                actual    = item["rating"]
                pairs.append((predicted,actual))
        return RMSE(pairs).compute(),len(pairs)

    def predict(self, item):
        return {"score":self._predict(item, self.svd), "order":item["oc"]}

if __name__ == "__main__":

    k = 5
    ranges = [range(i,i+k) for i in range(13,95,k)]
    ranges.append("''")
    musics = [None]
    musics = ["I like music but it does not feature heavily in my life",
                "Music has no particular interest for me",
                "Music is important to me but not necessarily more important",
                "Music is important to me but not necessarily more important than other hobbies or interests",
                "Music is no longer as important as it used to be to me",
                "Music means a lot to me and is a passion of mine"]
    regions = ["",
        "Centre",
        "Midlands",
        "North",
        "North Ireland",
        "Northern Ireland",
        "South"]

    times = [0,
        4,
        6,
        7,
        8,
        9,
        11,
        12,
        13,
        15,
        16,
        17,
        18,
        19,
        21,
        22,
        23]
    s_train = 0
    s_test = 0

    bins = []

    sum_rmse = 0

    n = 0

    rmse = 0
    rmse_count = 0
    s = 0

    responses = []
    period = []
    x = Bin()
    x.load_train_items()
    x.load_test_items()
    x.train()
    print x.ten_fold()
    for item in x.test_items:
        prediction = x.predict(item) 
        responses.append(prediction)

    b = Bin()
    
    print "loading no demos"
    b.load_no_demo()
    if len(b.train_items) > 0:
        b.train()
        for x in b.test_items:
            responses.append(b.predict(x))

    print len(responses)

    
    responses = sorted(responses, key=lambda x: x["order"])
    build = ""
    for x in responses: 
        build += str(x["score"]) + "\n"
    f = open("answer.csv", "w")
    f.write(build)
    f.flush()
    f.close()
