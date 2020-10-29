import sqlite3
import time
from datetime import datetime
import curses
import curses.textpad

def editor(pretitle="", prebody=""):
    '''
    A simple editor for posting questions or answers. Returns the title and body of the post
    It can also edit post given the title and body of the post wanted to be modified
    '''

    # initialize command line text editor with curses
    stdscr = curses.initscr()
    curses.noecho()      # displaying keys only when required
    curses.cbreak()      # no Enter key required
    stdscr.keypad(True)  # enable special keys

    begin_x = 0         # starting x coordinate
    begin_y = 0         # starting y coordinate
    rows, cols = stdscr.getmaxyx()   # get display dimention of the console

    win = curses.newwin(rows, cols, begin_y, begin_x)   # create window
    win.addstr(begin_y, begin_x, "Type your post here. Press Ctrl + G to switch and exit.")
    win.addstr(begin_y + 1, begin_x, "Title:")
    win.addstr(begin_y + 3, begin_x, "Body:")
    win.refresh()

    # initialize subwindow
    titlewin = win.subwin(1, cols ,begin_y + 2, begin_x)
    titlewin.addstr(0, 0, pretitle) # if a previous post title is supplied load the previous post

    bodywin = win.subwin(rows - 7, cols ,begin_y + 4, begin_x)
    bodywin.addstr(0, 0, prebody) # load previous post body

    # refresh previous text
    bodywin.refresh()
    titlewin.refresh()

    replywin = win.subwin(1, 5, rows - 2, begin_x + 22)
    redisplay = win.subwin(1, 22, rows - 2, begin_x)

    while True:
        title = curses.textpad.Textbox(titlewin).edit()
        body = curses.textpad.Textbox(bodywin).edit()

        redisplay.addstr(0, 0, "Exit and save? (y/N) ")
        redisplay.refresh()

        reply = curses.textpad.Textbox(replywin, insert_mode=True).edit(lambda x: 7 if x == 10 else x)  # convert Ctrl+G to Enter

        if reply.strip() in ['y', 'Y', "yes", "Yes", "YES"]:
            break
        else:  # return to edit post
            redisplay.clear()
            redisplay.refresh()
            replywin.clear()
            replywin.refresh()

    # restore configuration
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    return title, body

def choose_action(result):
    pass

def search_post(conn, db, uid):
    ''' 
    search a post in the database. Return the matching posts 
    '''
    print("Please enter keyword(s) to search. Press Enter to finish.")
    words = input().lower()  # lower the case of all keywords as the search is case insensitive
    keywords = tuple(words.split())
    time.sleep(0.5)
    if len(keywords) == 0:
        # If no keyword is supplied, return all posts, sort by newest
        result = db.execute("""
        SELECT 
            CASE
                WHEN posts.pid = answers.qid THEN
                    "Q"
                ELSE
                    "A"
                END checkqa,
            posts.*,
            IFNULL(COUNT(DISTINCT votes.vno), 0) vcnt,
            CASE
                WHEN posts.pid = answers.pid THEN
                    "N/A"
                ELSE
                    COUNT(DISTINCT answers.pid)
                END countanswers
            FROM posts LEFT JOIN answers ON posts.pid = answers.qid
            LEFT JOIN votes ON votes.pid = posts.pid
            GROUP BY posts.pid
            ORDER BY posts.pdate DESC
        """).fetchall()
    else:
        # search for supplied keyword
        query = """
        SELECT 
            CASE
                WHEN posts.pid = answers.qid THEN
                    "Q"
                ELSE
                    "A"
                END checkqa,
            posts.*,
            IFNULL(COUNT(DISTINCT votes.vno), 0) vcnt,
            CASE
                WHEN posts.pid = answers.pid THEN
                    "N/A"
                ELSE
                    COUNT(DISTINCT answers.pid)
                END countanswers
            FROM posts LEFT JOIN answers ON posts.pid = answers.qid
            LEFT JOIN votes ON votes.pid = posts.pid
            LEFT JOIN tags ON tags.pid = posts.pid
            GROUP BY posts.pid
            HAVING ((posts.title LIKE ?) OR (posts.body LIKE ?) OR (tags.tag LIKE ?))
        """
        # insert query statement for all matchings
        for i in range(len(keywords) - 1):
            query += "OR ((posts.title LIKE ?) OR (posts.body LIKE ?) OR (tags.tag LIKE ?)) \n"
        
        # append the keywords into input tuple
        queryInputs = []
        for k in keywords:
            kString = "%" + k + "%"
            for i in range(3):
                queryInputs.append(kString)
        
        # Order by the number of their apperance, counting only once per keyword
        # since the LIKE keyword will return 1 if match or 0 if not, adding them together return no. of keyword matched

        query += "ORDER BY ((posts.title LIKE ?) OR (posts.body LIKE ?) OR (tags.tag LIKE ?)) \n"
        for i in range(len(keywords) - 1):
            query += " + ((posts.title LIKE ?) OR (posts.body LIKE ?) OR (tags.tag LIKE ?)) \n"
        query += "DESC \n"

        # append the keywords into input tuple
        for k in keywords:
            kString = "%" + k + "%"
            for i in range(3):
                queryInputs.append(kString)
                
        queryInputs = tuple(queryInputs)
        result = db.execute(query, queryInputs).fetchall()

    for item in result:
        # item format:
        # (Ptype, pid, pdate, title, body, poster, vcnt, acnt)
        print(item)

