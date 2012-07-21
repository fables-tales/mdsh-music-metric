
import sqlite3
import collections

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier

from random import shuffle
from recsys.algorithm.factorize import SVD, SVDNeighbourhood
from sklearn.feature_selection import RFE,SelectKBest,chi2
from sklearn import svm

from recsys.evaluation.prediction import RMSE, MAE

from sklearn.svm import LinearSVC

conn = sqlite3.connect("db.sqlite")

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn.row_factory = dict_factory

if __name__ == "__main__":

    query = "SELECT * FROM users u, train t, raw_words w where t.user = u.user AND w.user = u.user"
    cur = conn.cursor()
    cur.execute(query)
    values = []
    labels = []
    for row in cur:
        values.append([row["age"],row["q_a"],
            row["q_b"],row["q_c"],row["q_d"],row["q_e"],row["q_f"],row["q_g"],
            row["q_h"],
            row["q_i"],
            row["q_j"],
            row["q_k"],
            row["q_l"],
            row["q_m"],
            row["q_n"],
            row["q_o"],
            row["q_p"],
            row["q_q"],
            row["q_r"],
            row["q_s"],

            ])
        labels.append(row["rating"])

        
    for x in values:
        for i in range(0,len(x)): 
            if x[i] == "":
                x[i] = 0

    clf = RandomForestClassifier(max_depth=40) 
    print "done selection"
    trn_v = values[0:int(len(values)*0.7)]
    print "bees"
    trn_l = labels[0:int(len(labels)*0.7)]
    print "fitting"
    clf.fit(trn_v, trn_l)

    diff = 0
    k = 0

    print "predicting"
    cls = clf.predict(values)
    for i in range(int(len(values)*0.7),len(values)):
        d = cls[i] - labels[i]
        diff += d*d
        k += 1
    diff /= k
    print diff ** 0.5
