from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings

warnings.filterwarnings('ignore')


def compute_tfidf_score(jd_text: str, resume_text: str) -> float:
    """
    Compute TF-IDF based similarity score between job description and resume.
    
    Args:
        jd_text: Job description text
        resume_text: Resume text
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        if not jd_text or not resume_text:
            return 0.0
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        
        # Fit and transform both texts
        vectors = vectorizer.fit_transform([jd_text, resume_text])
        
        # Compute cosine similarity
        similarity_matrix = cosine_similarity(vectors[0:1], vectors[1:2])
        
        # Extract and return score
        score = float(similarity_matrix[0][0])
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    except Exception as e:
        print(f"Warning: Failed to compute TF-IDF score: {str(e)}")
        return 0.0


def compute_final_score(tfidf_score: float, skill_match_pct: float,
                        experience_years: float) -> float:
    """
    Compute final weighted score combining TF-IDF, skill matching, and experience.
    
    Args:
        tfidf_score: TF-IDF similarity score (0-1)
        skill_match_pct: Percentage of required skills found (0-1)
        experience_years: Years of experience
        
    Returns:
        Final weighted score between 0 and 1 (rounded to 4 decimals)
    """
    try:
        # Weighted base score
        base_score = (tfidf_score * 0.5) + (skill_match_pct * 0.4)
        
        # Experience bonus
        experience_bonus = 0.0
        if experience_years >= 3:
            experience_bonus = 0.10
        elif experience_years >= 1:
            experience_bonus = 0.05
        
        # Final score with cap at 1.0
        final_score = min(base_score + experience_bonus, 1.0)
        
        return round(final_score, 4)
    except Exception as e:
        print(f"Warning: Failed to compute final score: {str(e)}")
        return 0.0


def rank_candidates(results: list) -> list:
    """
    Rank candidates by final score in descending order.
    
    Args:
        results: List of candidate result dictionaries
        
    Returns:
        Sorted list with "rank" key added to each candidate
    """
    try:
        if not results:
            return []
        
        # Sort by final_score descending
        sorted_results = sorted(results, key=lambda x: x.get("final_score", 0.0), reverse=True)
        
        # Add rank
        for idx, result in enumerate(sorted_results):
            result["rank"] = idx + 1
        
        return sorted_results
    except Exception as e:
        print(f"Warning: Failed to rank candidates: {str(e)}")
        return results
