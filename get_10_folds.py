import sqlite3
import time
from sklearn.cross_validation import ShuffleSplit
from random import shuffle
import cPickle as pickle

import recsys.algorithm

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

def collab_filter(model, filename, selector="SELECT rating,track,user FROM train"):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    l = list(cur.execute(selector))
    print "results",len(l)
    K = 100
    svd = model
    svd.set_data(l)
    svd.compute(k=K, min_values=0.0, pre_normalize=None, mean_center=True, post_normalize=True)
    svd.save_model(filename)


def everything_average():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT avg(rating) from train")
    return cur.fetchone()[0]

user_fallbacks = 0
track_fallbacks = 0
everything_fallbacks = 0
artist_fallbacks = 0
everything_average = everything_average()

def predict_item(svd, track, user):
    global everything_fallbacks
    global track_fallbacks
    global user_fallbacks
    
    try:
        r = svd.predict(track,user) 
    except (KeyError), err:
        if (err == user):
            r = track_means[track]
            user_fallbacks += 1
        elif (err == track):
            r = user_means[user]
            track_fallbacks += 1
        else:
            r = everything_average 
            everything_fallbacks += 1
    
    if r > 100:
        r = 100
    if r < 0:
        r = 0

    return r

def load_svd(filename):
    svd = SVD() 
    svd.load_model(filename)
    return svd


def test_classifier(model, filename=None, itemkey="track", selector="SELECT * FROM train"):
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    s = 0
    c = 0
    t_p = 0
    for i in range(0,10):
        svd = SVD()
        if filename is not None:
            svd.load_model(filename)
        l = list(cur.execute(selector))
        random.shuffle(l)
        count = len(l)
        svd.set_data([(x["rating"],x["track"],x["user"]) for x in l[0:int(count*0.7)]])
        K = 100
        svd.compute(k=K, min_values=0.0, pre_normalize=None, mean_center=True, post_normalize=True)

        pairs = []
        for idx,item in enumerate(l[int(count*0.7):]): 
            user = item["user"]
            track = item[itemkey]
            pairs.append((predict_item(svd, track,user), item["rating"]))
        t_p += len(pairs)
        s += RMSE(pairs).compute()
        c += 1.0
        print "iteration"
    print s/c, t_p


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

def classify_test_set(svd, selector):
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    l = cur.execute(selector)
    pairs = []
    track_means = track_averages()
    user_means  = user_averages()
    build = []
    for idx,item in enumerate(l): 
        user = item["user"]
        track = item["track"]
        if idx % 1024 == 0:
            print idx
        
        r = predict_item(svd, track, user)
        build.append({"score":r,"order":item["oc"]}) 

    return build

if __name__ == "__main__":
    #track_model = load_svd("svd.model")
    #artist_model = load_svd("svd-artists.model")
    #test_classifier(SVD(), "svd.model")
    #test_classifier(SVD(), "svd-artists.model", "artist")
    #x = SVDNeighbourhood()
    #collab_filter(x, "svd-n.model")
    #print "bees"
    #test_classifier(x, "svd-n.model")
    
    x = SVD()


    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT distinct time from train")
    build = []
    for row in cur:
        x = SVD()
        selector = "SELECT t.rating,t.track,t.user FROM train t where t.time=" + str(row[0]) 

        collab_filter(x, "tracks-male.model", selector)
        build += classify_test_set(x, selector="SELECT t.* FROM test t where t.time=" + str(row[0])) 
        print len(build)

    build = sorted(build, key=lambda x: x["order"])
    build = "\n".join([str(x["score"]) for x in build])
    build += "\n"

    f = open("answer.csv","w")
    f.write(build)
    f.close()

    print "missing users" , user_fallbacks
    print "missing track" , track_fallbacks
    print "all missing"   , everything_fallbacks
    print "artist fb"     , artist_fallbacks
