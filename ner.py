import re
import warnings
import spacy
from skills_list import SKILLS

warnings.filterwarnings('ignore')

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None


def extract_name(text: str) -> str:
    """
    Extract candidate name using spaCy NER from entire resume or first 1000 chars.
    
    Args:
        text: Resume text
        
    Returns:
        Candidate name or "Unknown"
    """
    try:
        if not nlp or not text:
            return "Unknown"
        
        # Process first 1000 chars for better name extraction
        short_text = text[:1000]
        doc = nlp(short_text)
        
        # Try to find the most likely PERSON entity
        person_names = []
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                if len(name) > 1 and not name.isdigit() and not re.search(r'email|phone|linkedin|github|portfolio', name, re.I):
                    person_names.append(name)
        if person_names:
            multi_word_names = [n for n in person_names if len(n.split()) > 1]
            return max(multi_word_names or person_names, key=len)

        # Fallback: look for name patterns in the top section of the resume
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        top_lines = lines[:12]
        generic_terms = re.compile(r'\b(?:email|phone|contact|linkedin|github|portfolio|address|objective|summary|profile|experience|skills|education|qualification|resume|cv|curriculum vitae|professional|developer|engineer|manager|analyst|consultant|intern|student|company|organization|institute|university|college)\b', re.I)

        def clean_name_line(line: str) -> str:
            line = re.sub(r'^(?:name|full name)[:\-]\s*', '', line, flags=re.I).strip()
            line = re.sub(r'\b(?:resume|cv|curriculum vitae)\b', '', line, flags=re.I).strip()
            line = re.sub(r'\s*[|\-]\s*.*$', '', line).strip()
            return line

        def looks_like_name(line: str) -> bool:
            if not line or len(line) < 5 or len(line) > 60:
                return False
            if re.search(r'[@\d]|http|www\.|mailto:|\(|\)', line, re.I):
                return False
            if generic_terms.search(line):
                return False

            words = line.split()
            if not 2 <= len(words) <= 4:
                return False

            titlecase_words = sum(
                1 for word in words if re.match(r"^([A-Z][a-z]+|[A-Z]\.|[A-Z][a-z]+[-'][A-Z][a-z]+)$", word)
            )
            if titlecase_words < len(words):
                return False

            if any(re.match(r'^(hibernate|spring|docker|kubernetes|react|tamil|nadu|india|developer|engineer|manager)$', w, re.I) for w in words):
                return False

            return True

        for line in top_lines:
            cleaned = clean_name_line(line)
            if looks_like_name(cleaned):
                return cleaned

        for line in top_lines:
            m = re.match(r'^(?:name|full name)[:\-]\s*(.+)$', line, flags=re.I)
            if m:
                candidate = clean_name_line(m.group(1).strip())
                if looks_like_name(candidate):
                    return candidate

        return "Unknown"
    except Exception as e:
        print(f"Warning: Failed to extract name: {str(e)}")
        return "Unknown"


def extract_skills(text: str) -> list:
    """
    Extract skills from resume text using keyword matching.
    
    Args:
        text: Resume text
        
    Returns:
        List of matched skills (deduplicated)
    """
    try:
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = set()
        
        for skill in SKILLS:
            # Use word boundary matching for accuracy
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        return sorted(list(found_skills))
    except Exception as e:
        print(f"Warning: Failed to extract skills: {str(e)}")
        return []


def extract_education(text: str) -> str:
    """
    Extract education qualification from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        Education level or "Not specified"
    """
    try:
        if not text:
            return "Not specified"
        
        text_lower = text.lower()
        
        # Education keywords to search for
        education_patterns = [
            r"b\.tech\b",
            r"b\.e\b",
            r"b\.sc\b",
            r"m\.tech\b",
            r"m\.sc\b",
            r"mba\b",
            r"mca\b",
            r"bca\b",
            r"ph\.d\b",
            r"phd\b",
            r"\bbachelor\b",
            r"\bmaster\b",
            r"\bdiploma\b",
            r"b\.com\b",
            r"m\.com\b",
            r"\bbe\b",
            r"\bme\b",
        ]
        
        for pattern in education_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return match.group(0).upper()
        
        return "Not specified"
    except Exception as e:
        print(f"Warning: Failed to extract education: {str(e)}")
        return "Not specified"


def extract_experience_years(text: str) -> float:
    """
    Extract years of experience from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        Years of experience as float
    """
    try:
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Check for fresher or 0 years
        if re.search(r'\bfresher\b', text_lower):
            return 0.0
        if re.search(r'\b0\s*years?\b', text_lower):
            return 0.0
        if re.search(r'\bno\s+experience\b', text_lower):
            return 0.0
        
        # Extract numeric experience patterns
        experience_matches = []
        
        # Pattern: "3 years", "2.5 years", "5+ years"
        numeric_pattern = r'(\d+\.?\d*)\s*\+?\s*years?'
        matches = re.findall(numeric_pattern, text_lower)
        if matches:
            experience_matches.extend([float(m) for m in matches])
        
        # Word-based: "three years", "five years", etc.
        word_numbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10
        }
        for word, num in word_numbers.items():
            if re.search(rf'\b{word}\s+years?\b', text_lower):
                experience_matches.append(float(num))
        
        # Return highest experience found
        if experience_matches:
            return max(experience_matches)
        
        return 0.0
    except Exception as e:
        print(f"Warning: Failed to extract experience: {str(e)}")
        return 0.0


def analyze_resume(text: str, jd_skills: list) -> dict:
    """
    Comprehensive resume analysis extracting all key information.
    
    Args:
        text: Resume text
        jd_skills: List of required skills from job description
        
    Returns:
        Dictionary with analysis results
    """
    try:
        if not text:
            return {
                "name": "Unknown",
                "education": "Not specified",
                "experience_years": 0.0,
                "skills_found": [],
                "skills_missing": jd_skills if jd_skills else [],
                "skill_match_pct": 0.0
            }
        
        # Extract all information
        name = extract_name(text)
        education = extract_education(text)
        experience_years = extract_experience_years(text)
        skills_found = extract_skills(text)
        
        # Calculate skill matching
        skills_missing = [s for s in jd_skills if s not in skills_found]
        skill_match_pct = len(skills_found) / len(jd_skills) if jd_skills else 0.0
        
        return {
            "name": name,
            "education": education,
            "experience_years": experience_years,
            "skills_found": skills_found,
            "skills_missing": skills_missing,
            "skill_match_pct": skill_match_pct
        }
    except Exception as e:
        print(f"Warning: Failed to analyze resume: {str(e)}")
        return {
            "name": "Unknown",
            "education": "Not specified",
            "experience_years": 0.0,
            "skills_found": [],
            "skills_missing": jd_skills if jd_skills else [],
            "skill_match_pct": 0.0
        }
