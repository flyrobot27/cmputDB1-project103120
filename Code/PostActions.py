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
    # rows, cols = stdscr.getmaxyx()   # get display dimention of the console # This is causing issues with the lab machines
    rows, cols = 15, 90

    win = curses.newwin(rows, cols, begin_y, begin_x)   # create window
    textstr = "Edit your post here. Press Ctrl + G to switch and exit."
    win.addstr(begin_y, begin_x, textstr)
    win.addstr(begin_y + 1, begin_x, "Title:")
    win.addstr(begin_y + 3, begin_x, "Body:")
    win.addstr(rows - 3, begin_x, "-" * len(textstr))
    win.refresh()

    # initialize subwindow
    titlewin = win.subwin(1, cols ,begin_y + 2, begin_x)
    titlewin.addstr(0, 0, pretitle[:cols - 1]) # if a previous post title is supplied load the previous post

    bodywin = win.subwin(rows - 7, cols ,begin_y + 4, begin_x)
    
    bodytext = prebody.split('\n')
    i = 0
    for text in bodytext:
        bodywin.addstr(i, 0, text[:cols]) # load previous post body. If the line is too long chop off
        i += 1

    # refresh previous text
    bodywin.refresh()
    titlewin.refresh()

    replywin = win.subwin(1, 5, rows - 2, begin_x + 22)
    redisplay = win.subwin(1, 22, rows - 2, begin_x)

    while True:
        title = curses.textpad.Textbox(titlewin, insert_mode=True).edit()
        bodywin.refresh() # refresh to update cursor location
        body = curses.textpad.Textbox(bodywin, insert_mode=True).edit()

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

def _print_text(title, body):
    '''
    A simple function to print the title and body
    '''

    def _parse(text):
        '''
        Parse the given text to the length 90
        '''

        newtext = list(text)
        accu = 0
        i = 0
        while i < len(text):
            if newtext[i] == '\n':
                accu = 0
                i += 1
            else:
                if accu > 88:
                    if newtext[i] == " ":
                        newtext.insert(i+1, '\n')
                    elif newtext[i - 1] == " ":
                        newtext.insert(i, '\n')
                    else:
                        newtext.insert(i, "-\n")

                    accu = 0
                else:
                    accu += 1
                
                i += 1

        return ''.join(newtext)

    print("-" * 90)
    if len(title) < 83:
        print("Title:",title)
    else:
        newtitle = _parse(title)
        print("Title:")
        print(newtitle)

    print("- " * 45)

    if len(body) < 83:
        print(body)
    else:
        newbody = _parse(body)
        print()
        print(newbody)
    
