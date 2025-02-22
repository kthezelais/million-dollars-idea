import sqlite3, json, math
from flask import Flask, flash, render_template, redirect, session, request
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from auth import login_required, error_page

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

FIRST_PAGE = 1
OCCURRENCES = 10

# Function used to open a connection to the SQLite Database
def get_db_connection():
    conn = sqlite3.connect('mdi.db')
    # Enable FK and Cascade delete
    conn.cursor().execute("PRAGMA foreign_keys = ON")
    return conn

# Function used to convert a post from an array
# to a list with key/value pairs
def formatPost(post):
    return {
        "id": post[0],
        "user_id": post[1],
        "username": post[2],
        "title": post[3],
        "description": post[4],
        "tags": post[5],
        "stars": post[6],
        "liked": post[7],
        "createdAt": post[8],
        "updatedAt": post[9],
    }

# Parse a tag array to remove the id
# and keep only tag name
def parseTags(tags):
    return list(map(lambda x: x[1], tags))

# Convert an SQLite datetime value to only a date separated by slash
def formatDate(timestamp):
    return f"{timestamp[8:10]}/{timestamp[5:7]}/{timestamp[0:4]}"

# Format a datetime to keep only HH:MM:SS
def formatTime(timestamp):
    return f"{timestamp[12:]}"


@app.route("/", methods=["GET"])
@login_required
def index():
    try:
        page = FIRST_PAGE
        occurrences = OCCURRENCES
        if request.args.get("page") is not None and int(request.args.get("page")) > 0:
            page = int(request.args.get("page"))
    except:
        return error_page("Not found", code=404)

    sql_query = """
                SELECT posts.id, posts.user_id, users.username, posts.title, posts.description,
                    posts.tags, COUNT(stars.user_id) as stars,
                    CASE WHEN (
                        SELECT user_id
                        FROM stars
                        WHERE user_id = ? AND post_id = posts.id
                    ) IS NULL THEN 0 ELSE 1 END AS liked, posts.createdAt, posts.updatedAt
                FROM posts LEFT JOIN stars
                ON stars.post_id = posts.id
                LEFT JOIN users
                ON posts.user_id = users.id
                GROUP BY posts.id
                ORDER BY updatedAt
                DESC LIMIT ? OFFSET ?
                """

    if request.args.get("type") is not None and request.args.get("type") == "most-stared":
        sql_query = """
                    SELECT posts.id, posts.user_id, users.username, posts.title, posts.description,
                        posts.tags, COUNT(stars.user_id) as stars,
                        CASE WHEN (
                            SELECT user_id
                            FROM stars
                            WHERE user_id = ? AND post_id = posts.id
                        ) IS NULL THEN 0 ELSE 1 END AS liked, posts.createdAt, posts.updatedAt
                    FROM posts LEFT JOIN stars
                    ON stars.post_id = posts.id
                    LEFT JOIN users
                    ON posts.user_id = users.id
                    GROUP BY posts.id
                    ORDER BY stars
                    DESC LIMIT ? OFFSET ?
                    """

    post = []
    conn = get_db_connection()
    cur = conn.cursor()

    if request.args.get("tag") is not None:
        sql_query = sql_query[:len(sql_query) - 38]
        posts = cur.execute(sql_query, (session["user_id"],)).fetchall()
    else:
        posts = cur.execute(sql_query, (session["user_id"], occurrences, occurrences * (page - 1))).fetchall()

    nb_posts = cur.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    nb_pages = math.ceil(nb_posts / occurrences)

    if page > nb_pages:
        return error_page("Not found", code=404)

    data = []

    for post in posts:
        post = formatPost(post)
        post["createdAt"] = formatDate(post["createdAt"])
        post["updatedAt"] = formatDate(post["updatedAt"])

        if request.args.get("tag") is None:
            data.append(post)
        elif set(request.args.get("tag").split('-')).issubset(set(post["tags"].split("-"))):
            data.append(post)

    if request.args.get("tag") is not None:
        nb_pages = math.ceil(len(data) / occurrences)
        stringTags = request.args.get("tag").split("-")
        parsedTags = cur.execute("SELECT id, name FROM tags WHERE id IN (%s)" % ",".join("?"*len(stringTags)), stringTags).fetchall()
        tags = parsedTags

        if len(data) > 10:
            data = data[occurrences * (page - 1):occurrences * page]

        conn.close()
        return render_template("index.html", posts=data, nb_pages=nb_pages, page=page, tags=tags)

    conn.close()
    return render_template("index.html", posts=data, nb_pages=nb_pages, page=page)


