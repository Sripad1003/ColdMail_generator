import streamlit as st
from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from scrapers import scrape_with_fallbacks
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ---------------- EMAIL CONFIG ----------------
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


# ---------------- STREAMLIT APP ----------------
def create_streamlit_app(llm, portfolio, clean_text):
    st.set_page_config(
        layout="wide",
        page_title="Cold Mail Generator",
        page_icon="📧"
    )

    # ------------- CUSTOM CSS -------------
    st.markdown(
        """
        <style>
        /* Background Gradient */
        .stApp {
            background: linear-gradient(130deg, #001f3f, #003566, #001220);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }

        @keyframes gradientBG {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        /* Fancy Title */
        .title {
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            color: #ffffff;
            padding-bottom: 20px;
            text-shadow: 0px 0px 20px rgba(255,255,255,0.4);
        }

        /* Glassmorphism Card */
        .glass-card {
            background: rgba(255, 255, 255, 0.10);
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.25);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
        }

        /* Buttons */
        .stButton>button {
            background: linear-gradient(90deg, #0077ff, #00bbff);
            color: white;
            padding: 10px 25px;
            border-radius: 8px;
            border: none;
            font-size: 1rem;
            font-weight: 600;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.4);
        }
        .stButton>button:hover {
            scale: 1.05;
            transition: 0.2s;
        }

        /* Input fields */
        .stTextInput>div>div>input {
            background: rgba(255,255,255,0.12);
            color: white;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ---------------- UI ----------------
    st.markdown('<div class="title">📧 Cold Mail Generator</div>', unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns([1.2, 1])

        with col1:
            st.markdown('<div class="glass-card"><h3 style="color:white;">🚀 Start Generating</h3>', unsafe_allow_html=True)

            url_input = st.text_input(
                "🔗 Enter Job URL:",
                value="https://jobs.nike.com/job/R-33460",
                placeholder="Paste job listing URL..."
            )

            mail_input = st.text_input(
                "📨 Receiver Email:",
                placeholder="example@gmail.com"
            )

            submit_button = st.button("🚀 Generate & Send")

            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown(
                """
                <div class="glass-card">
                    <h3 style='color:white;'>✨ How It Works</h3>
                    <ul style='color:white; font-size:1.1rem;'>
                        <li>✓ Scrapes job description automatically</li>
                        <li>✓ Extracts required skills using AI</li>
                        <li>✓ Matches with your portfolio automatically</li>
                        <li>✓ Generates a professional cold email</li>
                        <li>✓ Sends email instantly</li>
                    </ul>
                    <br>
                    <p style='color:#bde0fe;'>Just enter a job URL & email — let AI do the rest.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---------------- PROCESS ----------------
    if submit_button:
        try:
            with st.spinner("🔍 Scraping page... Please wait"):
                scraped = scrape_with_fallbacks(url_input)

            if scraped is None or len(scraped.strip()) < 50:
                st.error("❌ Failed to scrape usable content. Try another URL.")
                return

            cleaned = clean_text(scraped)

            portfolio.load_portfolio()

            with st.spinner("🧠 Extracting job details using AI..."):
                jobs = llm.extract_jobs(cleaned)

            if not jobs:
                st.error("❌ No jobs extracted from scraped content.")
                return

            for job in jobs:
                skills = job.get("skills", [])
                links = portfolio.query_links(skills)
                email = llm.write_mail(job, links)

                st.markdown("<br><div class='glass-card'>", unsafe_allow_html=True)
                st.subheader(f"✉ Generated Email for: **{job.get('role', 'Unknown Role')}**")
                st.code(email, language="markdown")
                st.markdown("</div>", unsafe_allow_html=True)

                with st.spinner("📨 Sending Email..."):
                    result = send_email(
                        receiver_email=mail_input,
                        subject=f"Application for {job.get('role', 'the position')}",
                        body=email,
                        sender_email=sender_email,
                        sender_password=sender_password
                    )

                if result is True:
                    st.success("✔ Email sent successfully!")
                else:
                    st.error(f"❌ Error sending email: {result}")

        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {e}")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    create_streamlit_app(chain, portfolio, clean_text)
