from flask import Flask, render_template_string, request, jsonify
import smtplib
from email.message import EmailMessage
import schedule
import threading
import time
import json
import requests
from bs4 import BeautifulSoup
import webbrowser
from datetime import datetime
import os

# ------------------------
# Flask app setup
# ------------------------
app = Flask(__name__)

# ------------------------
# Memory / Logs
# ------------------------
TASK_LOG_FILE = "tasks.json"

def load_tasks():
    try:
        with open(TASK_LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks):
    with open(TASK_LOG_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

tasks = load_tasks()

# ------------------------
# Email Function
# ------------------------
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
        return f"✅ Hey Andrew, your email to {to_email} has been sent successfully."
    except Exception as e:
        return f"❌ Sorry Andrew, I couldn’t send the email. Error: {e}"

# ------------------------
# Research Function
# ------------------------
def research_topic(topic):
    url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all('p')
        summary = "\n".join([p.text.strip() for p in paragraphs[:3]])
        return f"Hey Andrew, here’s a quick summary of '{topic}':\n{summary}\n💡 Suggested next steps: check latest news or reports."
    except Exception as e:
        return f"❌ Sorry Andrew, I couldn’t fetch research: {e}"

# ------------------------
# Play Song (Browser safe)
# ------------------------
def play_song(query):
    # Return clickable link instead of opening browser
    return f"🎵 Click to play on YouTube: https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# ------------------------
# Task Scheduler
# ------------------------
def schedule_reminder(task_name, delay_seconds, priority="medium"):
    def reminder():
        print(f"⏰ [{priority.upper()}] Reminder: {task_name}")
    schedule.every(delay_seconds).seconds.do(reminder)
    tasks.append({"task": task_name, "delay": delay_seconds, "priority": priority, "scheduled_at": str(datetime.now())})
    save_tasks(tasks)
    return f"✅ Hey Andrew, your reminder '{task_name}' has been scheduled (priority: {priority})."

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_schedule, daemon=True).start()

# ------------------------
# Flask HTML Template
# ------------------------
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Kai - Your COO Assistant</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 20px; }
        input, textarea { width: 100%; margin: 5px 0; padding: 8px; }
        button { padding: 10px 15px; margin-top: 5px; background: #0077cc; color: white; border: none; cursor: pointer; }
        .output { background: #fff; padding: 10px; margin-top: 10px; white-space: pre-wrap; border-radius: 5px; }
    </style>
</head>
<body>
    <h2>🤖 Kai - Your Human-Like COO Assistant</h2>
    <p>💡 Tip: Tap the input box, press your phone mic, and speak your command!</p>
    <form method="POST" action="/command">
        <label>Command:</label>
        <input type="text" name="command" required placeholder="email, research, reminder, content, finance, play song">
        <label>Details (comma-separated or JSON-like for email/reminder):</label>
        <textarea name="details" rows="4" placeholder="Email: to,subject,body | Reminder: task,delay,priority"></textarea>
        <label>Gmail Email (if needed):</label>
        <input type="text" name="gmail">
        <label>Gmail App Password:</label>
        <input type="password" name="gmail_pass">
        <button type="submit">Send Command</button>
    </form>
    {% if output %}
    <div class="output">{{ output }}</div>
    {% endif %}
</body>
</html>
'''

# ------------------------
# Command Parsing Logic
# ------------------------
def parse_command(cmd, details, gmail="", gmail_pass=""):
    cmd = cmd.strip().lower()
    output = ""

    if "email" in cmd:
        try:
            to_email, subject, body = details.split(',', 2)
            output = send_email(to_email.strip(), subject.strip(), body.strip(), gmail, gmail_pass)
        except:
            output = "❌ Format error for email. Use: to,subject,body"

    elif "research" in cmd:
        output = research_topic(details)

    elif "play song" in cmd:
        output = play_song(details)

    elif "reminder" in cmd or "task" in cmd:
        try:
            task_parts = details.split(',')
            task_name = task_parts[0].strip()
            delay = int(task_parts[1].strip())
            priority = task_parts[2].strip() if len(task_parts) > 2 else "medium"
            output = schedule_reminder(task_name, delay, priority)
        except:
            output = "❌ Format error for reminder. Use: task_name,delay_seconds,priority"

    elif "content" in cmd or "monetize" in cmd:
        output = ("📌 Content Plan:\n"
                  "1. Post 3-5 times/week.\n"
                  "2. Focus on trends in your niche.\n"
                  "3. Include strong hooks and CTAs.\n"
                  "4. Track analytics weekly.\n"
                  "5. Use free editing/scheduling tools.")

    elif "finance" in cmd or "invest" in cmd:
        output = ("💰 Financial Planning:\n"
                  "Enter your income and expenses via console for calculations in this free prototype.\n"
                  "Recommendation: save consistently, consider free ETF research sources for TFSA.")

    else:
        output = "❌ Command not recognized. Try: email, research, reminder, content, finance, play song"

    return output

# ------------------------
# Flask Routes
# ------------------------
@app.route('/', methods=['GET'])
def index():
    return HTML_TEMPLATE

@app.route('/command', methods=['POST'])
def command():
    cmd = request.form['command']
    details = request.form['details']
    gmail = request.form.get('gmail', "")
    gmail_pass = request.form.get('gmail_pass', "")
    output = parse_command(cmd, details, gmail, gmail_pass)
    return render_template_string(HTML_TEMPLATE, output=output)

# ------------------------
# Voice Endpoint for Automation
# ------------------------
@app.route('/voice', methods=['POST'])
def voice():
    data = request.json
    cmd = data.get("command", "")
    details = data.get("details", "")
    gmail = data.get("gmail", "")
    gmail_pass = data.get("gmail_pass", "")
    output = parse_command(cmd, details, gmail, gmail_pass)
    return jsonify({"response": output})

# ------------------------
# Run Flask App (Railway Port Fix)
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
