"""
AI Enabled Conversational IVR Modernization Framework
State-Based IVR Backend using FastAPI

FLOW OF THIS IVR SYSTEM:

1️⃣ User starts call → /ivr/start
2️⃣ System creates unique session_id
3️⃣ System sets current menu = "main"
4️⃣ System sends main menu prompt

5️⃣ User presses a digit → /ivr/input
6️⃣ System checks session_id
7️⃣ System checks current menu
8️⃣ System validates digit
9️⃣ Based on action:
      - goto → move to another menu
      - end → end call and delete session
      - agent → transfer call
      - hangup → end call
"""

from fastapi import FastAPI
from pydantic import BaseModel
import uuid

app = FastAPI(title="IRCTC IVR Backend Simulator")

# ---------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------

# When call starts, this model receives caller number
class StartCallRequest(BaseModel):
    caller_number: str = "Simulator"

# When user presses digit, this model receives:
# session_id (unique call id)
# digit (pressed key)
class InputRequest(BaseModel):
    session_id: str
    digit: str

# SESSION STORAGE (Temporary Memory)
# Stores active call sessions
# Example:
# sessions = {
#   "abc123": {"current_menu": "booking"}
# }

sessions = {}

# IVR MENU STRUCTURE (STATE MACHINE)
# Each menu contains:
# - prompt → message to user
# - options → digit mapping to action

MENUS = {

    # MAIN MENU (First menu user hears)
    "main": {
        "prompt": "Welcome to IRCTC. Press 1 for Booking, 2 for Train Status, 3 for Seat Availability, 0 to Speak to Agent, 9 to Exit.",
        "options": {
            "1": {"action": "goto", "target": "booking"},   # Move to booking menu
            "2": {"action": "goto", "target": "train"},     # Move to train status menu
            "3": {"action": "goto", "target": "seat"},      # Move to seat menu
            "0": {"action": "agent"},                       # Transfer to agent
            "9": {"action": "hangup"}                       # End call
        }
    },

    # BOOKING MENU
    "booking": {
        "prompt": "Booking Menu. Press 1 for Domestic, 2 for International, 9 to Go Back.",
        "options": {
            "1": {"action": "end", "message": "Domestic booking selected."},
            "2": {"action": "end", "message": "International booking selected."},
            "9": {"action": "goto", "target": "main"}  # Go back to main menu
        }
    },

    # TRAIN STATUS MENU
    "train": {
        "prompt": "Train Status Menu. Press 1 to Check Running Status, 9 to Go Back.",
        "options": {
            "1": {"action": "end", "message": "Train 12727 is running on time."},
            "9": {"action": "goto", "target": "main"}
        }
    },

    # SEAT AVAILABILITY MENU
    "seat": {
        "prompt": "Seat Availability Menu. Press 1 to Check Availability, 9 to Go Back.",
        "options": {
            "1": {"action": "end", "message": "Seats available in Sleeper class."},
            "9": {"action": "goto", "target": "main"}
        }
    }
}

# START CALL API

@app.post("/ivr/start")
def start_call(request: StartCallRequest):

    # 1️ Generate unique session ID
    session_id = str(uuid.uuid4())

    # 2️ Store session with initial state = main menu
    sessions[session_id] = {"current_menu": "main"}

    # 3️ Return main menu prompt
    return {
        "status": "call_started",
        "session_id": session_id,
        "menu": "main",
        "prompt": MENUS["main"]["prompt"]
    }

# HANDLE USER INPUT

@app.post("/ivr/input")
def handle_input(request: InputRequest):

    # 4️ Check if session exists
    session = sessions.get(request.session_id)

    if not session:
        return {"status": "error", "message": "Invalid session ID"}

    # 5️ Get current menu
    current_menu = session["current_menu"]
    menu_data = MENUS[current_menu]

    # 6️ Validate digit
    if request.digit not in menu_data["options"]:
        return {
            "status": "invalid_option",
            "prompt": menu_data["prompt"]
        }

    # 7️ Identify action
    selected_option = menu_data["options"][request.digit]
    action = selected_option["action"]

    
    # If action is "goto"
    # Move to another menu
    
    if action == "goto":
        new_menu = selected_option["target"]
        session["current_menu"] = new_menu

        return {
            "status": "menu_changed",
            "menu": new_menu,
            "prompt": MENUS[new_menu]["prompt"]
        }

    
    # If action is "end"
    # End call and delete session

    elif action == "end":
        message = selected_option["message"]
        del sessions[request.session_id]

        return {
            "status": "call_ended",
            "message": message
        }

    
    # If action is "agent"
    # Transfer call
    
    elif action == "agent":
        del sessions[request.session_id]

        return {
            "status": "transferred_to_agent",
            "message": "Please wait while we connect you to a customer support agent."
        }

    # If action is "hangup"
    # End call

    elif action == "hangup":
        del sessions[request.session_id]

        return {
            "status": "call_ended",
            "message": "Thank you for calling IRCTC. Goodbye."
        }

# ROOT API (Health Check)

@app.get("/")
def root():
    return {"status": "IRCTC IVR Backend Running Successfully"}