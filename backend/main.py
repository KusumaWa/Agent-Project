
# ============================================================
# COMPANY SUPPORT AI - FASTAPI BACKEND
# ============================================================
# This file acts as the bridge between our frontend and AI agent.
#
# The flow of information:
# 1. A user sends a message to the /chat endpoint.
# 2. FastAPI receives and validates the message.
# 3. Google ADK sends the message to our Gemini AI agent.
# 4. Gemini generates a response.
# 5. FastAPI returns the response to the user.
# ============================================================


# Used to manage the application's startup and shutdown.
from contextlib import asynccontextmanager

# Loads environment variables from our .env file.
from dotenv import load_dotenv

# FastAPI creates API endpoints.
# HTTPException lets us return HTTP errors when something fails.
from fastapi import FastAPI, HTTPException

# BaseModel validates incoming JSON request data.
from pydantic import BaseModel

# InMemoryRunner executes our AI agent and manages sessions.
from google.adk.runners import InMemoryRunner

# Provides the message formats required by Google's API.
from google.genai import types

# Provides detailed information about exceptions.
# Useful for finding exactly where a failure occurred.
import traceback

# Import Google's API error classes.
# This lets us distinguish quota failures from other errors.
from google.genai import errors

# Initialize our SQLite tables when the backend starts.
from database import initialize_database

# Import Google's API error classes.
# These distinguish quota errors from temporary server failures.
from google.genai import errors


# Import our existing customer and outage lookup functions.
# These return fictional demonstration data.
from tools import get_customer_info, check_network_outage

# Import the database function that retrieves customer tickets.
from database import fetch_customer_tickets


# Import FastAPI's Field for validating request fields.
from pydantic import Field

# Import our new SQLite ticket update function.
from database import update_ticket_status

# Reuse our existing Python functions for ticket operations.
from tools import create_support_ticket, get_support_ticket

# Used to validate the allowed ticket priority values.
from typing import Literal

# ------------------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------------------

# Read the .env file, which contains our Gemini API key.
# This keeps sensitive information out of our Python code.
load_dotenv()

# Import the agent we created in agent.py.
# The agent contains our Gemini model and its instructions.
from agent import root_agent


# ------------------------------------------------------------
# 2. CREATE THE AI RUNNER
# ------------------------------------------------------------

# The runner is responsible for executing our AI agent.
# It connects the agent to its conversation sessions.
runner = InMemoryRunner(
    agent=root_agent,
    app_name="spectrum_support"
)

# Identify the current user and conversation.
# These are temporary IDs for local development.
#
# Later, we'll generate separate IDs for each user so
# different customers don't share the same conversation.
USER_ID = "demo_user"
SESSION_ID = "demo_session"


# ------------------------------------------------------------
# 3. APPLICATION STARTUP
# ------------------------------------------------------------

