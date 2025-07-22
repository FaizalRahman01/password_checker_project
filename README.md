
#  Password Weakness Checker (Cybersecurity Mini Project)

This is a simple Flask web app to check if a user's Gmail password is weak by using a basic password list.

---

##  Features

- Web form to enter email
- Uses a password list to try common passwords
- Sends email to user if their password is found (or not)

---

##  Requirements

- Python 3.x
- Flask
- Gmail App Password (for sending email)

---

##  How to Run

1. Open terminal inside project folder
2. (Optional) Create a virtual environment:

    ```
    python -m venv venv
    source venv/bin/activate  # for macOS/Linux
    .\venv\Scripts\activate  # for Windows
    ```

3. Install Flask:

    ```
    pip install flask
    ```

4. Edit `app.py`:
   - Replace `yourgmail@gmail.com` with your Gmail
   - Replace `your_app_password` with your Gmail App Password

5. Run the app:

    ```
    python app.py
    ```

6. Open your browser at:

    ```
    http://127.0.0.1:5000/
    ```

---

##  Disclaimer

This is for educational use only. Do not use for illegal activities. Always take permission.

---

## Author

**Name:** Faizal Rahman  
**Course:** BCA Final Year (Cybersecurity)  
**Email:** faizalrahman7834@gmail.com
