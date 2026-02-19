from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

app = Flask(__name__)

# ===============================
# Personality System
# ===============================

MODE = "ceo"

def set_mode(new_mode):
    global MODE
    MODE = new_mode.lower()

def kai_personality(text):
    if MODE == "ceo":
        prefix = "Andrew, here’s the strategic breakdown:\n\n"
    elif MODE == "chill":
        prefix = "Hey Andrew 🙂 here’s what I found:\n\n"
    elif MODE == "strict":
        prefix = "Direct response:\n\n"
    else:
        prefix = ""
    return prefix + text + "\n\nLet me know the next move."

# ===============================
# Memory System
# ===============================

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(entry):
    memory = load_memory()
    memory.append({
        "timestamp": str(datetime.now()),
        "entry": entry
    })
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

# ===============================
# Task System
# ===============================

TASKS_FILE = "tasks.json"

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
            "priority": priority.lower(),
            "created": str(datetime.now())
        })
        save_tasks(tasks)
        save_memory(f"Task scheduled: {name}")
        return kai_personality(f"Task '{name}' scheduled with {priority} priority.")
    except:
        return kai_personality("Format reminder as: TaskName,minutes,priority")

def list_tasks():
    tasks = load_tasks()
    if not tasks:
        return kai_personality("No tasks scheduled.")
    order = {"high":0,"medium":1,"low":2}
    tasks = sorted(tasks, key=lambda x: order.get(x["priority"], 1))
    output = "Current Tasks:\n"
    for t in tasks:
        output += f"- {t['task']} ({t['priority']})\n"
    return kai_personality(output)

# ===============================
# Research (Multi-Source)
# ===============================

def research(topic):
    try:
        summary = ""

        wiki_url = f"https://en.wikipedia.org/wiki/{topic.replace(' ','_')}"
        r = requests.get(wiki_url)
        soup = BeautifulSoup(r.text, "html.parser")
        for p in soup.select("p")[:5]:
            summary += p.get_text()

        ddg = requests.get(
            f"https://api.duckduckgo.com/?q={topic}&format=json"
        ).json()

        if ddg.get("AbstractText"):
            summary += "\n" + ddg["AbstractText"]

        structured = f"""
Topic: {topic}

1. Core Idea:
{summary[:700]}

2. Strategic Impact:
Understanding this improves decision-making and leverage.

3. Application:
Focus on execution and measurable results.
"""
        save_memory(f"Research: {topic}")
        return kai_personality(structured)

    except:
        return kai_personality("Research failed for that topic.")

# ===============================
# Finance Engine
# ===============================

def finance():
    save_memory("Finance requested")
    return kai_personality("""
Financial Optimization Model:

1. Emergency reserve (3–6 months)
2. Eliminate high-interest debt
3. Invest consistently
4. Increase income leverage
5. Long-term compound strategy
""")

# ===============================
# Automation Bridge
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

def emergency_confirm():
    save_memory("Emergency requested")
    return "EMERGENCY_CONFIRM"

# ===============================
# Routes
# ===============================

@app.route('/')
def home():
    return "Kai Ultimate Automation Assistant is running."

@app.route('/voice', methods=['POST'])
def voice():
    data = request.json
    command = data.get("command","").lower().strip()

    if "research" in command:
        topic = command.replace("research","").strip()
        return jsonify({"response": research(topic)})

    elif "finance" in command:
        return jsonify({"response": finance()})

    elif "reminder" in command:
        details = command.replace("reminder","").strip()
        return jsonify({"response": schedule_task(details)})

    elif "list tasks" in command:
        return jsonify({"response": list_tasks()})

    elif "mode" in command:
        mode = command.replace("mode","").strip()
        set_mode(mode)
        return jsonify({"response": kai_personality(f"Mode switched to {mode}.")})

    elif "call" in command:
        name = command.replace("call","").strip()
        return jsonify({"response": call_contact(name)})

    elif "text" in command:
        parts = command.replace("text","").strip().split(" ",1)
        if len(parts) == 2:
            return jsonify({"response": text_contact(parts[0], parts[1])})

    elif "whatsapp" in command:
        parts = command.replace("whatsapp","").strip().split(" ",1)
        if len(parts) == 2:
            return jsonify({"response": whatsapp_contact(parts[0], parts[1])})

    elif "navigate" in command:
        place = command.replace("navigate","").strip()
        return jsonify({"response": navigate(place)})

    elif "spotify" in command:
        song = command.replace("spotify","").strip()
        return jsonify({"response": spotify(song)})

    elif "emergency" in command:
        return jsonify({"response": emergency_confirm()})

    else:
        return jsonify({"response": kai_personality(
            "Command recognized but not categorized. Try research, finance, reminder, call, text, whatsapp, navigate, spotify."
        )})

# ===============================
# Run
# ===============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)