def view(conn, db, uid, pid):
    '''
    detailed view of a post
    '''

    post = db.execute("SELECT posts.* FROM posts WHERE posts.pid = ?",(pid,)).fetchall() # extract post
    if post == []:
        print("Error: post with pid[{0}] does not exist".format(pid))
        return
    post = post[0]

    answers = list()
    checkQues = db.execute("SELECT pid FROM questions WHERE questions.pid = ?",(pid,)).fetchall() # check if it is a question
    IS_QUESTION = False
    if checkQues != [] and checkQues[0][0] == pid:
        IS_QUESTION = True
        answerpids = db.execute("SELECT answers.pid FROM answers WHERE answers.qid = ?",(pid,)).fetchall() # Get answers pid
        for apid in answerpids:
            apid = apid[0] # results are in tuples, need to extract the result out
            text = db.execute("SELECT posts.* FROM posts WHERE posts.pid = ?",(apid,)).fetchall() # get content of answer
            answers.append(text[0]) # remove the outer list from the return. There should only be 1 return (pid are unique)

    postdate = post[1]
    title = post[2]
    body = post[3]
    poster = post[4]

    print()
    if IS_QUESTION:
        # Check for theaid
        try:
            theaid = db.execute("SELECT questions.theaid FROM questions WHERE questions.pid = ?",(pid,)).fetchall()[0][0]
        except IndexError:
            theaid = None

        print("Viewing Question {0}".format(pid))
        print("=" * 90)
        print("Poster:u/{0:<25} {1:^20} {2:>28}".format(poster,"Question", postdate))
        _print_text(title, body)
        i = 1
        print("=" * 90)
        print()
        # Print the answers
        if len(answers) == 0:
            print("(No answers)")

        for ans in answers:
            Apid = ans[0]
            if Apid == theaid:
                print("{0:^90}".format("*** Accepted Answer ***"))
            print("Answer {0}/{1}:".format(i,len(answers)))
            Adate = ans[1]
            Atitle = ans[2]
            Abody = ans[3]
            Aposter = ans[4]
            print("Poster:u/{0:<25} AnswerPID:{1:<15} {2:>24}".format(Aposter,Apid, Adate))
            _print_text(Atitle, Abody)
            print("=" * 90)
            i += 1
        print()

    else:
        print("Viewing Answer {0}".format(pid))
        print("=" * 90)
        Qpid = db.execute("SELECT qid FROM answers WHERE answers.pid = ?",(pid, )).fetchall()[0][0] # return the pid of the Question
        print("Poster:u/{0:<25} Parent post:{1:<20} {2:>20}".format(poster,Qpid, postdate))
        _print_text(title, body)
        print()
        # get the parent post (Question)
        result = db.execute("SELECT posts.title, posts.body, posts.pdate, posts.poster FROM posts WHERE posts.pid = ?",(Qpid,)).fetchall()[0]
        print("= "*45)
        print()
        print("Viewing Parent post:{0:<20} Poster:u/{1:<10} {2:>27}".format(Qpid, result[3], result[2]))
        _print_text(result[0], result[1])
        print("="*90)
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

def vote(conn, db, uid, pid):
    '''
    Upvote the given post. Return if user already voted
    '''

    # check if user has already upvoted
    check = db.execute("SELECT votes.vdate FROM votes WHERE votes.pid = ? AND votes.uid = ?",(pid, uid)).fetchall()
    if check != []:
        print("Error: You have already upvoted this post on {0}".format(check[0][0]))
        return

    vno = db.execute("SELECT IFNULL(COUNT(DISTINCT votes.vno),0) FROM votes WHERE votes.pid = ?", (pid,)).fetchall()[0][0]

    vdate = datetime.date(datetime.now()) # get current date

    if type(vno) == int:
        vno = int(vno) + 1
        db.execute("INSERT INTO votes VALUES(?,?,?,?)",(pid,vno,vdate,uid))
        conn.commit()
    else:
        raise ValueError("Internal Database Error: vno type is not int")

def markacc(conn, db, Apid):
    '''
    Mark the answer as the accepted answer to to the assosiated question
    For privileged users only
    '''

    Qpid = db.execute("SELECT answers.qid FROM answers WHERE answers.pid = ?",(Apid,)).fetchall()
    if Qpid == []:
        print("Error: {0} is not an answer to a question".format(Apid))
        return
    
    Qpid = Qpid[0][0]

    # check if there already is an accepted answer
    check = db.execute("SELECT IFNULL(questions.theaid, 0) FROM questions WHERE questions.pid = ?",(Qpid,)).fetchall()
    if check != [] and check[0][0] != 0:
        theaid = check[0][0]
        userInput = input("There is already an accepted answer {0}. Do you want to change it to {1}? (y/N)".format(theaid, Apid))
        if userInput.strip() not in ['y', 'Y', "yes", "Yes", "YES"]:
            print("User rejected change. Accepted answer is {0}".format(theaid))
            return
    
    db.execute("UPDATE questions SET theaid = ? WHERE pid = ?",(Apid, Qpid))
    conn.commit()
    print("Accepted answer for {0} updated to {1}".format(Qpid, Apid))
    return

