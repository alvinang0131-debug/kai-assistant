from flask import Flask, request, jsonify
import json
import schedule
import threading
import time
from datetime import datetime
import webbrowser
import smtplib
from email.message import EmailMessage
import random

app = Flask(__name__)

# -------------------------
# Memory / Task Storage
# -------------------------
MEMORY_FILE = "kai_memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {"tasks": [], "notes": []}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

memory = load_memory()

# -------------------------
# Scheduler
# -------------------------
def schedule_reminder(task_name, delay_seconds, priority="medium"):
    def reminder():
        print(f"⏰ [{priority.upper()}] Reminder: {task_name}")
    schedule.every(delay_seconds).seconds.do(reminder)
    memory["tasks"].append({
        "task": task_name,
        "delay": delay_seconds,
        "priority": priority,
        "scheduled_at": str(datetime.now())
    })
    save_memory(memory)
    return f"✅ Reminder '{task_name}' scheduled (priority: {priority})"

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_schedule, daemon=True).start()

# -------------------------
# Email
# -------------------------
def send_email(to_email, subject, body, sender_email, sender_password):
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return f"✅ Email to {to_email} sent."
    except Exception as e:
        return f"❌ Email failed: {e}"

# -------------------------
# Research
# -------------------------
def research_topic(topic):
    # Placeholder: can be extended with ChatGPT free web scraping
    search_engines = ["Wikipedia", "DuckDuckGo"]
    engine = random.choice(search_engines)
    return f"🧠 Researching '{topic}' using {engine} (mock summary)."

# -------------------------
# Play Music
# -------------------------
def play_song(query):
    webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
    return f"🎵 Playing '{query}' on YouTube."

# -------------------------
# Emotional / Personality
# -------------------------
PERSONALITY_MODES = ["ceo","chill","strict","humor","empathetic","briefing","whisper"]

def tone_response(message, mode="ceo"):
    if mode=="humor":
        return f"{message} 😎"
    elif mode=="whisper":
        return f"{message.lower()}…"
    elif mode=="briefing":
        return f"{message} (summary)"
    elif mode=="empathetic":
        return f"{message} 💛"
    elif mode=="chill":
        return f"{message} ✌️"
    elif mode=="strict":
        return f"{message.upper()}!"
    else:
        return message

# -------------------------
# Voice Endpoint
# -------------------------
@app.route("/voice", methods=["POST"])
def voice():
    data = request.get_json()
    command_raw = data.get("command","").lower()
    personality = data.get("mode","ceo").lower()
    personality = personality if personality in PERSONALITY_MODES else "ceo"

    # Call
    if "call" in command_raw:
        contact = command_raw.replace("call","").strip()
        return jsonify({"response": f"CALL_CONTACT:{contact}"})
    
    # Text
    elif "text" in command_raw:
        parts = command_raw.replace("text","").split(":",1)
        contact = parts[0].strip()
        message = parts[1].strip() if len(parts)>1 else " "
        return jsonify({"response": f"TEXT_CONTACT:{contact}:{message}"})
    
    # WhatsApp
    elif "whatsapp" in command_raw:
        parts = command_raw.replace("whatsapp","").split(":",1)
        contact = parts[0].strip()
        message = parts[1].strip() if len(parts)>1 else " "
        return jsonify({"response": f"WHATSAPP_CONTACT:{contact}:{message}"})
    
    # Navigate
    elif "navigate" in command_raw:
        place = command_raw.replace("navigate","").strip()
        return jsonify({"response": f"NAVIGATE:{place}"})
    
    # Play music
    elif "play song" in command_raw or "play music" in command_raw:
        song = command_raw.replace("play song","").replace("play music","").strip()
        msg = play_song(song)
        return jsonify({"response": f"SPOTIFY_PLAY:{song}"})
    
    # Alarm
    elif "alarm" in command_raw or "set alarm" in command_raw:
        time_part = command_raw.replace("alarm","").replace("set alarm","").strip()
        return jsonify({"response": f"ALARM:{time_part}"})
    
    # Emergency
    elif "emergency" in command_raw:
        return jsonify({"response":"EMERGENCY_CONFIRM:TRUE"})
    
    # Reminder
    elif "reminder" in command_raw or "task" in command_raw:
        try:
            parts = command_raw.split(",")
            task_name = parts[0].strip()
            delay = int(parts[1].strip())
            priority = parts[2].strip() if len(parts)>2 else "medium"
            result = schedule_reminder(task_name, delay, priority)
            return jsonify({"response": tone_response(result, personality)})
        except:
            return jsonify({"response":"ERROR: Format reminder as task_name,delay_seconds,priority"})
    
    # Research
    elif "research" in command_raw:
        topic = command_raw.replace("research","").strip()
        result = research_topic(topic)
        return jsonify({"response": tone_response(result, personality)})
    
    # Email
    elif "email" in command_raw:
        return jsonify({"response":"EMAIL: Use Gmail credentials to send (mock placeholder)."})
    
    # Default
    else:
        return jsonify({"response": tone_response(f"🤖 Kai received: {command_raw}", personality)})

# -------------------------
# Run App
# -------------------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
