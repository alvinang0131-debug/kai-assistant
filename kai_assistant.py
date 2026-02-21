from flask import Flask, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import os
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ===============================
# GLOBAL MODE
# ===============================

MODE = "ceo"
MEMORY_FILE = "memory.json"
TASKS_FILE = "tasks.json"

# ===============================
# MEMORY SYSTEM
# ===============================

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(entry):
    memory = load_memory()
    memory.append({
        "time": str(datetime.now()),
        "entry": entry
    })
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

# ===============================
# PERSONALITY ENGINE
# ===============================

def set_mode(new_mode):
    global MODE
    MODE = new_mode.lower()

def personality_wrap(text):

    styles = {
        "ceo": [
            "Andrew, here’s the strategic breakdown.",
            "Let’s analyze this properly.",
        ],
        "chill": [
            "Alright Andrew, here’s what I found.",
            "Okay, so here’s the deal.",
        ],
        "strict": [
            "Direct response.",
            "Concise answer.",
        ],
        "humor": [
            "Alright, activating big brain mode.",
            "Okay Andrew, let’s cook something intelligent.",
        ],
        "empathetic": [
            "Hey Andrew, I’ve got you.",
            "Let’s walk through this calmly.",
        ],
        "briefing": [
            "Executive briefing:",
        ],
        "whisper": [
            "Lowering voice. Here’s the update.",
        ]
    }

    opener = random.choice(styles.get(MODE, ["Here’s the response."]))

    if MODE == "briefing":
        return f"{opener}\n{text}"

    return f"{opener}\n\n{text}\n\n... \n\nWhat’s the next move?"

# ===============================
# TASK SYSTEM
# ===============================

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def schedule_task(details):
    try:
        name, minutes, priority = [x.strip() for x in details.split(",")]
        tasks = load_tasks()
        tasks.append({
            "task": name,
            "minutes": minutes,
            "priority": priority,
            "created": str(datetime.now())
        })
        save_tasks(tasks)
        save_memory(f"Task scheduled: {name}")
        return personality_wrap(f"Task '{name}' scheduled with {priority} priority.")
    except:
        return personality_wrap("Format: task,minutes,priority")

def list_tasks():
    tasks = load_tasks()
    if not tasks:
        return personality_wrap("No tasks scheduled.")
    output = "Current tasks:\n"
    for t in tasks:
        output += f"- {t['task']} ({t['priority']})\n"
    return personality_wrap(output)

# ===============================
# RESEARCH ENGINE
# ===============================

def research(topic):
    try:
        summary = ""
        wiki = requests.get(f"https://en.wikipedia.org/wiki/{topic.replace(' ','_')}")
        soup = BeautifulSoup(wiki.text, "html.parser")
        for p in soup.select("p")[:4]:
            summary += p.get_text()

        summary = summary[:800]

        save_memory(f"Research: {topic}")
        return personality_wrap(summary)

    except:
        return personality_wrap("Research failed.")

# ===============================
# AUTOMATION (RAW OUTPUT)
# ===============================

def call_contact(name):
    save_memory(f"Call: {name}")
    return f"CALL_CONTACT:{name}"

def text_contact(name, message):
    save_memory(f"Text: {name}")
    return f"TEXT_CONTACT:{name}:{message}"

def whatsapp_contact(name, message):
    save_memory(f"WhatsApp: {name}")
    return f"WHATSAPP_CONTACT:{name}:{message}"

def navigate(place):
    save_memory(f"Navigate: {place}")
    return f"NAVIGATE:{place}"

def spotify(song):
    save_memory(f"Spotify: {song}")
    return f"SPOTIFY_PLAY:{song}"

def emergency():
    save_memory("Emergency triggered")
    return "EMERGENCY_CONFIRM"

# ===============================
# VOICE ROUTE
# ===============================

@app.route("/voice", methods=["POST"])
def voice():
    data = request.json
    command = data.get("command","").lower().strip()

    # Emotion detection
    if any(word in command for word in ["tired","stressed","overwhelmed"]):
        set_mode("empathetic")

    # Mode change
    if command.startswith("mode"):
        mode = command.replace("mode","").strip()
        set_mode(mode)
        return f"Mode switched to {mode}"

    # Automation (RAW RETURN)
    if command.startswith("call"):
        return call_contact(command.replace("call","").strip())

    if command.startswith("text"):
        parts = command.replace("text","").strip().split(" ",1)
        if len(parts)==2:
            return text_contact(parts[0], parts[1])

    if command.startswith("whatsapp"):
        parts = command.replace("whatsapp","").strip().split(" ",1)
        if len(parts)==2:
            return whatsapp_contact(parts[0], parts[1])

    if command.startswith("navigate"):
        return navigate(command.replace("navigate","").strip())

    if command.startswith("spotify"):
        return spotify(command.replace("spotify","").strip())

    if command.startswith("emergency"):
        return emergency()

    # Intelligence
    if command.startswith("research"):
        return research(command.replace("research","").strip())

    if command.startswith("finance"):
        return personality_wrap(
            "Financial model:\n1. Emergency fund\n2. Remove debt\n3. Invest\n4. Increase income\n5. Compound long-term."
        )

    if command.startswith("reminder"):
        return schedule_task(command.replace("reminder","").strip())

    if command.startswith("list tasks"):
        return list_tasks()

    return personality_wrap("Command recognized but not categorized.")

# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)
