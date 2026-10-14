
#This is fictional data that is currently being used
#In IRL, this would be replaced for real user data


# import database functions used to save and retrieve tickets.
from database import (
    insert_support_ticket,
    fetch_support_ticket
)

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

    city = city.strip().lower()

    if city in MOCK_OUTAGES:

        return {
            "city": city,
            "status": "success",
            "data": MOCK_OUTAGES[city]
        }

    return {
        "city": city,
        "status": "not_found",
        "message": "No simulated outage data available for this city."
    }



###Fictional data vvvvvvvvvvvvvvvvvvv
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


    print(f"[TOOL CALLED] get_customer_info({customer_id})")


    customer_id = customer_id.strip().upper()


    customer = MOCK_CUSTOMERS.get(customer_id)


    if customer is None:
        return {
            "status": "not_found",
            "message": "Customer record not found in demo data."
        }


    return {
        "status": "success",
        "customer_id": customer_id,
        "customer": customer,
        "data_source": "simulated"
    }





from datetime import datetime, timezone
from threading import Lock



SUPPORT_TICKETS = {}

ticket_counter = 0


ticket_lock = Lock()




# They validate information before calling database.py.
# separates business logic from database operations.



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

    # Normalize 
    customer_id = customer_id.strip().upper()
    issue = issue.strip()
    priority = priority.strip().capitalize()

    # Verify 
    customer = MOCK_CUSTOMERS.get(customer_id)

    if customer is None:
        return {
            "status": "error",
            "message": "Customer does not exist."
        }

    # Reject 
    if not issue:
        return {
            "status": "error",
            "message": "Issue description cannot be empty."
        }

    # Validate
    if priority not in ("Low", "Medium", "High"):
        return {
            "status": "error",
            "message": "Priority must be Low, Medium, or High."
        }

    # Call database functioun to creat ticket
  
    ticket = insert_support_ticket(
        customer_id=customer_id,
        customer_name=customer["name"],
        issue=issue,
        priority=priority
    )

  
    print(f"[DATABASE] Created support ticket {ticket['ticket_id']}")

    # return the ticket to Gemini through Google ADK.
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

    ticket = fetch_support_ticket(ticket_id)

    # if no ticket match
    if ticket is None:
        return {
            "status": "not_found",
            "message": "Support ticket not found."
        }

    # return database to ai agent
    return {
        "status": "success",
        "ticket": ticket,
        "data_source": "simulated"
    }