@app.route("/error", methods=["GET", "POST"])
def error():
    return render_template("error.html", code=404, message="Test error")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return error_page("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error_page("must provide password", 403)

        # Query database for username
        conn = get_db_connection()
        cur = conn.cursor()

        rows = cur.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return error_page("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        conn.close()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    if session.get("user_id") is not None:
        return redirect("/")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        if session.get("user_id") is not None:
            return redirect("/")
        return render_template("register.html")
    try:
        # Check user inputs
        if not request.form.get("username"):
            return error_page("Username must be filled")
        elif not request.form.get("password"):
            return error_page("Password must be filled")
        elif not request.form.get("confirmation"):
            return error_page("Confirmation password must be filled")
        elif request.form.get("password") != request.form.get("confirmation"):
            return error_page("Password and Confirmation password doesn't match")

        # Prepare user credentials to add in db
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))

        conn = get_db_connection()
        cur = conn.cursor()

        rows = cur.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()
        if len(rows) != 0:
            return error_page("Username already exist")

        # Add new user credentials to db
        cur.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hash))
        conn.commit()
    except ValueError:
        conn.close()
        # Return error if inputed username already exist
        return error_page("Username already exist")

    conn.close()
    # Redirect user to main page
    flash("Registered!")
    return render_template("login.html")


@app.route("/settings")
@login_required
def settings():
    """Handle user settings"""
    conn = get_db_connection()
    cur = conn.cursor()
    username = cur.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0]
    conn.close()
    return render_template("settings.html", username=username)


@app.route("/reset-password", methods=["POST"])
@login_required
def reset_password():
    if request.form.get("password") is None:
        return error_page("Missing password")
    elif request.form.get("new-password") is None:
        return error_page("Missing new password")
    elif request.form.get("confirmation") is None:
        return error_page("Missing password confirmation")

    password = request.form.get("password")
    new_password = request.form.get("new-password")
    confirmation = request.form.get("confirmation")

    if new_password != confirmation:
        return error_page("New password and confirmation doesn't match")

    conn = get_db_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT hash FROM users WHERE id = ?",
                       (session["user_id"],)).fetchall()

    # Ensure password is correct
    if len(rows) != 1 or not check_password_hash(
        rows[0][0], password
    ):
        return error_page("Wrong password", 403)

    cur.execute("UPDATE users SET hash = ? WHERE id = ?", (generate_password_hash(new_password), session["user_id"]))

    conn.commit()
    conn.close()
    flash("Password updated with success!")
    return redirect("/")


@app.route("/delete-account")
@login_required
def delete_account():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get the list of posts ids created by connected user
    cur.execute("DELETE FROM users WHERE id = ?", (session["user_id"],))

    conn.commit()
    conn.close()

    session.clear()

    flash("Your account has been successfully deleted!")
    return redirect("/login")


@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if request.method == "GET":
        return render_template("post.html")

    if request.form.get("title") is None:
        return error_page("Missing title")
    elif request.form.get("tags") is None:
        return error_page("Missing tags")
    elif request.form.get("description") is None:
        return error_page("Missing description")

    title = request.form.get("title")
    tags = request.form.get("tags")
    description = request.form.get("description")

    conn = get_db_connection()
    cur = conn.cursor()

    tagsParsed = json.loads(tags)

    for tag in tagsParsed:
        res = cur.execute("SELECT * FROM tags WHERE name LIKE ?", (f"%{tag["name"]}%",)).fetchall()

        if len(res) == 0:
            cur.execute("INSERT INTO tags (name) VALUES (?)", (tag["name"][0].upper() + tag["name"][1:].lower(),))
            conn.commit()

    tagsSQLFormated = list(map(lambda x: x['name'], tagsParsed))
    tagIDsSQLFormated = cur.execute("SELECT id FROM tags WHERE name IN (%s)" % ",".join("?"*len(tagsSQLFormated)), tagsSQLFormated).fetchall()

    cur.execute("INSERT INTO posts (user_id, title, description, tags) VALUES (?, ?, ?, ?)", (session["user_id"], title, description, '-'.join(list(map(lambda x: str(x[0]), tagIDsSQLFormated)))))
    conn.commit()

    print(f"{title}, {description}, {'-'.join(list(map(lambda x: str(x[0]), tagIDsSQLFormated)))}")

    conn.close()
    flash(f"'{title}' has been posted!")
    return redirect("/")


