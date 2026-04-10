import os
import smtplib
from email.message import EmailMessage
from twilio.rest import Client
import time
import threading

# Cooldown tracking per person_id
last_alert_time = {}
ALERT_COOLDOWN = 60 # seconds

def send_alerts_async(person_id, timestamp, image_path):
    """
    Triggers asynchronous SMS and Email alerts if the cooldown period has passed.
    """
    current_time = time.time()
    
    # Throttle check
    if person_id in last_alert_time:
        if current_time - last_alert_time[person_id] < ALERT_COOLDOWN:
            return # Skip alert due to cooldown
            
    last_alert_time[person_id] = current_time
    
    # Launch threads to avoid blocking video processing
    threading.Thread(target=_send_sms, args=(person_id, timestamp, image_path), daemon=True).start()
    threading.Thread(target=_send_email, args=(person_id, timestamp, image_path), daemon=True).start()

def _send_sms(person_id, timestamp, image_path):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_num = os.environ.get('TWILIO_PHONE_NUMBER')
    to_num = os.environ.get('DEST_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, from_num, to_num]):
        print("Twilio credentials missing in environment variables. SMS skipped.")
        return
        
    try:
        client = Client(account_sid, auth_token)
        # Note: Twilio MMS requires a publicly accessible URL for the image media_url.
        # For a local file, we would need to upload it to an S3 bucket or use a local tunnel (like ngrok).
        # We'll send the text alert as requested and add a placeholder note for the image MMS.
        message = client.messages.create(
            body=f"URGENT: Fall Detected! Person ID: {person_id} at {timestamp}. Please check cameras.",
            from_=from_num,
            to=to_num
        )
        print(f"SMS alert sent successfully (SID: {message.sid})")
    except Exception as e:
        print(f"Error sending SMS alert: {e}")

def _send_email(person_id, timestamp, image_path):
    server = os.environ.get('SMTP_SERVER')
    port = int(os.environ.get('SMTP_PORT', '587'))
    user = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASS')
    to_email = os.environ.get('DEST_EMAIL')
    
    if not all([server, user, password, to_email]):
        print("SMTP credentials missing in environment variables. Email skipped.")
        return
        
    try:
        msg = EmailMessage()
        msg['Subject'] = f"URGENT ALERT: Fall Detected (Person {person_id})"
        msg['From'] = user
        msg['To'] = to_email
        msg.set_content(f"A fall was detected for Person ID {person_id} at timestamp {timestamp}.\n\nPlease find the captured snapshot attached.")
        
        with open(image_path, 'rb') as f:
            img_data = f.read()
            msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename=os.path.basename(image_path))
            
        with smtplib.SMTP(server, port) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        print(f"Email alert sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending Email alert: {e}")
