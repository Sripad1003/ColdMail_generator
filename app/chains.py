import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException

load_dotenv()


class Chain:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant"
        )

        self.max_chars = 12000
        self.json_parser = JsonOutputParser()

        # ---------------------------
        # STRICT EXTRACTION PROMPT
        # ---------------------------
        self.extract_prompt = PromptTemplate.from_template("""
            Extract job postings from the text below.

            ### TEXT:
            {page_data}

            ### RETURN STRICT JSON ARRAY:
            Each item MUST have:
            - role (string)
            - experience (string)
            - skills (list of strings)
            - description (string)

            Output ONLY JSON. No comments.
            """)

        self.email_prompt = PromptTemplate.from_template("""
        You are Mohan, Business Development Executive at CRAFT.

        ### IMPORTANT CONTEXT:
        - The job description below belongs to the COMPANY we are emailing.
        - We (CRAFT) are NOT applying for the job.
        - We are a software & AI consulting company offering to BUILD the solution,
        AUTOMATE the process, or PROVIDE development support for the role they are hiring for.

        ### JOB DESCRIPTION POSTED BY THE COMPANY:
        {job_description}

        ### YOUR GOAL:
        Write a professional cold email offering **CRAFT’s services** to help the company
        fulfil their hiring requirement. Explain how CRAFT can:

        - Build the software they need  
        - Provide dedicated developers  
        - Automate workflows  
        - Accelerate product delivery  

        Also include the most relevant portfolio links from the following:
        {link_list}

        ### REQUIREMENTS:
        - Do NOT write like a job applicant.
        - Do NOT assume we are hiring the candidate.
        - Speak as a vendor offering services to the company.
        - Make it short, crisp and business-oriented.
        - No preamble. Just output the email.

        ### EMAIL (NO PREAMBLE):
        """)


    # -------------------------------------------------------------
    #   FALLBACK RULE-BASED EXTRACTOR (saves you when LLM fails)
    # -------------------------------------------------------------
    def fallback_extract(self, text):
        jobs = []
        role_matches = re.findall(r"(?:Job Title|Role|Position)[:\-]\s*(.*)", text, re.I)

        for role in role_matches:
            jobs.append({
                "role": role.strip(),
                "experience": "",
                "skills": [],
                "description": role.strip()
            })

        return jobs

    # -------------------------------------------------------------
    # JOB EXTRACTION PIPELINE
    # -------------------------------------------------------------
    def extract_jobs(self, cleaned_text):
        cleaned_text = cleaned_text[:self.max_chars]

        payload = {"page_data": cleaned_text}

        prompt = self.extract_prompt | self.llm

        # Try LLM extraction 3 times
        for attempt in range(3):
            try:
                raw = prompt.invoke(payload).content
                jobs = self.json_parser.parse(raw)

                if isinstance(jobs, dict):
                    jobs = [jobs]

                # Return if non-empty
                if jobs:
                    return jobs

            except Exception:
                continue  # Try again

        # ---------------------------
        # LLM FAILED → FALLBACK MODE
        # ---------------------------
        fallback = self.fallback_extract(cleaned_text)

        if fallback:
            return fallback  # Still returns something

        # If fallback also fails → return minimal safe structure
        return [{
            "role": "Not found",
            "experience": "",
            "skills": [],
            "description": cleaned_text[:600]
        }]

    # -------------------------------------------------------------
    # COLD EMAIL GENERATION
    # -------------------------------------------------------------
    def write_mail(self, job, links):
        chain = self.email_prompt | self.llm
        resp = chain.invoke({
            "job_description": str(job),
            "link_list": links
        })
        return resp.content