def post_question(conn, db, uid):
    ''' 
    post a question to the database 
    '''
    title, body = editor()
    print("*-----------------------*")
    print("Please review your post:")
    print("Title:", title)
    print("Body:")
    print(body)
    userInput = input("Do you want to post? (y/N)")
    if userInput.strip() not in ['y', 'Y', "yes", "Yes", "YES"]:
        print("User discarded post.")
        time.sleep(0.5)
        print("*-----------------------*")
        return
    print("Posting...\n")
    time.sleep(1)
    maxpid = db.execute("SELECT MAX(pid) FROM posts").fetchall()
    if maxpid[0][0] != None:
        maxpidstr = maxpid[0][0][1:]
        if maxpidstr == "999":
            print("Maximum posts reached. No more posts can be made.")
            return
        pidint = int(maxpidstr) + 1
        newpid = "p" + str(pidint).zfill(len(maxpidstr))
    else:
        newpid = "p000"

    pdate = datetime.date(datetime.now()) # pdate = current date

    db.execute("INSERT INTO posts VALUES (?,?,?,?,?)", (newpid, pdate, title, body, uid)) # insert question into posts table
    db.execute("INSERT INTO questions VALUES (?, NULL)", (newpid,)) # insert question into questions table. theaid does not exist initially
    conn.commit()

    check = db.execute("SELECT posts.pid FROM posts WHERE posts.pid = ?", (newpid,))
    if check != []:
        print("Question posted successfully!")
        print()
        time.sleep(0.5)
    else:
        print("Question posting unsuccessful. Please try again later")
        print()
        time.sleep(0.5)

    return

def session(conn, db, uid):
    ''' User session entrance '''
    print("*-----------------------*")
    print("Welcome back, {0}!".format(uid))
    while True:
        print("Select an action:")
        print("1. Post a question.")
        print("2. Search for posts.")
        print("3. Logout")
        userInput = input("(1/2/3): ")
        print("*-----------------------*")
        userInput.strip()
        if not userInput.isdigit():
            print()
            print("Unrecognized input. Please try again.")
            time.sleep(1)
            continue

        userInput = int(userInput)
        if userInput == 1:
            post_question(conn, db, uid)

        elif userInput == 2:
            search_post(conn, db, uid)

        elif userInput == 3:
            time.sleep(0.5)
            return

if __name__ == "__main__":
    title = "Test title"
    body = ''' 
    This is a really long body. The purpose of this long body is too test that if the editor is functioning properly. There are a lot of 
    redunant sentences and words in this string, or you may call it, text. Again, these are just fillers, they dont really mean anything.
    It is also unnecessarily verbose such that I can test what if the post body is more than a single line
    '''
    newtitle, newbody = editor(title, body)
    print(newtitle)
    print(newbody)
    