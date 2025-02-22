# Million $ Idea
#### Video Demo:  https://youtu.be/GFfsWAZUblQ

## Description:
I chose this stack for its simplicity since I'm working alone on this project and I feel pretty confortable with it.

I called this website **Million $ Idea**: this project is inspired by an old website I've been using a few years ago, and which doesn't exist anymore as far as I can tell.
The idea is pretty simple: have you ever been in this situation where you have a very good idea, but you don't have neither the skill set, the time, the budget, or just the motivation to put your time on it? But you still think "if this thing existed, I would buy it with no hesitation!".

And here we are! This website provides a place where you can publish your ideas, and see ideas of other people by hoping, one day, someone with the skill set, the budget, and enough motivation, will take the time needed to bring your idea to life!

On the other hand, it is not always easy to find a project to work on, to find a good idea that will keep you motivated. And thanks to **Million $ Idea**, you will now see other people ideas, and scroll the feed until you find the "perfect idea" for your project!

## Project stack
My project is a website I developed using the same Flask stack we've been using for the previous CS50 section including:
- HTML/CSS
- Javascript
- Jinja
- Python/Flask
- SQLite
- Material Design CSS template (used for a few styled components)

I've also used ChatGPT to create set of dummy data to inject into my SQL database.
The entire project has been developed using the CS50 environment.

To run the project, make sure you are under **project/** directory, and then start the flask project:
```bash
flask run
```

## Features list
The website is pretty simple in its features:
1. You register
2. You login with your credentials
3. You can then consult other people ideas by scrolling the website feed, but also:
    - Sort the feed by most stared or latest posted ideas
    - Filter by categories/tags
    - Give a star to any idea you'd like
    - Publish your own ideas!

On the other side, you can also:
1. Update/Delete your posts at any time!
2. Consult and manage your own ideas
3. Logout
4. In Settings:
    - Edit your password
    - Delete your account

## Project structure
Below is the list of files for the website:
```
.
├── app.py
├── auth.py
├── init_db.sql
├── mdi.db
├── README.md
├── static/
└── templates/
    ├── auth_form.html
    ├── error.html
    ├── index.html
    ├── layout.html
    ├── login.html
    ├── my_ideas.html
    ├── pagination.html
    ├── post.html
    ├── register.html
    ├── settings.html
    ├── star_mgmt.html
    └── view.html

2 directories, 17 files
```

- **app.py**:  main file used by the flask app to configure all endpoints, which are:
    - ***GET "/"***: main page of the website which require to be logged in: if logged in, redirect user to the feed. Otherwise, redirect to login page.
    - ***GET "/logout"***: clear the session and redirect user to "/" which will redirect user to login page then.
    - ***GET "/login"***: return the login page form.
    - ***POST "/login"***: handle credentials sent by user from GET request and open a session if credentials are correct.
    - ***GET "/register"***: return the register page form.
    - ***POST "/register"***: handle the credentials send by user from GET request and create the account if the username doesn't exist yet.
    - ***GET "/settings"***: return a simple page with 2 buttons the user can click on:
        -  Reset password: display a pop-up window with a form.
        -  Delete account: display a pop-up window asking user confirmation before proceeding.
    - ***POST "/reset-password"***: handle form sent by user from settings pop-up, and check if current password is correct as well as new password and confirmation match, then update the password hash in database and redirect user on feed page.
    - ***GET "/delete-account"***: check if the user is logged in, close the session, delete the account and redirect to the login page.
    - ***GET "/post"***: return a formular to post a new idea.
    - ***POST "/post"***: handle form sent by user from previous formular, and add the new post to the database.
    - ***GET "/tags"***: return the list of tags stored in the database. This endpoint is mostly used by javascript request when the user is trying to filter on the main page by tags/categories, or when looking for an existing tag when creating/updating a post.
    - ***POST "/tags"***: this endpoint is used to create a new tag by adding it in the database. This on is only used when create/update post are sent.
    - ***GET "/view"***: display a specific idea with a bit more details. User can achieve that by clicking on the title of any post from the feed. If the logged user is the author of the post, buttons "DELETE" and "UPDATE" show be displayed.
    - ***GET "/star"***: this endpoint is used when a user wants to put a like on a post he sees from the feed, or when consulting a specific idea from the **/view** endpoint. It is used by a javascript fetch request when a user clicks on the star.
    - ***GET "/edit-post"***: return a formular to update a existing idea. It checks if the user is the author before sending the form. If he isn't, it's redirect the user toward an error page.
    - ***POST "/edit-post"***: handle form sent by the user and update the post values according to the edits if user has the permission.
    - ***GET "/delete-post"***: delete the post if the user is the author of the idea, and redirect to main page with a success notification to confirm the deletion.
    - ***GET "/my-ideas"***: list all the ideas the user has ever posted in an array. The user is able to click on any idea in the array to view it (redirect to **/view** page) or delete it (redirect to **/delete-post** page).
- **auth.py**: this file is a copy with a few changes of the finance CS50 project used to handle the user session over the app (since it uses the exact same stack), as well as the error page.
- **init_db.sql**: this file is used to initialise the SQLite database in case I need to restart the db from scratch. It contains all the required SQL tables the app needs, as well as varies dummy data used to simulate users acount creation, posts and stars. All the data has been generated thanks to **ChatGPT**.
- **mdi.db**: the file containing the SQLite database used by the application.
- **README.md**: this file which contains all the documentation required for the CS50 final project.
- **static/**: directory containing favicon of the app. It uses icon freely available from the material icon web page, as well as the **style.css** file
- **templates/**: directory containing all the HTML file/Jinja templates according to the Flask good practices.
    - ***auth_form.html***: A javascript snipet I developed to add a couple of features to the authentication formulars (/login and /register).
    - ***error.html***: The error page displayed when the application needs to redirect the user towards an error page with a custom error code and message (inspired by the error page in the CS50 Finance project).
    - ***index.html***: Main page of the website containing the feed of the application as well as various filters to list the ideas:
        - Sort by latest posted idea.
        - Sort by most stared idea.
        - Filter by tags/categories.
    - ***layout.html***: according to the Flask/Jinja good practice and the CS50 Finance project, this template is the main template used accross the website. It handles the top bar of the website including:
        - "Million $ Idea" title on the top left corner which redirect to the main page.
        - The login button on the top right corner which redirect to the login page if clicked, and when logged in, display a drop down menu used to access the **/my-ideas** endpoint to list all the user posts, the settings as well as logout.
    This template also import the **style.css** stylesheet and the material design CSS style used accross the website for a couple of buttons and forms components.
    - **login.html**: the login formular.
    - **my_ideas.html**: the array displaying all the user posts.
    - **register.html**: the register formular.
    - **settings.html**: the settings web page. Contains 2 buttons: one to delete the account and another one to reset the user password. It displays a pop-up window according to the clicked button.
    - **star_mgmt.html**: the javascript snipet I developed to handle the "like" feature on posts.
    - **view.html**: the HTML/Jinja template used to display a specific idea from the feed.
