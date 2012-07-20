import sqlite3
import csv


def process_words():
    r = csv.reader(open('csv_data/words.csv', 'r'))
    s = {}

    i = 0

    for row in list(r)[1:]:
        processed_row = row[3].replace("\xcd","'").replace("\xd5","'").replace("`","'").lower()
        if not s.has_key(processed_row):
            s[processed_row] = i
            i += 1
        key = s[processed_row]
    

def create_train_table():
    conn = sqlite3.connect('db.sqlite')

    cur = conn.cursor()
    cur.execute('SELECT count(*) FROM train') 
    rows = cur.fetchone()
    print "training rows", rows[0]
    if rows[0] == 0:
        f = open("csv_data/train.csv").read().strip().replace("\r","").split("\n")
        for line in f[1:]:
            split = line.split(",")
            cur.execute("INSERT INTO train (artist,track,user,rating,time) VALUES (?,?,?,?,?);", (split[0],split[1],split[2],split[3],split[4]))
        conn.commit() 
        print "injected",len(f[1:]),"rows into train"

def create_test_table():
    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM test") 

    rows = cur.fetchone()
    print "testing rows",rows[0]
    if rows[0] == 0:
        f = open("csv_data/test.csv").read().strip().replace("\r","").split("\n")
        for line in f[1:]:
            split = line.split(",")
            cur.execute("INSERT INTO test (artist,track,user,time) VALUES (?,?,?,?);", (split[0],split[1],split[2],split[3]))
        conn.commit() 
        print "injected",len(f[1:]),"rows into test"


def create_raw_words_table():
    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM raw_words")
    rows = cur.fetchone()
    print "raw words rows", rows[0]
    if rows[0] == 0:
        f = csv.reader(open("csv_data/words.csv", "r"))
        i = 0
        for line in list(f)[1:]:
            line = [i] + list(line)
            i += 1
            if len(line) < 88:
                line.append('')
            line[4] = line[4].replace("\xd5","'").replace("`","'").replace("\xcd","")
            cur.execute("INSERT INTO raw_words VALUES(" + ",".join(["?"]*(len(line))) + ")", tuple(line)) 

        conn.commit()

def create_processed_words_table():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT count(*) from processed_words")
    rows = cur.fetchone()
    print "processed words rows", rows[0]
    if rows[0] == 0:
        cur.execute("SELECT * FROM raw_words")
        rows = []
        heard_of_mapping   = {}
        own_artist_mapping = {}
        like_artist_mapping = {}
        for row in cur:
            if not heard_of_mapping.has_key(row[3]):
                heard_of_mapping[row[3]] = len(heard_of_mapping)

            if not own_artist_mapping.has_key(row[4]):
                own_artist_mapping[row[4]] = len(own_artist_mapping)


            if not like_artist_mapping.has_key(row[5]):
                like_artist_mapping[row[5]] = len(like_artist_mapping)

            rows.append(list(row))

        for row in rows:
            row[3] = heard_of_mapping[row[3]]
            row[4] = own_artist_mapping[row[4]]
            row[5] = like_artist_mapping[row[5]]
            cur.execute("INSERT INTO processed_words VALUES(" + ",".join(["?"]*len(row)) + ")", tuple(row))
        conn.commit()

def create_user_table():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT count(*) from users")
    rows = cur.fetchone()
    print "user rows",rows[0]
    if rows[0] == 0:
        f = csv.reader(open("csv_data/users.csv", "r"))

        for line in list(f)[1:]:
            if str(line[6]).find("More than 16") != -1:
                line[6] = 17
            if str(line[6]).lower() == "less than an hour":
                line[6] = 0
            if str(line[6]).find("16+") != -1:
                line[6] = 17

            if str(line[6]).lower().find("hour") != -1:
                line[6] = int(line[6].lower().replace(" hour","").replace("s",""))

            if str(line[7]).find("More than 16") != -1:
                line[7] = 17
            if str(line[7]).lower() == "less than an hour":
                line[7] = 0
            if str(line[7]).find("16+") != -1:
                line[7] = 17

            if str(line[7]).lower().find("hour") != -1:
                line[7] = int(line[7].lower().replace(" hour","").replace("s",""))
            cur.execute("INSERT INTO users VALUES(" + ",".join(["?"] * len(line)) + ")",tuple(line)) 
        conn.commit()

if __name__ == "__main__":

    create_train_table()
    create_test_table()

    create_raw_words_table()
    create_processed_words_table()

    create_user_table()
