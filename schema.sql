DROP TABLE IF EXISTS reservations;

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passengerName TEXT NOT NULL,
    seatRow INTEGER NOT NULL,
    seatColumn INTEGER NOT NULL,
    eTicketNumber TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS admins;

CREATE TABLE admins (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
);
