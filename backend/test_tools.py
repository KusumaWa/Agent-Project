
# Import the ticket functions we want to test.
from tools import create_support_ticket, get_support_ticket


# Create a sample ticket for an existing demo customer.
result = create_support_ticket(
    customer_id="CUST001",
    issue="Internet disconnects every 10 minutes",
    priority="Medium"
)

# Display the result so we can inspect it.
print("CREATION RESULT:")
print(result)


# Only attempt lookup if creation was successful.
if result["status"] == "success":

    # Extract the generated ticket ID.
    ticket_id = result["ticket"]["ticket_id"]

    # Search for that ticket.
    lookup_result = get_support_ticket(ticket_id)

    # Display the retrieved record.
    print("\nLOOKUP RESULT:")
    print(lookup_result)
