try:
    import sqlite3
    import time
    from datetime import datetime
    import PostActions
except ImportError as args:
    print("Import Error:",args)
    exit(1)

def display_result(columnNames, result, displayStart, resultLength):
    '''
    Display results in a command line table
    columnNames and results will be tuple of strings or integer
    It will only display at most 5 results
    '''
    if resultLength == 0:
        print()
        print("Empty Result, try a different keyword(s)")
        print()
        return

    displayEnd = displayStart + 5  # at most 5 results per page
    if displayEnd >= resultLength: # prevent integer overflow
        displayEnd = resultLength

    displayResult = [list(r) for r in result[displayStart:displayEnd]]
    # Format result to ensure they do not exceed specific length
    for text in displayResult:
        # remove newline and tab
        for i in range(len(text)):
            text[i] = str(text[i]).replace('\n','')
            text[i] = str(text[i]).replace('\t',' ')

        # length check
        if len(text[3]) > 30:
            text[3] = text[3][:27]
            text[3] += "..."

        if len(text[4]) > 50:
            text[4] = text[4][:47]
            text[4] += "..."
        
        if len(text[5]) > 10:
            text[5] = text[5][:7]
            text[5] += "..."
    print()
    print('='*145)
    print("{0:<10}  {1:<5}  {2:<10}  {3:<30}  {4:<50}  {5:<10}  {6:<6}  {7:<9}".format(*columnNames))
    print("-"*10+"  "+"-"*5+"  "+"-"*10+"  "+"-"*30 + "  "+ "-"*50+ "  "+"-"*10+"  "+"-"*6+"  "+"-"*9) 
    for text in displayResult:
        print("{0:<10}  {1:<5}  {2:<10}  {3:<30}  {4:<50}  {5:<10}  {6:<6}  {7:<9}".format(*text))
    print('='*145)
    print("Displaying Result ({0}-{1})/{2}".format(str(displayStart + 1), displayEnd, resultLength))
    print()
    return

def choose_actions(conn, db, uid, result, keywords):
    '''
    Performs actions after searching for post:
    Post action-Answer
    Post action-Vote

    For privileged users:
    Post action-Mark as the accepted
    Post action-Give a badge
    Post action-Add a tag
    Post Action-Edit
    '''
    
    IS_PRIVILEGED = False
    CMD_CHAR = '$'
    findprivilege = db.execute("SELECT uid FROM privileged WHERE uid = ?", (uid,)).fetchall()
    if findprivilege != []:
        IS_PRIVILEGED = True
        CMD_CHAR = '#'

    # item format:
    columnNames = ("PostType","PID","Date","Title","Body","Poster","Votes","ansCount")
    resultLength = len(result)

    displayStart = 0   
    display_result(columnNames, result, displayStart, resultLength)

    # all users can have these actions
    actions = [".h",".answer",".vote",".next",".prev",".quit",".view",".show"]

    # only privileged users can have these actions
    privAct = [".markacc",".givebdg",".tag",".edit"]

    userInput = input("[u/{0} (.h for help)]{1} ".format(uid, CMD_CHAR))
    while userInput.strip() not in [".q", ".quit"]:
        try:
            #Extract command
            if userInput.strip() != '':
                cmd = userInput.split()[0].strip().lower()
                # check command
                if cmd not in actions:
                    if IS_PRIVILEGED and (cmd not in privAct):
                        raise SyntaxError
                    elif not IS_PRIVILEGED:
                        raise SyntaxError

                # only certain command will have second argv
                if cmd not in [".h", ".next", ".prev", ".q", ".quit",".show"]:
                    userPID = userInput.split()[1].strip().lower()

                    if cmd == ".tag": # user need to specify tag
                        tagName = ' '.join(userInput.split()[2:])
            else:
                cmd = None
        except IndexError:
            print("Error: {0}: missing arguments...".format(userInput))
        except SyntaxError:
            print("Error {0}: Invalid command...".format(userInput))
        else:
            if cmd == ".h":
                print("Avaliable Actions:")
                print("\tRefresh page:       .show")
                print("\tView post:          .view [PID]")
                print("\tView next page:     .next")
                print("\tView previous page: .prev")
                print("\tAnswer a question:  .answer [PID]")
                print("\tVote a post:        .vote [PID]")
                print("\tQuit this search:   .q / .quit")
                if IS_PRIVILEGED:
                    print()
                    print("Special actions:")
                    print("\tMark as accepted Ans:   .markacc [PID]")
                    print("\tGive badge to poster:   .givebdg [PID]")
                    print("\tAdd a tag:              .tag [PID] [tag name]")
                    print("\tEdit post:              .edit [PID]")

            elif cmd ==".show":
                # Refresh the result table
                result = search_post(conn, db, uid, keywords)
                resultLength = len(result)
                display_result(columnNames, result, displayStart, resultLength)

            elif cmd == ".view":
                PostActions.view(conn, db, uid, userPID)

            elif cmd == ".prev": # view previous page
                if (displayStart - 5) < 0: # i.e. already on most previous result
                    print("Error: This is the first page.")
                else:
                    displayStart -= 5
                    display_result(columnNames, result, displayStart, resultLength)
                    

            elif cmd == ".next":
                if (displayStart + 5) >= resultLength:
                    print("Error: This is the last page.")
                else:
                    displayStart += 5
                    display_result(columnNames, result, displayStart, resultLength)

            elif cmd == ".answer":
                PostActions.answer(conn, db, uid, userPID)

            elif cmd == ".vote":
                PostActions.vote(conn, db, uid, userPID)

            elif IS_PRIVILEGED:
                if cmd == ".markacc":
                    PostActions.markacc(conn, db, userPID)
                elif cmd == ".givebdg":
                    PostActions.givebdg(conn, db, userPID)
                elif cmd == ".tag":
                    PostActions.tag(conn, db, userPID, tagName)
                elif cmd == ".edit":
                    PostActions.edit_post(conn, db, userPID)
                    
        # finally
        userInput = input("[u/{0}]{1} ".format(uid, CMD_CHAR))

    print("*-----------------------*")
    return

