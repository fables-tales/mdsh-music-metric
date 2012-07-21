import sqlite3
import time
from sklearn.cross_validation import ShuffleSplit
from random import shuffle
import cPickle as pickle

import recsys.algorithm

recsys.algorithm.VERBOSE = True
from recsys.algorithm.factorize import SVD
from recsys.evaluation.prediction import RMSE, MAE


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



def collab_filter():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    l = list(cur.execute("SELECT user,track,rating FROM train"))
    K = 100
    svd = SVD()
    svd.set_data(l)
    svd.compute(k=K, min_values=0.1, pre_normalize=None, mean_center=True, post_normalize=True)
    svd.save_model("svd.model")
    

if __name__ == "__main__":
    collab_filter()
