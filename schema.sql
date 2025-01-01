-- In this SQL file, write (and comment!) the schema of your database, including the CREATE TABLE, CREATE INDEX, CREATE VIEW, etc. statements that compose it

-- add table for users

    CREATE TABLE  users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
    );



-- Add table for decks
CREATE TABLE decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
-- Add table for cards
CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    user_id INTEGER,
    deck_id INTEGER,
    rating INTEGER DEFAULT 3,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (deck_id) REFERENCES decks(id),

);



