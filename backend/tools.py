
# ============================================================
# SPECTRUM SUPPORT AI - AGENT TOOLS
# ============================================================
# This file contains Python functions our AI agent can call.
#
# For now, we use fictional outage data.
# In a real company, this information might come from
# a database or internal network monitoring service.
# ============================================================


# Import database functions used to save and retrieve tickets.
from database import (
    insert_support_ticket,
    fetch_support_ticket
)

# Simulated outage information.
# Each city contains an outage status and a description.
MOCK_OUTAGES = {
    "st. louis": {
        "outage": True,
        "description": "Maintenance affecting some customers.",
        "estimated_resolution": "2 hours"
    },
    "rolla": {
        "outage": False,
        "description": "No outages currently reported.",
        "estimated_resolution": None
    },
    "kansas city": {
        "outage": True,
        "description": "Network equipment issue.",
        "estimated_resolution": "4 hours"
    }
}


def check_network_outage(city: str) -> dict:
    """
    Check simulated internet outages for a specified city.

    Args:
        city: The city the customer wants to check.

    Returns:
        A dictionary describing the outage status.
    """

    # Convert the city name to lowercase and remove
    # leading/trailing spaces for easier matching.
    city = city.strip().lower()

    # Look for the city in our simulated database.
    if city in MOCK_OUTAGES:

        # Return the outage information for that city.
        return {
            "city": city,
            "status": "success",
            "data": MOCK_OUTAGES[city]
        }

    # If the city isn't in our dataset, return a clear
    # message instead of pretending no outage exists.
    return {
        "city": city,
        "status": "not_found",
        "message": "No simulated outage data available for this city."
    }


# ============================================================
# CUSTOMER ACCOUNT LOOKUP
# ============================================================
# These are fictional customer records used for testing.
#
# In a production application, we would store account data
# in a database instead of directly inside our Python code.
#
# Each customer has a unique ID that acts as the dictionary key.
# ============================================================


MOCK_CUSTOMERS = {
    "CUST001": {
        "name": "Alex Johnson",
        "city": "St. Louis",
        "plan": "Internet Ultra",
        "speed_mbps": 500,
        "account_status": "Active"
    },

    "CUST002": {
        "name": "Taylor Smith",
        "city": "Rolla",
        "plan": "Internet Premier",
        "speed_mbps": 100,
        "account_status": "Active"
    },

    "CUST003": {
        "name": "Jordan Lee",
        "city": "Kansas City",
        "plan": "Internet Gig",
        "speed_mbps": 1000,
        "account_status": "Suspended"
    }
}


def get_customer_info(customer_id: str) -> dict:
    """
    Retrieve fictional customer account information.

    Args:
        customer_id: The customer's unique identification code.

    Returns:
        A dictionary containing customer information or
        an error message if the customer does not exist.
    """

    # Print a debugging message whenever this tool executes.
    # This will appear in our FastAPI terminal.
    print(f"[TOOL CALLED] get_customer_info({customer_id})")

    # Remove extra spaces and convert the ID to uppercase.
    # For example, " cust001 " becomes "CUST001".
    customer_id = customer_id.strip().upper()

    # Search the dictionary for the requested customer.
    customer = MOCK_CUSTOMERS.get(customer_id)

    # If the customer doesn't exist, return an error result.
    # This avoids inventing customer information.
    if customer is None:
        return {
            "status": "not_found",
            "message": "Customer record not found in demo data."
        }

    # Return the customer information if a match exists.
    # The AI agent can use this result to answer the user.
    return {
        "status": "success",
        "customer_id": customer_id,
        "customer": customer,
        "data_source": "simulated"
    }



# ============================================================
# SUPPORT TICKET SYSTEM
# ============================================================
# These functions allow our AI agent to create and retrieve
# support tickets for fictional customers.
#
# For now, tickets are stored in Python memory.
# They will disappear when the backend restarts.
#
# We'll replace this with SQLite in Step 6.
# ============================================================

from datetime import datetime, timezone
from threading import Lock


# Store tickets in a dictionary.
# The key is the ticket ID, and the value is the ticket data.
SUPPORT_TICKETS = {}

# Count how many tickets have been created.
ticket_counter = 0

# Prevent multiple requests from updating the counter
# at the same time within one server process.
ticket_lock = Lock()



# ============================================================
# DATABASE-BACKED SUPPORT TICKET TOOLS
# ============================================================
# These functions are available to our Gemini AI agent.
#
# They validate information before calling database.py.
# This separates business logic from database operations.
# ============================================================


def create_support_ticket(
    customer_id: str,
    issue: str,
    priority: str
) -> dict:
    """
    Create a fictional support ticket in SQLite.

    Args:
        customer_id: Fictional customer account ID.
        issue: Description of the customer's problem.
        priority: Low, Medium, or High.

    Returns:
        A success result containing the stored ticket
        or an error describing invalid input.
    """

    # Normalize incoming values.
    customer_id = customer_id.strip().upper()
    issue = issue.strip()
    priority = priority.strip().capitalize()

    # Verify that the customer exists in our demo records.
    customer = MOCK_CUSTOMERS.get(customer_id)

    if customer is None:
        return {
            "status": "error",
            "message": "Customer does not exist."
        }

    # Reject empty issue descriptions.
    if not issue:
        return {
            "status": "error",
            "message": "Issue description cannot be empty."
        }

    # Validate priority before saving it to SQLite.
    if priority not in ("Low", "Medium", "High"):
        return {
            "status": "error",
            "message": "Priority must be Low, Medium, or High."
        }

    # Call our database function to create the ticket.
    # SQLite generates the unique numeric identifier.
    ticket = insert_support_ticket(
        customer_id=customer_id,
        customer_name=customer["name"],
        issue=issue,
        priority=priority
    )

    # Log successful ticket creation in the terminal.
    print(f"[DATABASE] Created support ticket {ticket['ticket_id']}")

    # Return the ticket to Gemini through Google ADK.
    return {
        "status": "success",
        "message": "Support ticket created successfully.",
        "ticket": ticket,
        "data_source": "simulated"
    }


def get_support_ticket(ticket_id: str) -> dict:
    """
    Retrieve a fictional support ticket from SQLite.

    Args:
        ticket_id: Ticket identifier, such as TKT-0001.

    Returns:
        The stored ticket or a not-found message.
    """

    # Query our SQLite database for the requested ticket.
    ticket = fetch_support_ticket(ticket_id)

    # If no ticket matches, return a clear result.
    if ticket is None:
        return {
            "status": "not_found",
            "message": "Support ticket not found."
        }

    # Return the database record to our AI agent.
    return {
        "status": "success",
        "ticket": ticket,
        "data_source": "simulated"
    }
