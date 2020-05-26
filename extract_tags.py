import sqlite3
import glob
import re

db = sqlite3.connect('tags.db')
cursor = db.cursor()
cursor.execute('DROP TABLE IF EXISTS tags')
cursor.execute("""CREATE TABLE tags (
                                tag TEXT,
                                doc TEXT
                               )""")
help_files = glob.glob('/usr/local/share/vim/vim82/doc/*.txt')
for doc in help_files:
    with open(doc) as f:
        text = f.read()

        tag_regex = re.compile(r'(?:^|\s)\*(.*?)\*(?=\s)')
        tags = tag_regex.findall(text)
        for t in tags:
            docname = doc.split('/')[-1].split('.')[0]
            entry = (t, docname)
            cursor.execute('INSERT INTO tags VALUES (?,?)', entry)
            print('{} => {}'.format(entry[1], entry[0]))

db.commit()
db.close()
