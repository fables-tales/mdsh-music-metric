import sqlite3
import time
from sklearn.cross_validation import ShuffleSplit
from random import shuffle
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
    for i in range(0,10):
        folda = r[i * len(r)/10 : (i + 1) * len(r) / 10]
        foldb = r[0 : i * len(r)/10] + r[(i + 1) * len(r)/10:-1]

        folds.append((folda,foldb))
    
    return folds

if __name__ == "__main__":
    start = time.time()
    x = tenFolds()
    end = time.time()
    print end-start
    
    start = time.time()
    y = tenFolds()
    end = time.time()
    print end-start
    assert x == y
    print x[0][0][0]
    print y[0][0][0]
