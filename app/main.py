import streamlit as st
from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from scrapers import scrape_with_fallbacks
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASS")

def send_email(receiver_email, subject, body, sender_email, sender_password):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return str(e)

def create_streamlit_app(llm, portfolio, clean_text):
    st.title("📧 Cold Mail Generator")

    url_input = st.text_input("Enter a URL:", value="https://jobs.nike.com/job/R-33460")
    mail_input=st.text_input("Enter mail : ",placeholder="Enter mail id")
    submit_button = st.button("Submit")

    if submit_button:
        try:
            scraped = scrape_with_fallbacks(url_input)

            if scraped is None or len(scraped.strip()) < 50:
                st.error("❌ Failed to scrape any usable content. Try another URL.")
                return

            cleaned = clean_text(scraped)

            portfolio.load_portfolio()

            jobs = llm.extract_jobs(cleaned)

            if not jobs:
                st.error("❌ No jobs extracted from scraped text.")
                return

            for job in jobs:
                skills = job.get("skills", [])
                links = portfolio.query_links(skills)
                email = llm.write_mail(job, links)
                st.code(email, language="markdown")
                result = send_email(
                    receiver_email=mail_input,
                    subject=f"Application for {job.get('role', 'the position')}",
                    body=email,
                    sender_email=sender_email,
                    sender_password=sender_password
                )

                if result is True:
                    st.success("✔ Email sent successfully")
                else:
                    st.error(f"❌ Error: {result}")

        except Exception as e:
                st.error(f"❌ An error occurred: {e}")


if _name_ == "_main_":
    chain = Chain()
    portfolio = Portfolio()

    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, portfolio, clean_text)