
# This file handlesSQLite database.
#
# Responsibilities:
# 1. Connect to database.
# 2. Create database tables.
# 3. Insert new support tickets.
# 4. Retrieve existing tickets.

import sqlite3
from pathlib import Path
from datetime import datetime, timezone


# Stores database in the same directory as database.py
# avoids problems if Python runs from another folder?
DB_PATH = Path(__file__).resolve().parent / "spectrum.db"


def get_connection():
    """
    Open a new connection to our SQLite database.

    Returns:
        A SQLite connection object.
    """

    # sqlite3.connect creates database file if it not exsist
    connection = sqlite3.connect(DB_PATH, timeout=10)

    # allows retrieve columns using names instead of numbahs
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """
    Create the support_tickets table if it doesn't exist.
    """

    connection = get_connection()

    try:
        # Createing table using SQL.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                issue TEXT NOT NULL,
                priority TEXT NOT NULL
                    CHECK(priority IN ('Low', 'Medium', 'High')),
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL
            )
        """)

        # Save the table creation to DB (Database)
        connection.commit()

        print("[DATABASE] Support tickets table ready.")

    finally:
        # error bypass not important
        connection.close()


def insert_support_ticket(
    customer_id: str,
    customer_name: str,
    issue: str,
    priority: str
) -> dict:
    """
    Insert a support ticket into the database.

    Returns:
        The newly created ticket as a dictionary.
    """

    # record when ticket created
    created_at = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    try:
        # Insert the new ticket into our database.
        # (question marks are SQL placeholders)
        # Protection and such
        cursor = connection.execute(
            """
            INSERT INTO support_tickets
                (customer_id, customer_name, issue,
                 priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                customer_name,
                issue,
                priority,
                "Open",
                created_at
            )
        )

        database_id = cursor.lastrowid

        connection.commit()

        # Numeric Id -> readable stuff
        # Ex: 1 becomes TKT-0001.
        ticket_id = f"TKT-{database_id:04d}"

        return {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "issue": issue,
            "priority": priority,
            "status": "Open",
            "created_at": created_at
        }

    finally:
        connection.close()


def fetch_support_ticket(ticket_id: str) -> dict | None:
    """
    Retrieve a stored ticket using its ticket ID.

    Args:
        ticket_id: For example, TKT-0001.

    Returns:
        A ticket dictionary or None if not found.
    """

    # Normalize ID
    ticket_id = ticket_id.strip().upper()

    # Verify ID
    if not ticket_id.startswith("TKT-"):
        return None

    # Extract ID
    number = ticket_id[4:]

    # Reject invalid ID
    if not number.isdigit():
        return None

    connection = get_connection()

    try:
        # Retrie mathcing Id
        cursor = connection.execute(
            """
            SELECT *
            FROM support_tickets
            WHERE id = ?
            """,
            (int(number),)
        )

        row = cursor.fetchone()

        # Return None when no match
        if row is None:
            return None

        # Convert SQLite's row to dictionary.
        ticket = dict(row)

        # Convert into customer-friendly ticket format.
        ticket["ticket_id"] = f"TKT-{ticket.pop('id'):04d}"

        return ticket

    finally:
        connection.close()



# This function allows our dashboard to display a customer's
# support tickets without calling Gemini (This is because Gemini might be a bit slow sometimes (FREE MODEL!!!))

def fetch_customer_tickets(customer_id: str) -> list[dict]:
    """
    Retrieve all support tickets belonging to a customer.

    Args:
        customer_id: Fictional customer identifier.

    Returns:
        A list of ticket dictionaries, newest first.
    """

    # normalize the customer ID to match  stored format
    customer_id = customer_id.strip().upper()

    # Open connection to database
    connection = get_connection()

    try:
        # Retrieve the matching tickets.
        # The ? is protection
        cursor = connection.execute(
            """
            SELECT *
            FROM support_tickets
            WHERE customer_id = ?
            ORDER BY id DESC
            """,
            (customer_id,)
        )

        # Fetch  matching record
        rows = cursor.fetchall()

        # Convert SQLite rows into reg dic.
        tickets = []

        for row in rows:

            # Convert the database into dic
            ticket = dict(row)

            # Replace the numeric ID into readable stuff
            ticket["ticket_id"] = f"TKT-{ticket.pop('id'):04d}"

            tickets.append(ticket)

        return tickets

    finally:
        connection.close()



# update support ticket status and permamntly saves
#
# Current statuses:
# - Open
# - In Progress
# - Resolved


def update_ticket_status(ticket_id: str, new_status: str) -> dict | None:
    """
    Update the status of an existing support ticket.

    Args:
        ticket_id: Ticket identifier, such as TKT-0003.
        new_status: Open, In Progress, or Resolved.

    Returns:
        The updated ticket, or None if it doesn't exist.

    Raises:
        ValueError: If the ticket ID or status is invalid.
    """

    
    ticket_id = ticket_id.strip().upper()

   
    new_status = " ".join(new_status.split()).title()

   
    valid_statuses = ("Open", "In Progress", "Resolved")

   
    if new_status not in valid_statuses:
        raise ValueError(
            f"Invalid ticket status: {new_status!r}. "
            "Allowed values: Open, In Progress, Resolved."
        )

   
    if not ticket_id.startswith("TKT-"):
        raise ValueError("Invalid ticket ID.")


    number = ticket_id[4:]

    if not number.isdigit():
        raise ValueError("Invalid ticket ID.")

    database_id = int(number)

    # Open a connection to SQLite
    connection = get_connection()

    try:
 

        cursor = connection.execute(
            """
            UPDATE support_tickets
            SET status = ?
            WHERE id = ?
            """,
            (new_status, database_id)
        )

      
        connection.commit()

        if cursor.rowcount == 0:
            return None

    finally:
      
        connection.close()


    return fetch_support_ticket(ticket_id)
