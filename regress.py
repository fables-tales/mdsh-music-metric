import sqlite3
import simplejson
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, RandomForestRegressor


conn = sqlite3.connect("db.sqlite")

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn.row_factory = dict_factory

words = "Uninspired,Sophisticated,Aggressive,Edgy,Sociable,Laid back,Wholesome,Uplifting,Intriguing,Legendary,Free,Thoughtful,Outspoken,Serious,Good lyrics,Unattractive,Confident,Old,Youthful,Boring,Current,Colourful,Stylish,Cheap,Irrelevant,Heartfelt,Calm,Pioneer,Outgoing,Inspiring,Beautiful,Fun,Authentic,Credible,Way out,Cool,Catchy,Sensitive,Mainstream,Superficial,Annoying,Dark,Passionate,Not authentic,Good Lyrics,Background,Timeless,Depressing,Original,Talented,Worldly,Distinctive,Approachable,Genius,Trendsetter,Noisy,Upbeat,Relatable,Energetic,Exciting,Emotional,Nostalgic,None of these,Progressive,Sexy,Over,Rebellious,Fake,Cheesy,Popular,Superstar,Relaxed,Intrusive,Unoriginal,Dated,Iconic,Unapproachable,Classic,Playful,Arrogant,Warm,Soulful"

useful_keys = ["q_" + i for i in "abcdefghijklmnopqrs"] + ["age"] + [x.lower().replace(" ", "_") for x in words.split(",")] + ["user","artist","time"]

if __name__ == "__main__":
    wh = open('regressionresult.json', 'w')
    cur = conn.cursor()
    q1 = "SELECT * FROM users u, train t, raw_words r WHERE u.user = r.user AND u.user = t.user AND t.artist = r.artist;"
    values_arr = []
    labels_arr = []
    for idx,x in enumerate(cur.execute(q1)):
        label = x["rating"]
        values = []
        for key in useful_keys:
            assert isinstance(x[key], int) or isinstance(x[key], float) or x[key] == ""
            if x[key] == "":
                x[key] = 0
            values.append(x[key])
        assert len(values) == len(useful_keys)
        values_arr.append(values)
        labels_arr.append(label)
        if idx % 1024 == 0:
            print idx


    # clf = RandomForestRegressor() 
    clf = RandomForestRegressor(n_jobs=1,n_estimators=80, max_depth=10, min_samples_split=20, random_state=0,min_density=0.8, compute_importances=True)
    

    

    trn_v = values_arr
    print "bees"
    trn_l = labels_arr
    print "fitting"
    clf.fit(trn_v, trn_l)

    diff = 0
    k = 0

    cur = conn.cursor()
    results = []
    q1 = "SELECT * FROM users u, test t, raw_words r WHERE u.user = r.user AND u.user = t.user AND t.artist = r.artist;"
    for idx,x in enumerate(cur.execute(q1)):
        values = []
        for key in useful_keys:
             assert isinstance(x[key], int) or isinstance(x[key], float) or x[key] == ""
             if x[key] == "":
                 x[key] = 0
             values.append(x[key])
        assert len(values) == len(useful_keys)
        cls = float(clf.predict(values)[0])   
        if cls > 100:
             pred = 100.0
        elif cls < 0:
             pred = 0.0
        else:
             pred = cls
         
    results.append({"score":pred,"order":x['oc']})
    if idx % 1024 == 0:
         print idx
    simplejson.dump(wh, results)