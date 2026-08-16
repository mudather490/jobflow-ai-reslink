import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.resume_parser import ResumeParser
from core.pdf_generator import ResumeDocumentGenerator

def main():
    # Look for Mudather's sample resume
    # The instructions say "parse and export Mudather Mohammed's sample resume to PDF"
    # Let's check where the sample resume is, or construct a test one.
    resume_text = """Mudather Mohammed
Software Engineer | AI Engineer
San Francisco, CA | mudather@email.com | +1 (555) 123-4567 | linkedin.com/in/mudather | github.com/mudather

PROFESSIONAL SUMMARY
Highly motivated Software Engineer specializing in Python, React, and Machine Learning. And Ai Application Development. Proven track record of delivering scalable solutions.

TECHNICAL SKILLS
Python, JavaScript, TypeScript, React, Next.js, Node.js, FastAPI, PostgreSQL, MongoDB, Redis, PyTorch, LangChain, LlamaIndex, Docker, AWS. Includes Linux. Numpy. Numpy. Pytorch : • Pandas

EXPERIENCE
Software Engineer | Tech Innovators Inc. (2021 - Present)
• Developed scalable backend services handling 10k+ requests per second using FastAPI. — Company
• Built interactive dashboards with React and Next.js for data visualization. — Company
• Built interactive dashboards with React and Next.js for data visualization. — Company
• Integrated LangChain for AI-driven insights. — Company

AI Engineer Intern | Future Solutions (2020 - 2021)
• Trained custom LLM models for text summarization. — Company
• Designed and implemented a vector database using Pinecone for semantic search. — Company

PROJECTS
Real-Time Analytics Platform - A comprehensive analytics engine built with Python and React.
Real-Time Analytics Platform - A comprehensive analytics engine built with Python and React.
AI Chat Assistant - Intelligent agent built using LangGraph and OpenAI.

EDUCATION
B.S. in Computer Science | University of California, Berkeley (2016 - 2020)
"""
    # Write to a test text file
    with open("test_mudather_resume.txt", "w") as f:
        f.write(resume_text)

    # Parse it
    profile = ResumeParser.parse_file("test_mudather_resume.txt")
    
    print(f"Name: {profile.full_name}")
    print(f"Skills: {profile.skills}")
    print(f"Categorized Skills: {profile.categorized_skills}")
    print(f"Experience bullets for first job: {profile.experience[0].bullets}")
    print(f"Projects: {[p.name for p in profile.projects]}")

    # Generate PDF
    pdf_path = "mudather_resume_test.pdf"
    ResumeDocumentGenerator.generate_pdf(profile, pdf_path)
    print(f"PDF generated at {pdf_path}")
    
    # Clean up txt
    os.remove("test_mudather_resume.txt")

if __name__ == "__main__":
    main()