# lifespan runs when FastAPI starts and stops.
# We use it to create a conversation session before
# the first message is sent to the AI agent.

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create the database table if it doesn't already exist.
    # This runs each time FastAPI starts, but existing
    # tickets remain untouched.
    initialize_database()

    # Create our demonstration AI conversation session.
    # Google ADK stores conversation history separately
    # from the SQLite support tickets.
    await runner.session_service.create_session(
        app_name="spectrum_support",
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # Allow FastAPI to start accepting requests.
    yield

    # Shutdown cleanup would go here if needed.



# ------------------------------------------------------------
# 4. CREATE THE FASTAPI APPLICATION
# ------------------------------------------------------------

# Initialize our backend.
# The lifespan argument tells FastAPI to run our
# startup logic before accepting requests.
app = FastAPI(
    title="Spectrum Support AI",
    version="0.2.0",
    lifespan=lifespan
)


# ------------------------------------------------------------
# 5. DEFINE THE REQUEST FORMAT
# ------------------------------------------------------------

# This class describes the JSON data our /chat endpoint expects.
#
# Example request:
# {
#     "message": "My internet is slow"
# }
#
# Pydantic automatically checks that message is a string.
class ChatRequest(BaseModel):
    message: str


# ============================================================
# DIRECT SUPPORT TICKET REQUEST
# ============================================================
# This model validates ticket information submitted by React.
# Using Literal restricts the priority to supported values.
# ============================================================

class CreateTicketRequest(BaseModel):
    customer_id: str
    issue: str
    priority: Literal["Low", "Medium", "High"]
    confirmed: bool = False

# ============================================================
# TICKET STATUS UPDATE REQUEST
# ============================================================
# This model validates the data sent by our React frontend
# when a support representative changes a ticket's status.
# ============================================================

class TicketStatusRequest(BaseModel):

    # Require a nonempty status string.
    # The endpoint will validate that it's an allowed value.
    status: str = Field(min_length=1)



# ------------------------------------------------------------
# 6. HOME ENDPOINT
# ------------------------------------------------------------

# GET requests retrieve information from the backend.
# This endpoint confirms our application is accessible.
@app.get("/")
def home():
    return {
        "message": "Company Support AI is running"
    }


# ------------------------------------------------------------
# 7. HEALTH CHECK ENDPOINT
# ------------------------------------------------------------

# This endpoint reports whether our API server is responding.
# Later, we could expand it to check database connectivity.
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# CUSTOMER DASHBOARD API
# ============================================================
# These endpoints let our React dashboard retrieve information
# directly, without sending requests to the Gemini AI agent.
#
# IMPORTANT:
# These endpoints currently use fictional demonstration data.
# They are intended for local development only.
# ============================================================


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    """
    Retrieve a fictional customer account.
    """

    # Reuse the customer lookup tool we've already written.
    result = get_customer_info(customer_id)

    # Return HTTP 404 if the customer doesn't exist.
    if result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="Customer not found."
        )

    # Return the customer ID and its account information.
    return {
        "customer_id": result["customer_id"],
        "customer": result["customer"]
    }


@app.get("/outages/{city}")
def get_outage(city: str):
    """
    Retrieve the simulated outage status of a city.
    """

    # Execute our existing outage lookup function.
    result = check_network_outage(city)

    # An unknown city means we don't have demonstration data.
    # It doesn't necessarily mean there is no outage.
    if result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="No simulated outage data for this city."
        )

    # Return the simulated outage information.
    return {
        "city": result["city"],
        "outage": result["data"],
        "data_source": "simulated"
    }


@app.get("/customers/{customer_id}/tickets")
def get_customer_tickets(customer_id: str):
    """
    Retrieve all fictional support tickets for one customer.
    """

    # Verify that the fictional customer exists.
    customer_result = get_customer_info(customer_id)

    if customer_result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="Customer not found."
        )

    # Retrieve the customer's tickets directly from SQLite.
    tickets = fetch_customer_tickets(
        customer_result["customer_id"]
    )

    # Return the tickets and their total count.
    return {
        "customer_id": customer_result["customer_id"],
        "count": len(tickets),
        "tickets": tickets,
        "data_source": "simulated"
    }



# ============================================================
# UPDATE SUPPORT TICKET ENDPOINT
# ============================================================
# PATCH updates part of an existing resource.
#
# Example request:
# PATCH /tickets/TKT-0003/status
#
# JSON body:
# {
#     "status": "In Progress"
# }
# ============================================================

@app.patch("/tickets/{ticket_id}/status")
def change_ticket_status(
    ticket_id: str,
    request: TicketStatusRequest
):
    """
    Update a fictional support ticket's status.
    """

    try:
        # Call our SQLite function to update the record.
        updated_ticket = update_ticket_status(
            ticket_id=ticket_id,
            new_status=request.status
        )

    except ValueError as error:

        # Invalid ticket IDs or unsupported statuses
        # should return HTTP 400 Bad Request.
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    # Return HTTP 404 if no matching ticket exists.
    if updated_ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found."
        )

    # Return the updated ticket information to React.
    return {
        "status": "success",
        "ticket": updated_ticket,
        "data_source": "simulated"
    }




