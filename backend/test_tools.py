
# Import the ticket functions
from tools import create_support_ticket, get_support_ticket


# Create a sample ticket for demo
result = create_support_ticket(
    customer_id="CUST001",
    issue="Internet disconnects every 10 minutes",
    priority="Medium"
)

# display result
print("CREATION RESULT:")
print(result)


# Only attempt lookup if creation was successful.
if result["status"] == "success":

    ticket_id = result["ticket"]["ticket_id"]

    lookup_result = get_support_ticket(ticket_id)

    print("\nLOOKUP RESULT:")
    print(lookup_result)
