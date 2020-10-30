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

def _parse(text):
    '''
    NOT WORKING
    A parse function to ensure the total text display will not exceed 70 characters
    '''
    accu = 0
    i = 0
    titleLength = len(text)
    while i < titleLength:
        if text[i] != '\n': #If there is a newline we reset the accumulator
            accu += 1
            if accu > 62:
                char = text[accu]
                if char.stip() == "": # If the character we want to shift to newline is empty
                    text = text[:i] + '\n' + (" "*6) + text[i + 1:]
                else: # find the previous space
                    found = False
                    prei = i
                    while i > 0 and not found:
                        i -= 1
                        if char.stip() == "":
                            text = text[:i] + '\n'+ (" "*6) + text[i + 1:]
                            found = True
                    if not found: # edge case when title word is longer than 62
                        text = text[:prei - 1] + '-\n'+ (" "*6) + text[prei + 1:]

        accu = 0
        i += 1
    return text

def view(conn, db, uid, pid):
    '''
    detailed view of a post
    '''
    post = db.execute("SELECT posts.* FROM posts WHERE posts.pid = ?",(pid,)).fetchall() # extract post
    if post == []:
        print("Error: post with pid[{0}] does not exist".format(pid))
        return
    post = post[0]

    answers = None
    checkQues = db.execute("SELECT pid FROM questions WHERE questions.pid = ?",(pid,)).fetchall() # check if it is a question
    IS_QUESTION = False
    if checkQues != [] and checkQues[0][0] == pid:
        IS_QUESTION = True
        answerpids = db.execute("SELECT answers.pid FROM answers WHERE answers.qid = ?",(pid,)).fetchall() # Get answers pid
        answers = list()
        for apid in answerpids:
            apid = apid[0] # results are in tuples, need to extract the result out
            text = db.execute("SELECT posts.* FROM posts WHERE posts.pid = ?",(apid,)).fetchall() # get content of answer
            answers.append(text[0]) # remove the outer list from the return. There should only be 1 return (pid are unique)

    postdate = post[1]
    title = post[2]
    body = post[3]
    poster = post[4]

    print()
    print("=" * 70)
    if IS_QUESTION:
        print("Poster:u/{0:<15} {1:<25} {2:<10}".format(poster,"Question", postdate))
    else:
        Qpid = db.execute("SELECT qid FROM answers WHERE answers.pid = ?",(pid, )).fetchall()[0][0] # return the pid of the Question
        print("Poster:u/{0:<15} Parent post:{1:<15} {2:<10}".format(poster,Qpid, postdate))

    

    print("-" * 70)
    if len(title) < 63:
        print("HERE")
        print("Title:",title)
    else:
        newtitle = _parse(title)
        print("Title:",newtitle)

    print()

    if len(body) < 63:
        print("HERE")
        print("Body: ",body)
    else:
        newbody = _parse(body)
        print("Body: ",newbody)

    print("=" * 70)
    print()

    return

def answer(conn, db, uid, quespid):
    '''
    Answer a Question
    '''
    checkReturn = db.execute("SELECT pid FROM questions WHERE questions.pid = ?",(quespid,)).fetchall()
    if checkReturn == []:
        print("Error: Selected post is not a Question.")
        return
    
    title, body = editor()
    if title.strip() == "" or body.strip() == "":
        print("Error: Title and Body cannot be empty.")
        return

    print()
    print("Please review your answer:")
    print("Title:", title)
    print("Body:")
    print(body)
    userInput = input("Do you want to post? (y/N) ")
    if userInput.strip() not in ['y', 'Y', "yes", "Yes", "YES"]:
        print("User discarded post.")
        time.sleep(0.5)
        print()
        return
    print("Posting...\n")

    maxpid = db.execute("SELECT MAX(pid) FROM posts").fetchall()
    if maxpid[0][0] != None:
        maxpidstr = maxpid[0][0][1:]
        if maxpidstr == "999":
            print("Error: Maximum posts reached. No more posts can be made.")
            return
        pidint = int(maxpidstr) + 1
        anspid = "p" + str(pidint).zfill(len(maxpidstr))
    else:
        anspid = "p000"

    pdate = datetime.date(datetime.now()) # pdate = current date

    db.execute("INSERT INTO posts VALUES (?,?,?,?,?)", (anspid, pdate, title, body, uid)) # insert answer into posts table
    db.execute("INSERT INTO answers VALUES (?,?)", (anspid, quespid)) #insert post into answer
    conn.commit()

    check1 = db.execute("SELECT posts.pid FROM posts WHERE posts.pid = ?", (anspid,))
    check2 = db.execute("SELECT answers.pid, answers.qid FROM answers WHERE answers.pid = ? AND answers.qid = ?", (anspid, quespid))
    if check1 != [] and check2 != []:
        print("Answer to {0} posted successfully!".format(quespid))
        print()
        time.sleep(0.5)
    else:
        print("Answer posting unsuccessful. Please try again later")
        print()
        time.sleep(0.5)

    return