@app.route("/tags", methods=["GET", "POST"])
@login_required
def tags():
    if request.method == "GET":
        if request.args.get("search") is None:
            return []

        conn = get_db_connection()
        cur = conn.cursor()

        res = cur.execute("SELECT * FROM tags WHERE name LIKE ?", (f"%{request.args.get("search")}%",)).fetchall()

        conn.close()
        return res
    return []


@app.route("/view", methods=["GET"])
@login_required
def view():
    if request.args.get("id") is None or int(request.args.get("id")) < 0:
        return error_page("Not found", code=404)

    conn = get_db_connection()
    cur = conn.cursor()

    post = formatPost(cur.execute("""
                        SELECT posts.id, posts.user_id, users.username, posts.title, posts.description,
                            posts.tags, COUNT(stars.user_id) as stars,
                            CASE WHEN (
                                SELECT user_id
                                FROM stars
                                WHERE user_id = ? AND post_id = ?
                            ) IS NULL THEN 0 ELSE 1 END AS liked, posts.createdAt, posts.updatedAt
                        FROM posts LEFT JOIN stars
                        ON stars.post_id = posts.id
                        LEFT JOIN users
                        ON posts.user_id = users.id
                        WHERE posts.id = ?
                        """, (session["user_id"], request.args.get("id"), request.args.get("id"))).fetchone())

    stringTags = post["tags"].split("-")
    parsedTags = parseTags(cur.execute("SELECT id, name FROM tags WHERE id IN (%s)" % ",".join("?"*len(stringTags)), stringTags).fetchall())
    post["tags"] = parsedTags
    post["updatedAt"] = f"{formatDate(post["updatedAt"])} at {formatTime(post["updatedAt"])}"
    post["createdAt"] = f"{formatDate(post["createdAt"])} at {formatTime(post["createdAt"])}"

    conn.close()
    return render_template("view.html", post=post)


