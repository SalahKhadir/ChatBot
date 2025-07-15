import os
import sys
import re
from datetime import datetime

# Try different import methods for PyMuPDF
try:
    import fitz  # PyMuPDF

    print("✅ Using 'fitz' import")
except ImportError:
    try:
        import PyMuPDF as fitz

        print("✅ Using 'PyMuPDF' import")
    except ImportError:
        try:
            import pymupdf as fitz

            print("✅ Using 'pymupdf' import")
        except ImportError:
            print("❌ PyMuPDF not found. Install with: pip install PyMuPDF")
            sys.exit(1)

# Try importing spacy
try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    print("⚠️ spaCy not installed. Install with: pip install spacy")
    SPACY_AVAILABLE = False

# ---------- CONFIG ----------

PDF_PATH = "./SALAH KHADIR CV (ENGLISH).pdf"
SKILLS = {
    "programming": ["php", "python", "javascript", "sql", "c++", "java", "typescript"],
    "frameworks": ["django", "laravel", "springboot", "express", "react", "bootstrap"],
    "frontend": ["html", "css", "javascript", "bootstrap", "react", "jquery"],
    "backend": ["php", "python", "django", "laravel", "springboot", "express"],
    "database": ["sql", "pl/sql", "mysql", "mongodb", "postgresql"],
    "tools": ["git", "docker", "photoshop", "figma", "canva", "tkinter", "excel", "word", "powerpoint"],
    "systems": ["windows", "linux", "rest api", "api"]
}


# ---------- TEXT EXTRACTION ----------

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return ""

    print(f"📄 Reading PDF: {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return ""


# ---------- ENHANCED SKILL MATCHING ----------

def find_skills_by_category(text, skill_categories):
    text = text.lower()
    results = {}

    for category, skills in skill_categories.items():
        found = [skill for skill in skills if skill.lower() in text]
        if found:
            results[category] = found

    return results


# ---------- CONTACT INFORMATION EXTRACTION ----------

def extract_contact_info(text):
    contact_info = {}

    # Email extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact_info['email'] = emails[0]

    # Phone number extraction
    phone_pattern = r'\+212\s?770944640'
    phones = re.findall(phone_pattern, text)
    if phones:
        contact_info['phone'] = phones[0]

    # LinkedIn extraction - look for your specific format
    if '/Salah-KHADIR' in text:
        contact_info['linkedin'] = 'linkedin.com/in/Salah-KHADIR'
    elif '/SalahKhadir' in text:
        contact_info['linkedin'] = 'linkedin.com/in/SalahKhadir'

    # Location
    if 'Errachidia' in text and 'Morocco' in text:
        contact_info['location'] = 'Errachidia, Morocco'

    return contact_info


# ---------- EDUCATION EXTRACTION ----------

def extract_education(text):
    education = []

    # Look for specific education entries
    if 'Computer and Network Engineering' in text:
        education.append('Computer and Network Engineering (2024 – Present)')

    if 'Full Stack Web Development' in text:
        education.append('Full Stack Web Development (2022 – 2024)')

    if 'EMSI Rabat' in text:
        education.append('EMSI Rabat')

    if 'ISTA Mohamed El Fassi' in text:
        education.append('ISTA Mohamed El Fassi - Errachidia')

    return education


# ---------- EXPERIENCE EXTRACTION ----------

def extract_experience(text):
    experience = []

    # Main internship
    if 'Agence du Bassin Hydraulique' in text:
        exp = "Internship at Agence du Bassin Hydraulique Guir-Ziz-Rheris (April 2024) - Led development of Police Patrol Management and Infraction Stock Application using ReactJS, Laravel, MySQL, jQuery, JavaScript, HTML, CSS, REST API"
        experience.append(exp)

    return experience


# ---------- PROJECTS EXTRACTION ----------

def extract_projects(text):
    projects = []

    # Trainee Management System
    if 'Trainee Management System' in text:
        projects.append(
            'Trainee Management System (December 2023) - Python, Tkinter GUI application for managing trainees')

    # Football Tournament Management
    if 'Football Tournament Management' in text:
        projects.append(
            'Football Tournament Management Application (January 2025) - C++ desktop application for tournament organization')

    # SkillSync
    if 'SkillSync' in text:
        projects.append(
            'SkillSync - Recruitment Platform (March 2025) - React.js, Python, Django, MySQL full-stack web application')

    return projects


# ---------- LANGUAGES EXTRACTION ----------

def extract_languages(text):
    languages = []

    if 'Arabic: Native' in text:
        languages.append('Arabic: Native')
    if 'French: Fluent' in text:
        languages.append('French: Fluent')
    if 'English: Fluent' in text:
        languages.append('English: Fluent')

    return languages


# ---------- GENERATE CLEAN REPORT ----------

def generate_report(text, skills, contact_info, education, experience, projects, languages):
    print("\n" + "=" * 60)
    print("🔍 CV ANALYSIS REPORT - SALAH KHADIR")
    print("=" * 60)

    # Contact Information
    print("\n📞 CONTACT INFORMATION:")
    if contact_info:
        for key, value in contact_info.items():
            print(f"  {key.capitalize()}: {value}")
    else:
        print("  ❌ No contact information found")

    # Education
    print("\n🎓 EDUCATION:")
    if education:
        for i, edu in enumerate(education, 1):
            print(f"  {i}. {edu}")
    else:
        print("  ❌ No education information found")

    # Experience
    print("\n💼 PROFESSIONAL EXPERIENCE:")
    if experience:
        for i, exp in enumerate(experience, 1):
            print(f"  {i}. {exp}")
    else:
        print("  ❌ No experience information found")

    # Projects
    print("\n🚀 PROJECTS:")
    if projects:
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project}")
    else:
        print("  ❌ No projects found")

    # Skills by Category
    print("\n🛠️ TECHNICAL SKILLS:")
    if skills:
        for category, skill_list in skills.items():
            print(f"  {category.capitalize()}: {', '.join(skill_list)}")
    else:
        print("  ❌ No technical skills found")

    # Languages
    print("\n🌐 LANGUAGES:")
    if languages:
        for lang in languages:
            print(f"  • {lang}")
    else:
        print("  ❌ No language information found")

    # Summary Stats
    print(f"\n📊 SUMMARY:")
    print(f"  • Total characters: {len(text):,}")
    print(f"  • Total words: {len(text.split()):,}")
    print(f"  • Skills found: {sum(len(skills_list) for skills_list in skills.values())}")
    print(f"  • Education entries: {len(education)}")
    print(f"  • Experience entries: {len(experience)}")
    print(f"  • Projects: {len(projects)}")
    print(f"  • Languages: {len(languages)}")


