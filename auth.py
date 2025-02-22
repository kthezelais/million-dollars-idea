from flask import redirect, render_template, session
from functools import wraps


def login_required(f):
    """
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/#login-required-decorator
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def error_page(message, code=400):
    """
    Return error page from a message and a code
    """
    return render_template("error.html", code=code, message=message)
