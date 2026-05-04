import os
import smtplib
import ssl
from datetime import datetime, date
from email.message import EmailMessage

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

POOL_NAME = os.getenv("POOL_NAME", "Agua the Dip")
POOL_LOCATION = os.getenv("POOL_LOCATION", "Dhinde Kalan, Near Asian Public School")
POOL_PHONE = os.getenv("POOL_PHONE", "+91 70069 48378")


def send_reservation_email(data):
    """Send reservation details to the pool owner via SMTP."""
    if not (SMTP_USER and SMTP_PASSWORD and OWNER_EMAIL):
        raise RuntimeError("Email credentials are not configured on the server.")

    subject = f"New Pool Reservation — {data['name']} on {data['date']}"
    body = (
        "A new reservation has been requested.\n\n"
        f"Name      : {data['name']}\n"
        f"Email     : {data['email']}\n"
        f"Phone     : {data['phone']}\n"
        f"Date      : {data['date']}\n"
        f"Time Slot : {data['time']}\n"
        f"People    : {data['people']}\n"
        f"Notes     : {data.get('notes') or '-'}\n\n"
        f"Submitted : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = OWNER_EMAIL
    msg["Reply-To"] = data["email"]
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


@app.route("/")
def index():
    return render_template(
        "index.html",
        pool_name=POOL_NAME,
        pool_location=POOL_LOCATION,
        pool_phone=POOL_PHONE,
        today=date.today().isoformat(),
        year=date.today().year,
    )


@app.route("/reserve", methods=["POST"])
def reserve():
    form = request.get_json(silent=True) or request.form
    required = ["name", "email", "phone", "date", "time", "people"]
    missing = [f for f in required if not str(form.get(f, "")).strip()]
    if missing:
        return jsonify({"ok": False, "error": f"Missing: {', '.join(missing)}"}), 400

    try:
        people = int(form.get("people", 0))
        if people < 1 or people > 100:
            raise ValueError
    except ValueError:
        return jsonify({"ok": False, "error": "People count must be between 1 and 100."}), 400

    try:
        booking_date = datetime.strptime(form["date"], "%Y-%m-%d").date()
        if booking_date < date.today():
            return jsonify({"ok": False, "error": "Please choose a future date."}), 400
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid date format."}), 400

    payload = {
        "name": str(form["name"]).strip(),
        "email": str(form["email"]).strip(),
        "phone": str(form["phone"]).strip(),
        "date": form["date"],
        "time": str(form["time"]).strip(),
        "people": people,
        "notes": str(form.get("notes", "")).strip(),
    }

    try:
        send_reservation_email(payload)
    except Exception as exc:
        app.logger.exception("Email send failed")
        return jsonify({"ok": False, "error": f"Could not send email: {exc}"}), 500

    return jsonify({"ok": True, "message": "Reservation request received! We will contact you shortly."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
