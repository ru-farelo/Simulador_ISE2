def band_from_score(score: float) -> str:
    if score >= 85:
        return "Distinction"
    if score >= 70:
        return "Merit"
    if score >= 50:
        return "Pass"
    return "Not yet"
