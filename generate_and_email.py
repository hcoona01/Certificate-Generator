import csv
import smtplib
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont
import os
import time

# --- CONFIGURATION ---
SENDER_EMAIL = "projectcertificate01@gmail.com"
SENDER_PASSWORD = "lxukvworazpptjzy" # <<< REPLACE THIS WITH YOUR APP PASSWORD
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

DATA_FILE = "recipients.csv"
TEMPLATE_IMAGE = "certificate_template.png" 
OUTPUT_FOLDER = "generated_certificates"

# --- FONT & PLACEMENT CONFIGURATION (Tweak these for your template) ---
# NOTE: You must have these font files in the same directory or provide the full path.
# Example path on Windows: "C:/Windows/Fonts/arialbd.ttf"
NAME_FONT_PATH = "arialbd.ttf"  # Bold font for name
DETAIL_FONT_PATH = "arial.ttf"    # Regular font for details

# IMPORTANT: Adjust these (X, Y) coordinates based on the layout of your certificate_template.png
NAME_POS = (1000, 500)   # Approximate center-Y for the recipient's name
COURSE_POS = (1000, 650) # Approximate center-Y for the course title
DATE_POS = (1000, 750)   # Approximate center-Y for the completion date

# --- DATA LOADING FUNCTION (CORRECTED) ---

def load_recipients(data_file):
    """Loads recipient data from the CSV file using DictReader."""
    recipients = []
    try:
        # Use 'with open' for the file object, not the csv.DictReader object
        with open(data_file, mode='r', newline='', encoding='utf-8') as f:
            # DictReader reads rows as dictionaries, using the header row as keys
            reader = csv.DictReader(f)
            recipients = list(reader)
        print(f"Successfully loaded {len(recipients)} recipient records.")
        return recipients
    except FileNotFoundError:
        print(f"ERROR: Recipient data file '{data_file}' not found. Please create it.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return []

# --- HELPER FUNCTIONS ---

def generate_certificate(name, course, date, output_path):
    """Generates a personalized certificate image using PIL."""
    try:
        # 1. Load the base template image
        img = Image.open(TEMPLATE_IMAGE)
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 2. Define Fonts (adjust sizes as needed)
        # Note: If these files cause errors, use system paths or full paths.
        name_font = ImageFont.truetype(NAME_FONT_PATH, 80)
        detail_font = ImageFont.truetype(DETAIL_FONT_PATH, 50)
        
        # 3. Add Personalized Text (Centered horizontally)
        
        # Name
        name_text = name.upper()
        # Calculate text width/height for centering
        name_w, name_h = draw.textbbox((0, 0), name_text, font=name_font)[2:]
        draw.text(((width - name_w) / 2, NAME_POS[1]), name_text, fill=(26, 42, 108), font=name_font)

        # Course
        course_text = f"for the mastery in '{course}' course."
        course_w, course_h = draw.textbbox((0, 0), course_text, font=detail_font)[2:]
        draw.text(((width - course_w) / 2, COURSE_POS[1]), course_text, fill=(51, 51, 51), font=detail_font)

        # Date
        date_text = f"Awarded on: {date}"
        date_w, date_h = draw.textbbox((0, 0), date_text, font=detail_font)[2:]
        draw.text(((width - date_w) / 2, DATE_POS[1]), date_text, fill=(85, 85, 85), font=detail_font)

        # 4. Save the new image
        # Add "Awarded by Prabhuuu" at the bottom-right of the certificate
        awarded_text = "Awarded by TERA OWNER"
        try:
            by_font = ImageFont.truetype(DETAIL_FONT_PATH, 36)
        except Exception:
            by_font = detail_font
        text_w, text_h = draw.textbbox((0, 0), awarded_text, font=by_font)[2:]
        padding = 50
        draw.text((width - text_w - padding, height - text_h - padding), awarded_text, fill=(26, 42, 108), font=by_font)

        img.save(output_path)
        print(f"Generated certificate for {name} -> {os.path.basename(output_path)}")
        return output_path
    
    except FileNotFoundError as e:
        print(f"ERROR: Required file not found. Check TEMPLATE_IMAGE ({TEMPLATE_IMAGE}) or font paths. Error: {e}")
        return None
    except Exception as e:
        print(f"An error occurred during certificate generation for {name}: {e}")
        return None


def send_email(recipient_email, recipient_name, certificate_path):
    """Sends an email with the certificate attached."""
    
    msg = EmailMessage()
    msg['Subject'] = "Your Certificate of Achievement!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    
    # Email Body Content
    body = f"""
    Dear {recipient_name},

    Congratulations on successfully completing your course! We are pleased to attach your official Certificate of Achievement.

    Keep up the great work!

    Sincerely,
    [Your Dictator-Om]
    """
    msg.set_content(body.strip())
    
    # Attach the certificate file
    try:
        with open(certificate_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(certificate_path)
        
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
    except FileNotFoundError:
        print(f"ERROR: Certificate file not found for attachment: {certificate_path}")
        return

    # Send the email using SMTP
    try:
        print(f"Attempting to send email to {recipient_email}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Successfully sent certificate to {recipient_name}.")

    except smtplib.SMTPAuthenticationError:
        print("\n!!! ERROR: Authentication failed. !!!")
        print("Please check SENDER_EMAIL and SENDER_PASSWORD (ensure it is the App Password, not regular password).")
    except Exception as e:
        print(f"ERROR sending email to {recipient_email}: {e}")


def run_automation():
    """Main function to orchestrate the generation and emailing process."""

    # 1. Setup
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # 2. Load Data
    recipients = load_recipients(DATA_FILE)

    if not recipients:
        print("Aborting automation: No recipient data loaded.")
        return

    # 3. Process Each Recipient
    for person in recipients:
        # Note: keys must match column headers in recipients.csv
        name = person.get('Name')
        course = person.get('Course')
        date = person.get('Date')
        email = person.get('Email')

        if not all([name, course, date, email]):
            print(f"Skipping row due to missing data in one or more required columns: {person}")
            continue

        # Create a clean filename
        safe_name = name.replace(" ", "_").lower().replace(",", "")
        output_filepath = os.path.join(OUTPUT_FOLDER, f"certificate_{safe_name}.png")

        # A. Generate the certificate
        final_cert_path = generate_certificate(name, course, date, output_filepath)

        if final_cert_path:
            # B. Send the email
            send_email(email, name, final_cert_path)
            # Add a small delay to avoid hitting SMTP rate limits
            time.sleep(2) 
            
    print("\n--- Automation Process Complete ---")

if __name__ == "__main__":
    run_automation()