@app.route("/star", methods=["GET"])
@login_required
def star():
    if request.args.get("post_id") is None:
        return None

    conn = get_db_connection()
    cur = conn.cursor()
    post_id = request.args.get("post_id")

    stars = cur.execute("SELECT * FROM stars WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()

    if len(stars) > 0:
        cur.execute("DELETE FROM stars WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id))
    else:
        cur.execute("INSERT INTO stars (user_id, post_id) VALUES (?, ?)", (session["user_id"], post_id))

    conn.commit()
    conn.close()
    return {}


@app.route("/edit-post", methods=["GET", "POST"])
@login_required
def editPost():
    # GET method treatment
    if request.method == "GET":
        if request.args.get("post_id") is None:
            return error_page("Not Found", code=404)

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            post = formatPost(cur.execute("""
                            SELECT posts.id, posts.user_id, users.username, posts.title, posts.description,
                                posts.tags, COUNT(stars.user_id) as stars,
                                CASE WHEN (
                                    SELECT user_id
                                    FROM stars
                                    WHERE user_id = ? AND post_id = ?
                                ) IS NULL THEN 0 ELSE 1 END AS liked, posts.createdAt, posts.updatedAt
                            FROM posts LEFT JOIN stars
                            ON stars.post_id = posts.id
                            LEFT JOIN users
                            ON posts.user_id = users.id
                            WHERE posts.id = ?
                            """, (session["user_id"], request.args.get("post_id"), request.args.get("post_id"))).fetchone())

            stringTags = post["tags"].split("-")
            parsedTags = cur.execute("SELECT id, name FROM tags WHERE id IN (%s)" % ",".join("?"*len(stringTags)), stringTags).fetchall()
            post['tags'] = parsedTags
            post['updatedAt'] = formatDate(post['updatedAt'])
            post['createdAt'] = formatDate(post['createdAt'])
        except:
            conn.close()
            return error_page("Not Found", code=404)

        conn.close()
        return render_template("post.html", post=post)
    # POST method treatment
    if request.form.get("post_id") is None:
        return error_page("Not Found", code=404)
    elif request.form.get("title") is None:
        return error_page("Missing title")
    elif request.form.get("tags") is None:
        return error_page("Missing tags")
    elif request.form.get("description") is None:
        return error_page("Missing description")

    title = request.form.get("title")
    tags = request.form.get("tags")
    description = request.form.get("description")
    post_id = request.form.get("post_id")

    conn = get_db_connection()
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM posts WHERE user_id = ? AND id = ?", (session["user_id"], post_id)).fetchall()
    if len(rows) != 1:
        conn.close()
        return error_page("Not Found", code=404)

    tagsParsed = json.loads(tags)

    for tag in tagsParsed:
        res = cur.execute("SELECT * FROM tags WHERE name LIKE ?", (f"%{tag["name"]}%",)).fetchall()

        if len(res) == 0:
            cur.execute("INSERT INTO tags (name) VALUES (?)", (tag["name"][0].upper() + tag["name"][1:].lower(),))
            conn.commit()

    tagsSQLFormated = list(map(lambda x: x['name'], tagsParsed))
    tagIDsSQLFormated = cur.execute("SELECT id FROM tags WHERE name IN (%s)" % ",".join("?"*len(tagsSQLFormated)), tagsSQLFormated).fetchall()

    cur.execute("""
                UPDATE posts
                SET user_id = ?, title = ?, description = ?, tags = ?, updatedAt = current_timestamp
                WHERE user_id = ? AND id = ?
                """, (session["user_id"], title, description, '-'.join(list(map(lambda x: str(x[0]), tagIDsSQLFormated))), session["user_id"], post_id))
    conn.commit()

    print(f"title: {title}\ndescription: {description[0:50]}...\ntags: {'-'.join(list(map(lambda x: str(x[0]), tagIDsSQLFormated)))}")

    conn.close()
    flash(f"'{title}' has been updated!")
    return redirect("/")


@app.route("/delete-post", methods=["GET"])
@login_required
def deletePost():
    if request.args.get("post_id") is None:
        return error_page("Not Found", code=404)
    post_id = request.args.get("post_id")

    conn = get_db_connection()
    cur = conn.cursor()

    rows = cur.execute("SELECT title FROM posts WHERE user_id = ? AND id = ?", (session["user_id"], post_id)).fetchall()

    if len(rows) != 1:
        conn.close()
        return error_page("Not Found", code=404)

    cur.execute("DELETE FROM posts WHERE user_id = ? AND id = ?", (session["user_id"], post_id))
    conn.commit()

    conn.close()
    flash(f"Idea '{rows[0][0]}' has been successfully deleted!")
    return redirect("/")


@app.route("/my-ideas", methods=["GET", "POST"])
@login_required
def myIdeas():
    if request.method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()

        username = cur.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0]

        sql_query = """
            SELECT posts.id, posts.user_id, users.username, posts.title, posts.description,
                posts.tags, COUNT(stars.user_id) as stars,
                CASE WHEN (
                    SELECT user_id
                    FROM stars
                    WHERE user_id = ? AND post_id = posts.id
                ) IS NULL THEN 0 ELSE 1 END AS liked, posts.createdAt, posts.updatedAt
            FROM posts LEFT JOIN stars
            ON stars.post_id = posts.id
            LEFT JOIN users
            ON posts.user_id = users.id
            WHERE posts.user_id = ?
            GROUP BY posts.id
            ORDER BY updatedAt
            """

        if request.args.get("type") is not None and request.args.get("type") == "most-stared":
            sql_query = """
                        SELECT posts.id, posts.user_id, users.username, posts.title, posts.description,
                            posts.tags, COUNT(stars.user_id) as stars,
                            CASE WHEN (
                                SELECT user_id
                                FROM stars
                                WHERE user_id = ? AND post_id = posts.id
                            ) IS NULL THEN 0 ELSE 1 END AS liked, posts.createdAt, posts.updatedAt
                        FROM posts LEFT JOIN stars
                        ON stars.post_id = posts.id
                        LEFT JOIN users
                        ON posts.user_id = users.id
                        WHERE posts.user_id = ?
                        GROUP BY posts.id
                        ORDER BY stars
                        """

        data = []
        posts = cur.execute(sql_query, (session["user_id"], session["user_id"])).fetchall()

        for post in posts:
            post = formatPost(post)
            stringTags = post["tags"].split("-")
            parsedTags = parseTags(cur.execute("SELECT id, name FROM tags WHERE id IN (%s)" % ",".join("?"*len(stringTags)), stringTags).fetchall())
            post["tags"] = parsedTags
            post["createdAt"] = formatDate(post["createdAt"])
            post["updatedAt"] = formatDate(post["updatedAt"])
            data.append(post)

        conn.close()
        return render_template("my_ideas.html", username=username, posts=data)
    return None

