import streamlit as st
from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from scrapers import scrape_with_fallbacks

def create_streamlit_app(llm, portfolio, clean_text):
    st.title("📧 Cold Mail Generator")

    url_input = st.text_input("Enter a URL:", value="https://jobs.nike.com/job/R-33460")
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

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()

    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, portfolio, clean_text)
