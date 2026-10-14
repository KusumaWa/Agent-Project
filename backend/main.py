

# This file acts as the bridge between our frontend and AI agent.
#
# The flow of information:
# 1. A user sends a message to the /chat endpoint.
# 2. FastAPI receives and validates the message.
# 3. Google ADK sends the message to our Gemini AI agent.
# 4. Gemini generates a response.
# 5. FastAPI returns the response to the user.



from contextlib import asynccontextmanager
from typing import Literal
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from google.adk.runners import InMemoryRunner
from google.genai import types, errors

# Database operations
from database import (
    initialize_database,
    fetch_customer_tickets,
    update_ticket_status,
)

# Customer, outage, and ticket tools
from tools import (
    get_customer_info,
    check_network_outage,
    create_support_ticket,
    get_support_ticket,
)


#Load env files, gemini key
load_dotenv()

# Import the agent we created in agent.py. (Contains model and instrcutions)
from agent import root_agent


#Runs AI agent
runner = InMemoryRunner(
    agent=root_agent,
    app_name="spectrum_support"
)


USER_ID = "demo_user"
SESSION_ID = "demo_session"


# Initialize the database and AI session when FastAPI starts.
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Set up the database without deleting existing tickets.
    initialize_database()

    # Create a demo AI conv session (May be changed later?)
    await runner.session_service.create_session(
        app_name="spectrum_support",
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # Start the application.
    yield




# Initialize backend
app = FastAPI(
    title="Spectrum Support AI",
    version="0.2.0",
    lifespan=lifespan
)



# This class describes the JSON data gem expects
# Example request:
# {
#     "message": "My internet is slow"
# }
#
class ChatRequest(BaseModel):
    message: str


#Validates data when ticket requesting
class CreateTicketRequest(BaseModel):
    customer_id: str
    issue: str
    priority: Literal["Low", "Medium", "High"]
    confirmed: bool = False

#Validates data when ticket status change
class TicketStatusRequest(BaseModel):

    # Require a nonempty status string.
    status: str = Field(min_length=1)



#Grants message when ai is running
@app.get("/")
def home():
    return {
        "message": "Company Support AI is running"
    }


#Is the API responding?
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }



# These endpoints let our React dashboard retrieve information
# directly, without sending requests to the Gemini AI agent.
#^^^ This is to circumvate gemini dying on me

#This uses fictional data

@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    """
    Retrieve a fictional customer account.
    """

    result = get_customer_info(customer_id)

    # Return HTTP 404 if the customer not exsist
    if result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="Customer not found."
        )

    # Return the customer ID and account information
    return {
        "customer_id": result["customer_id"],
        "customer": result["customer"]
    }


@app.get("/outages/{city}")
def get_outage(city: str):
    """
    Retrieve the simulated outage status of a city.
    """

    result = check_network_outage(city)

    # (St louis is the only city that exsist!)
    if result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="No simulated outage data for this city."
        )

    # Return fake information 
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

    # Verify fictional customer exsist
    customer_result = get_customer_info(customer_id)

    if customer_result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="Customer not found."
        )

    # Retrieve customer ticket from sqlite
    tickets = fetch_customer_tickets(
        customer_result["customer_id"]
    )

    # return ticket and total count
    return {
        "customer_id": customer_result["customer_id"],
        "count": len(tickets),
        "tickets": tickets,
        "data_source": "simulated"
    }




# PATCH updates part of an existing resource.
#
# In this case:
# PATCH /tickets/TKT-0003/status
# JSON body:
# {
#     "status": "In Progress"
# }


@app.patch("/tickets/{ticket_id}/status")
def change_ticket_status(
    ticket_id: str,
    request: TicketStatusRequest
):
    """
    Update a fictional support ticket's status.
    """

    try:
        # Call SQLite to update func
        updated_ticket = update_ticket_status(
            ticket_id=ticket_id,
            new_status=request.status
        )

    except ValueError as error:


        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    if updated_ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found."
        )

    # Return the updated ticket info
    return {
        "status": "success",
        "ticket": updated_ticket,
        "data_source": "simulated"
    }





# Allows React to create fictional support tickets directly,
# without calling Gemini.
#^^^Free model 

@app.post("/tickets", status_code=201)
def create_ticket(request: CreateTicketRequest):

    # Verify that the user confirmed the ticket details.
    # If not, reject the request with HTTP 400.
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Ticket creation requires confirmation."
        )


    result = create_support_ticket(
        customer_id=request.customer_id,
        issue=request.issue,
        priority=request.priority
    )


    if result["status"] != "success":
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    # Return the created ticket to React.
    return result


@app.get("/tickets/{ticket_id}")
def lookup_ticket(ticket_id: str):


    result = get_support_ticket(ticket_id)


    if result["status"] != "success":
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found."
        )


    return result



# POST requests send data to the backend.

# This endpoint receives the user's message, passes it to
# Gemini through Google ADK, and returns the AI's response

@app.post("/chat")
async def chat(request: ChatRequest):

    # try to handle errors withhout crashing the API
    try:

        # convert user's text into Google Content format.
        # (Google ADK apprently expects messages to contain a role and parts)
        message = types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=request.message)
            ]
        )

        #store final response
        response_text = ""


        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message
        ):

            # Customers dont want to hear gemini yapp about whole lot of stuff, they only care of end result
            if event.is_final_response():

                
                if event.content and event.content.parts:

                    # Combine all text parts into one string.
                   # just in case, some AI likes multiple strings
                    response_text = "".join(
                        part.text
                        for part in event.content.parts
                        if part.text is not None
                    )

        # Return both user's original message and the
        # generated response as JSON.
        return {
            "user_message": request.message,
            "response": response_text
        }

    
    # iGNORE all of this, this is just to find out why things break
    except errors.ClientError as error:


        if error.code == 429:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota exceeded. "
                    "Please try again after the quota resets."
                )
            ) from error

  
        raise HTTPException(
            status_code=502,
            detail="The AI provider rejected the request."
        ) from error


    except errors.ServerError as error:


        if error.code == 503:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Gemini is temporarily experiencing high demand. "
                    "Please try again later."
                )
            ) from error


        raise HTTPException(
            status_code=502,
            detail="The AI provider encountered a server error."
        ) from error


    except Exception as error:

  
        print(f"[AGENT ERROR] {error}", flush=True)


        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred."
        ) from error