def givebdg(conn, db, pid):
    '''
    Give a badge to the poster of the post. For privileged users only
    '''

    poster = db.execute("SELECT poster FROM posts WHERE posts.pid = ?",(pid,)).fetchall()
    if poster == []:
        print("Error: post with PID[{0}] does not exist".format(pid))
        return
    else:
        poster = poster[0][0]

    bdate = datetime.date(datetime.now()) # get current date

    # check if user already received badges today
    check = db.execute("SELECT * FROM ubadges WHERE uid = ? AND bdate = ?",(poster, bdate)).fetchall()
    if check != []:
        print("Error: User u/{0} has already received a badge today.".format(poster))
        return

    results = db.execute("SELECT bname, type FROM badges").fetchall()
    btypes = set([bt[1] for bt in results])
    print("Avaliable badges:")
    for types in btypes:
        print("{0} badges:".format(types))
        for badges in results:
            if badges[1] == types:
                print("\t",badges[0])
        print()

    userInput = input("Which badge do you want to give to u/{0}? >>> ".format(poster)).lower().lstrip().rstrip() # lower the input and strip leading/trailing spaces
    avaliablebdg = [bt[0].lstrip().rstrip() for bt in results]

    if userInput not in avaliablebdg:
        print("Error: invalid badge name")
        return

    bname = userInput
    uid = poster
    db.execute("INSERT INTO ubadges VALUES(?,?,?)",(uid,bdate,bname))
    conn.commit()

    print("Successfully given [{0}] to u/{1}.".format(bname, uid))
    print()
    return

def tag(conn, db, pid, tagName):
    '''
    Tag a post. For privileged users only.
    '''

    check = db.execute("SELECT posts.pid FROM posts WHERE posts.pid = ?",(pid,)).fetchall()
    if check == []:
        print("Error: post with PID[{0}] does not exist".format(pid))
        return

    def _insertTag(conn, db, pid, tagName):
        ''' insert tag function '''
        db.execute("INSERT INTO tags VALUES(?,?)",(pid,tagName))
        conn.commit()
        print("Successfully tagged post [{0}] with tag [{1}].".format(pid, tagName))
        return

    # Get if post has any tag
    existingTags = db.execute("SELECT tags.tag FROM tags WHERE tags.pid = ?",(pid,)).fetchall()
    if not existingTags:
        _insertTag(conn, db, pid, tagName)
        return
    else:
        # check if tag is already added
        check = db.execute("SELECT tags.tag FROM tags WHERE tags.pid = ? AND tags.tag LIKE ?",(pid, "%"+tagName+"%")).fetchall()
        if not check:
            _insertTag(conn, db, pid, tagName)
        else:
            print("Error: tag [{0}] already added for post [{1}]".format(tagName, pid))
            return

def edit_post(conn, db, pid):
    '''
    Edit a given post. For privileged users only
    '''
    # fetch the post
    post = db.execute("SELECT posts.title, posts.body FROM posts WHERE posts.pid = ?",(pid,)).fetchall()
    if post == []:
        print("Error: post [{0}] does not exist.".format(pid))
        return
    
    # extract post title and body
    pretitle = post[0][0]
    prebody = post[0][1]
    # call the editor
    newtitle, newbody = editor(pretitle, prebody)

    # Preview post after edit
    print()
    print("Preview of edited post [{0}]:".format(pid))
    print("=" * 90)
    _print_text(newtitle, newbody)
    print("=" * 90)
    print()

    # Confirm edit
    userInput = input("Confirm edit? (y/N) ")
    if userInput.strip() not in ['y', 'Y', "yes", "Yes", "YES"]:
        print("User discarded edit.")
        return
    
    db.execute("UPDATE posts SET title = ?, body = ? WHERE pid = ?",(newtitle, newbody, pid))
    conn.commit()
    print("Successfully edited post [{0}].".format(pid))
    return