def search_post(conn, db, uid, keywords):
    ''' 
    search a post in the database. Return the matching posts 
    '''
    if len(keywords) == 0:
        # If no keyword is supplied, return all posts, sort by newest
        result = db.execute("""
        SELECT 
            CASE
                WHEN posts.pid = questions.pid THEN
                    "Question"
                ELSE
                    "Answer"
                END checkqa,
            posts.*,
            IFNULL(COUNT(DISTINCT votes.vno), 0) vcnt,
            CASE
                WHEN posts.pid = questions.pid THEN
                    COUNT(DISTINCT answers.pid)
                ELSE
                    "N/A"
                END countanswers
            FROM posts LEFT JOIN answers ON posts.pid = answers.qid
            LEFT JOIN votes ON votes.pid = posts.pid
            LEFT JOIN questions ON questions.pid = posts.pid
            GROUP BY posts.pid
            ORDER BY posts.pdate DESC
        """).fetchall()
    else:
        # search for supplied keyword
        query = """
        SELECT 
            CASE
                WHEN posts.pid = questions.pid THEN
                    "Question"
                ELSE
                    "Answer"
                END checkqa,
            posts.*,
            IFNULL(COUNT(DISTINCT votes.vno), 0) vcnt,
            CASE
                WHEN posts.pid = questions.pid THEN
                    COUNT(DISTINCT answers.pid)
                ELSE
                    "N/A"
                END countanswers
            FROM posts LEFT JOIN answers ON posts.pid = answers.qid
            LEFT JOIN questions ON questions.pid = posts.pid
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

    return result

def post_question(conn, db, uid):
    ''' 
    post a question to the database 
    '''
    title, body = PostActions.editor()

    if title.strip() == "" or body.strip() == "":
        print()
        print("Error: Title and/or body cannot be empty.")
        print()
        time.sleep(1)
        return

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
            print("Error: Maximum posts reached. No more posts can be made.")
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
            print("Please enter keyword(s) to search. Press Enter to search.")
            words = input(">>> ").lower()  # lower the case of all keywords as the search is case insensitive
            keywords = tuple(words.split())
            time.sleep(0.5)
            result = search_post(conn, db, uid, keywords)
            choose_actions(conn, db, uid, result, keywords)

        elif userInput == 3:
            time.sleep(0.5)
            return