# ---------- MAIN ----------

def main():
    # Verify PyMuPDF is working
    try:
        print(f"✅ PyMuPDF version: {fitz.version}")
    except AttributeError:
        print("✅ PyMuPDF loaded successfully")

    # Extract text
    text = extract_text_from_pdf(PDF_PATH)
    if not text:
        return

    print(f"\n📄 Processing CV: {PDF_PATH}")
    print(f"📝 Document length: {len(text):,} characters")

    # Perform all analyses
    skills = find_skills_by_category(text, SKILLS)
    contact_info = extract_contact_info(text)
    education = extract_education(text)
    experience = extract_experience(text)
    projects = extract_projects(text)
    languages = extract_languages(text)

    # Generate clean report
    generate_report(text, skills, contact_info, education, experience, projects, languages)

    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"cv_analysis_salah_{timestamp}.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("CV ANALYSIS REPORT - SALAH KHADIR\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"File: {PDF_PATH}\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("CONTACT INFORMATION:\n")
        for key, value in contact_info.items():
            f.write(f"  {key.capitalize()}: {value}\n")

        f.write("\nEDUCATION:\n")
        for edu in education:
            f.write(f"  • {edu}\n")

        f.write("\nEXPERIENCE:\n")
        for exp in experience:
            f.write(f"  • {exp}\n")

        f.write("\nPROJECTS:\n")
        for project in projects:
            f.write(f"  • {project}\n")

        f.write("\nTECHNICAL SKILLS:\n")
        for category, skill_list in skills.items():
            f.write(f"  {category.capitalize()}: {', '.join(skill_list)}\n")

        f.write("\nLANGUAGES:\n")
        for lang in languages:
            f.write(f"  • {lang}\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("FULL EXTRACTED TEXT:\n")
        f.write(text)

    print(f"\n💾 Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()