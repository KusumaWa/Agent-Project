
# import database and ticket functions.
from database import initialize_database
from tools import create_support_ticket, get_support_ticket


# SQLite database.
initialize_database()


# Create and save a test ticket.
result = create_support_ticket(
    customer_id="CUST001",
    issue="Internet disconnects every 10 minutes",
    priority="Medium"
)

# Display result
print("\nCREATION RESULT:")
print(result)


# verify and retrival
if result["status"] == "success":

    # retrieve ticke
    ticket_id = result["ticket"]["ticket_id"]
    saved_ticket = get_support_ticket(ticket_id)

    print("\nLOOKUP RESULT:")
    print(saved_ticket)

    #verify
    assert saved_ticket["status"] == "success"
    assert saved_ticket["ticket"]["customer_id"] == "CUST001"

    print("\nSUCCESS: SQLite ticket creation and retrieval work!")

else:
    print("\nFAILED: Could not create a support ticket.")
