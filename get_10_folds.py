import sqlite3
import time
from sklearn.cross_validation import ShuffleSplit
from random import shuffle
import cPickle as pickle

import recsys.algorithm

recsys.algorithm.VERBOSE = True
from recsys.algorithm.factorize import SVD, SVDNeighbourhood
from recsys.evaluation.prediction import RMSE, MAE

import random


libmc = True

try:
    import pylibmc
except:
    libmc = False

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def fold(r, i, k):
    return r[i * k : (i + 1) * k]

def rest(r, i, k):
    return r[0 : i * k] + r[(i + 1) * k:-1] 

def tenFolds():
    if libmc:
        mc = pylibmc.Client(["127.0.0.1"], binary=True,
                         behaviors={"tcp_nodelay": True,
                                    "ketama": True})
    rows = None
    if libmc and mc.get("mdsh_rows") is None:
        print "sql"
        conn = sqlite3.connect("db.sqlite")
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute("SELECT * FROM train")

        rows = list(cur)
        mc.set("mdsh_rows", rows)
    else:
        rows = mc["mdsh_rows"]
        
    print "end sql"
    folds = []
    r = rows
    k = len(r)/10
    folds = [(fold(r, i, k),rest(r, i, k)) for i in range(0,10)]
    
    return folds



def collab_filter(model, filename):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    l = list(cur.execute("SELECT rating,track,user FROM train"))
    K = 100
    svd = model
    svd.set_data(l)
    svd.compute(k=K, min_values=0.0, pre_normalize=None, mean_center=False, post_normalize=True)
    svd.save_model(filename)

def test_classifier(model, filename):
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT count(*) fROM train")
    c = cur.fetchone()
    print c
    svd = model
    svd.load_model(filename)
    l = cur.execute("SELECT * FROM train")
    pairs = []
    for idx,item in enumerate(l): 
        user = item["user"]
        track = item["track"]
        if idx % 1024 == 0:
            print idx, c
        pairs.append((svd.predict(track,user), item["rating"]))

    print RMSE(pairs).compute()


def track_averages():
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT avg(rating),track fROM train group by track")
    scores = {}
    for row in cur:
        scores[row["track"]] = row["avg(rating)"]
    return scores

def user_averages():
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT avg(rating),user fROM train group by user")
    scores = {}
    for row in cur:
        scores[row["user"]] = row["avg(rating)"]
    return scores



def classify_test_set(model,filename):
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT count(*) fROM test")
    c = cur.fetchone()
    print c
    svd = model
    svd.load_model(filename)
    l = cur.execute("SELECT * FROM test")
    pairs = []
    track_means = track_averages()
    user_means  = user_averages()
    build = ""
    for idx,item in enumerate(l): 
        user = item["user"]
        track = item["track"]
        if idx % 1024 == 0:
            print idx, c
        print track
        print user
        try:
            r = svd.predict(track,user) 
        except (KeyError), err:
            if (err == user):
                r = track_means[track]
            elif (err == track):
                r = user_means[user]
            else:
                r = 50
            
        if r > 100:
            r = 100
        if r < 0:
            r = 0
        
        build += str(item["artist"]) + "," + str(item["track"]) + "," + str(item["user"]) +  "," + str(r) + "\n"


    f = open("answer.csv", "w")
    f.write(build)
    f.flush()
    f.close()


if __name__ == "__main__":
    test_classifier(SVD(), "svd.model")
    #x = SVDNeighbourhood()
    #collab_filter(x, "svd-n.model")
    #print "bees"
    #test_classifier(x, "svd-n.model")
    classify_test_set(SVD(), "svd.model")
