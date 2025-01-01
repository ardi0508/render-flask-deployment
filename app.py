import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import random

PROBABILITY_WEIGHTS = {
    1: 0.4,
    2: 0.3,
    3: 0.2,
    4: 0.07,
    5: 0.03
}

# Configure application
app = Flask(__name__)

if __name__ == "__main__":
    app.run()

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///poppy.db")

# Apology function
def apology(message, code=400):
    return render_template("apology.html", message=message), code

#make sure login is needed
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Register route
@app.route("/register", methods=["POST", "GET"])
def register():
    # Forget any user id
    session.clear()

    if request.method == "POST":

        # Ensure username is provided
        if not request.form.get("username"):
            return apology("Must provide username", 400)

        # Ensure password is provided
        elif not request.form.get("password"):
            return apology("Must provide password.", 400)

        # Ensure confirmation password is provided
        elif not request.form.get("confirmation"):
            return apology("Must provide correct confirmation password", 400)

        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # Make sure username isn't taken
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 0:
            return apology("Username already exists")

        # Add user to the database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Retrieve user_id of the newly created user
        user_id = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = user_id

        # Redirect to login page
        return redirect("/login")

    else:
        return render_template("register.html")



#login form

@app.route("/login", methods=["POST", "GET"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

#index page

@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    return render_template("index.html")

# timer form
@app.route("/timer", methods=["POST", "GET"])
@login_required
def timer():
    return render_template("timer.html")

#logout form

@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    """Log user out"""
    if request.method=="POST":

        # Forget any user_id
        session.clear()

        # Redirect user to login form
        return redirect("/login")
    else:
        return render_template("logout.html")


# deck form


# add cards
@app.route("/cue-cards", methods=["POST", "GET"])
@login_required
def cue_cards():
    if request.method == "POST":
        # Get the name of the new deck from the form
        name = request.form.get("name")

        if name:
            # Insert the new deck into the database
            db.execute("INSERT INTO decks (name, user_id) VALUES (:name, :user_id)",
                       name=name, user_id=session["user_id"])

        return redirect("/cue-cards")  # Redirect to the cue-cards page to see the updated list

    else:
        # Fetch all decks for the logged-in user
        decks = db.execute("SELECT * FROM decks WHERE user_id = :user_id",
                           user_id=session["user_id"])
        return render_template("cue-cards.html", decks=decks)



@app.route('/remove-deck/<int:deck_id>')
@login_required
def remove_deck(deck_id):
    deck = db.execute("SELECT id FROM decks WHERE id = :deck_id AND user_id = :user_id",
                      deck_id=deck_id, user_id=session["user_id"])
    if not deck:
        return apology("Deck not found or you don't have permission to remove it")

    db.execute("DELETE FROM cards WHERE deck_id = :deck_id", deck_id=deck_id)

    db.execute("DELETE FROM decks WHERE id = :deck_id", deck_id=deck_id)


    return redirect("/cue-cards")



@app.route("/deck/<int:deck_id>/add", methods=["GET", "POST"])
def add_card(deck_id):
    # Query to fetch the deck by its ID to make sure it exists and belongs to the current user
    deck = db.execute("SELECT id, name FROM decks WHERE id = :deck_id AND user_id = :user_id",
                      deck_id=deck_id, user_id=session["user_id"])

    if not deck:
        return apology("Deck not found or you don't have permission to add cards")

    if request.method == "POST":
        question = request.form.get("question")
        answer = request.form.get("answer")

        if not question or not answer:
            return apology("Please provide both a question and an answer")

        # Insert the new card into the database
        db.execute("INSERT INTO cards (deck_id, question, answer, user_id) VALUES (:deck_id, :question, :answer, :user_id)",
                   deck_id=deck_id, question=question, answer=answer, user_id=session["user_id"])

        # Redirect back to the deck page (or the cards list)
        return redirect(f"/deck/{deck_id}/add")

    # Render the page for adding a card to the specific deck
    else:
      return render_template("add_card.html", deck=deck[0])


@app.route("/card/<int:deck_id>/view", methods=["GET"])
@login_required
def cards(deck_id):
    # Fetch cards associated with the deck for the current user
    cards = db.execute("SELECT * FROM cards WHERE user_id = :user_id AND deck_id = :deck_id",
                        user_id=session["user_id"], deck_id=deck_id)
    if not cards:
        flash("No cards found for this deck.")


    # Render the template with the cards for that deck
    return render_template("your-cards.html", cards=cards, deck_id=deck_id)




# Remove card
@app.route("/remove-card/<int:card_id>/remove", methods=["GET"])
@login_required
def remove_card(card_id):
    # Check if the card exists for the current user
    cards = db.execute("SELECT id FROM cards WHERE id = :card_id AND user_id = :user_id",
                       card_id=card_id, user_id=session["user_id"])

    if not cards:
        return apology("Card not found or you don't have permission to remove it")

    # Get the deck_id associated with the card
    deck_id = db.execute("SELECT deck_id FROM cards WHERE id = :card_id", card_id=card_id)

    # Ensure that deck_id is not empty or None
    if not deck_id or len(deck_id) == 0:
        return apology("Deck associated with the card not found")

    # Debugging: print the deck_id to verify if it's correct
    print(f"Deck ID: {deck_id[0]['deck_id']}")  # This will show in the terminal

    # Delete the card from the database
    db.execute("DELETE FROM cards WHERE id = :card_id", card_id=card_id)

    # Redirect to the deck's page
    return redirect(f"/card/{deck_id[0]['deck_id']}/view")



@app.route("/edit-card/<int:card_id>", methods=["GET", "POST"])
@login_required
def edit_card(card_id):
    # Query the card to ensure it exists and belongs to the user
    card = db.execute("SELECT * FROM cards WHERE id = :card_id AND user_id = :user_id",
                      card_id=card_id, user_id=session["user_id"])

    if not card:
        return apology("Card not found or you don't have permission to edit it")

    card = card[0]  # Since db.execute returns a list of dictionaries

    if request.method == "POST":
        # Get updated question and answer from the form
        question = request.form.get("question")
        answer = request.form.get("answer")

        if not question or not answer:
            return apology("Please provide both a question and an answer")

        # Update the card in the database
        db.execute("UPDATE cards SET question = :question, answer = :answer WHERE id = :card_id",
                   question=question, answer=answer, card_id=card_id)

        # Redirect back to the deck's page
        return redirect(f"/card/{card['deck_id']}/view")

    # Render the edit card page
    return render_template("edit_card.html", card=card)


@app.route("/study", methods=["GET"])
@login_required
def view_decks():
    decks = db.execute("SELECT * FROM decks WHERE user_id= :user_id", user_id=session["user_id"])
    return render_template("view_decks.html", decks=decks)





@app.route("/study/<int:deck_id>", methods=["GET"])
@login_required
def study(deck_id):
    # Fetch the deck to ensure it belongs to the user
    deck = db.execute("SELECT * FROM decks WHERE id = :deck_id AND user_id = :user_id",
                      deck_id=deck_id, user_id=session["user_id"])
    if not deck:
        return apology("Deck not found or you don't have permission to access it")

    # Fetch all cards for the deck
    cards = db.execute("""SELECT * FROM cards WHERE deck_id = :deck_id AND user_id = :user_id""",
                        deck_id=deck_id, user_id=session["user_id"])

    if not cards:
        return apology("No cards found in the deck.")

    # Select a random card from the deck (change this logic as per your preference)
    next_card = random.choice(cards)  # Pick a random card

    return render_template("study.html", card=next_card, deck=deck[0])




@app.route('/rate-card', methods=['POST'])
@login_required
def rate_card():
    card_id = request.form.get("card_id")
    rating = int(request.form.get("rating"))

    # Validate inputs
    if not card_id or not rating:
        return jsonify({"error": "Invalid input"}), 400

    # Update the card's rating based on the user's feedback
    db.execute("""
        UPDATE cards
        SET rating = :rating
        WHERE id = :card_id AND user_id = :user_id
    """, rating=rating, card_id=card_id, user_id=session["user_id"])

    return jsonify({"success": True})