# ============================================================
# CREATE SUPPORT TICKET ENDPOINT
# ============================================================
# Allows React to create fictional support tickets directly,
# without calling Gemini.
# ============================================================

@app.post("/tickets", status_code=201)
def create_ticket(request: CreateTicketRequest):

    # Verify that the user confirmed the ticket details.
    # If not, reject the request with HTTP 400.
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Ticket creation requires confirmation."
        )

    # Call our existing support ticket creation function.
    # This validates the customer and saves the ticket
    # permanently in our SQLite database.
    result = create_support_ticket(
        customer_id=request.customer_id,
        issue=request.issue,
        priority=request.priority
    )

    # Check whether ticket creation succeeded.
    # For example, an invalid customer ID causes failure.
    if result["status"] != "success":
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    # Return the created ticket to React.
    return result


# ============================================================
# LOOK UP AN EXISTING SUPPORT TICKET
# ============================================================
# Allows React to retrieve saved tickets without Gemini.
# ============================================================

@app.get("/tickets/{ticket_id}")
def lookup_ticket(ticket_id: str):

    # Search SQLite for the requested ticket.
    result = get_support_ticket(ticket_id)

    # Return HTTP 404 when the ticket doesn't exist.
    if result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found."
        )

    # Return the ticket information to React.
    return result


# ------------------------------------------------------------
# 8. AI CHAT ENDPOINT
# ------------------------------------------------------------

# POST requests send data to the backend.
#
# This endpoint receives the user's message, passes it to
# Gemini through Google ADK, and returns the AI's response.
#
# We use async because the AI response requires waiting
# for an external API without blocking the event loop.

@app.post("/chat")
async def chat(request: ChatRequest):

    # Use try/except to handle errors without crashing the API.
    try:

        # Convert the user's text into Google's Content format.
        # Google ADK expects messages to contain a role and parts.
        message = types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=request.message)
            ]
        )

        # This variable will store Gemini's final response.
        response_text = ""

        # Run our agent using the current conversation session.
        #
        # run_async produces events as the agent processes
        # the request, potentially including tool calls.
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message
        ):

            # We only want the final response from the agent.
            # Intermediate events may represent internal steps.
            if event.is_final_response():

                # Verify that the response contains actual content.
                if event.content and event.content.parts:

                    # Combine all text parts into one string.
                    # Some agent responses may contain multiple parts.
                    response_text = "".join(
                        part.text
                        for part in event.content.parts
                        if part.text is not None
                    )

        # Return both the user's original message and the
        # generated response as JSON.
        #
        # Example:
        # {
        #     "user_message": "My internet is slow",
        #     "response": "Try restarting your router..."
        # }
        return {
            "user_message": request.message,
            "response": response_text
        }

    
    # Handle API quota and rate-limit errors.
    except errors.ClientError as error:

        # HTTP 429 means the Gemini quota or rate limit
        # has been exceeded.
        if error.code == 429:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota exceeded. "
                    "Please try again after the quota resets."
                )
            ) from error

        # Other client errors indicate Google rejected
        # the request for a different reason.
        raise HTTPException(
            status_code=502,
            detail="The AI provider rejected the request."
        ) from error

    # Handle temporary Gemini server failures.
    except errors.ServerError as error:

        # HTTP 503 means Gemini is temporarily unavailable.
        if error.code == 503:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Gemini is temporarily experiencing high demand. "
                    "Please try again later."
                )
            ) from error

        # Other upstream server errors become HTTP 502.
        raise HTTPException(
            status_code=502,
            detail="The AI provider encountered a server error."
        ) from error

    # Catch any other unexpected errors.
    except Exception as error:

        # Log the problem for debugging.
        print(f"[AGENT ERROR] {error}", flush=True)

        # Return a generic message without exposing
        # internal application details to users.
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred."
        ) from error

