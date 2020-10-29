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

def view(conn, db, uid, pid):
    '''
    detailed view of a post
    '''


def answer(conn, db, uid, quespid):
    '''
    Answer a Question
    '''
    checkReturn = db.execute("SELECT pid FROM questions WHERE questions.pid = ?",(quespid,)).fetchall()
    if checkReturn == []:
        print("Error: Selected post is not a Question.")
        return
    
    title, body = editor()

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
            print("Maximum posts reached. No more posts can be made.")
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