import os
import smtplib
import ssl
from datetime import datetime, date
from email.message import EmailMessage

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import razorpay
from razorpay.errors import SignatureVerificationError

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

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
PRICE_PER_HOUR = int(os.getenv("PRICE_PER_HOUR", "200"))

razorpay_client = (
    razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET
    else None
)


def send_reservation_email(data):
    """Send reservation details to the pool owner via SMTP."""
    if not (SMTP_USER and SMTP_PASSWORD and OWNER_EMAIL):
        raise RuntimeError("Email credentials are not configured on the server.")

    subject = f"New PAID Pool Reservation — {data['name']} on {data['date']}"
    body = (
        "A new reservation has been received and PAID.\n\n"
        f"Name       : {data['name']}\n"
        f"Email      : {data['email']}\n"
        f"Phone      : {data['phone']}\n"
        f"Date       : {data['date']}\n"
        f"Time Slot  : {data['time']}\n"
        f"People     : {data['people']}\n"
        f"Amount Paid: ₹{data.get('amount_paid', '—')}\n"
        f"Payment ID : {data.get('payment_id', '—')}\n"
        f"Order ID   : {data.get('order_id', '—')}\n"
        f"Notes      : {data.get('notes') or '-'}\n\n"
        f"Submitted  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
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


def _validate_reservation(form):
    required = ["name", "email", "phone", "date", "time", "people"]
    missing = [f for f in required if not str(form.get(f, "")).strip()]
    if missing:
        return None, f"Missing: {', '.join(missing)}"

    try:
        people = int(form.get("people", 0))
        if people < 1 or people > 100:
            raise ValueError
    except ValueError:
        return None, "People count must be between 1 and 100."

    try:
        booking_date = datetime.strptime(form["date"], "%Y-%m-%d").date()
        if booking_date < date.today():
            return None, "Please choose a future date."
    except ValueError:
        return None, "Invalid date format."

    payload = {
        "name": str(form["name"]).strip(),
        "email": str(form["email"]).strip(),
        "phone": str(form["phone"]).strip(),
        "date": form["date"],
        "time": str(form["time"]).strip(),
        "people": people,
        "notes": str(form.get("notes", "")).strip(),
    }
    return payload, None


@app.route("/")
def index():
    return render_template(
        "index.html",
        pool_name=POOL_NAME,
        pool_location=POOL_LOCATION,
        pool_phone=POOL_PHONE,
        razorpay_key_id=RAZORPAY_KEY_ID,
        price_per_hour=PRICE_PER_HOUR,
        today=date.today().isoformat(),
        year=date.today().year,
    )


@app.route("/reserve", methods=["POST"])
def reserve():
    """Validate form and create a Razorpay order. Returns checkout details."""
    if not razorpay_client:
        return jsonify({
            "ok": False,
            "error": "Online payments are not configured. Please contact us by phone."
        }), 503

    form = request.get_json(silent=True) or request.form
    payload, err = _validate_reservation(form)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    amount_paise = payload["people"] * PRICE_PER_HOUR * 100
    receipt = f"agua-{int(datetime.now().timestamp())}"

    try:
        order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": {
                "name": payload["name"],
                "email": payload["email"],
                "phone": payload["phone"],
                "date": payload["date"],
                "time": payload["time"],
                "people": str(payload["people"]),
                "notes": payload["notes"][:240],
            },
        })
    except Exception:
        app.logger.exception("Razorpay order create failed")
        return jsonify({"ok": False, "error": "Could not start payment. Please try again."}), 500

    return jsonify({
        "ok": True,
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key_id": RAZORPAY_KEY_ID,
        "name": POOL_NAME,
        "description": f"Pool reservation — {payload['people']} guest(s) on {payload['date']} ({payload['time']})",
        "prefill": {
            "name": payload["name"],
            "email": payload["email"],
            "contact": payload["phone"],
        },
    })


@app.route("/reserve/verify", methods=["POST"])
def reserve_verify():
    """Verify payment signature, then send the owner email."""
    if not razorpay_client:
        return jsonify({"ok": False, "error": "Payments not configured."}), 503

    data = request.get_json(silent=True) or {}
    pid = data.get("razorpay_payment_id")
    oid = data.get("razorpay_order_id")
    sig = data.get("razorpay_signature")

    if not (pid and oid and sig):
        return jsonify({"ok": False, "error": "Missing payment details."}), 400

    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": oid,
            "razorpay_payment_id": pid,
            "razorpay_signature": sig,
        })
    except SignatureVerificationError:
        return jsonify({"ok": False, "error": "Payment verification failed."}), 400
    except Exception:
        app.logger.exception("Verify error")
        return jsonify({"ok": False, "error": "Verification error."}), 500

    try:
        order = razorpay_client.order.fetch(oid)
        notes = order.get("notes") or {}
        amount_paid = (order.get("amount", 0) or 0) / 100
    except Exception:
        app.logger.exception("Order fetch failed")
        notes, amount_paid = {}, "—"

    email_payload = {
        "name": notes.get("name", "—"),
        "email": notes.get("email", "—"),
        "phone": notes.get("phone", "—"),
        "date": notes.get("date", "—"),
        "time": notes.get("time", "—"),
        "people": notes.get("people", "—"),
        "notes": notes.get("notes", ""),
        "payment_id": pid,
        "order_id": oid,
        "amount_paid": amount_paid,
    }

    try:
        send_reservation_email(email_payload)
    except Exception as exc:
        app.logger.exception("Email failed after payment")
        # Payment succeeded — don't fail the customer; surface a soft notice.
        return jsonify({
            "ok": True,
            "message": f"Payment received. Email confirmation failed — please call us at {POOL_PHONE}.",
            "payment_id": pid,
        })

    return jsonify({
        "ok": True,
        "message": "Payment successful! Your reservation is confirmed — see you at the pool.",
        "payment_id": pid,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
