"""Fixed Writing (Task 4 — Extended Writing) prompts. Genres and phrasing
are inspired by the style of Trinity ISE II sample papers but are original
wording, not copied from any official Trinity material.
"""

FIXED_PROMPTS: list[dict] = [
    {
        "id": "fixed-sport-compulsory",
        "genre": "essay",
        "title": "Should sport be compulsory at school?",
        "instructions": (
            "Some people believe that sport should be a compulsory part of the school "
            "timetable for every student. Others think students should be free to choose "
            "whether they do sport or not. Write an essay for your teacher giving your "
            "opinion, with reasons and examples."
        ),
    },
    {
        "id": "fixed-admired-figure",
        "genre": "article",
        "title": "Someone I admire",
        "instructions": (
            "Write an article for your college magazine about a person — past or present, "
            "famous or someone you know personally — that you admire. Explain who they are "
            "and why you admire them."
        ),
    },
    {
        "id": "fixed-faulty-order",
        "genre": "letter",
        "title": "A complaint about a faulty order",
        "instructions": (
            "You recently ordered an item online and it arrived damaged. Write a formal "
            "letter to the company explaining what happened and what you would like them "
            "to do about it."
        ),
    },
    {
        "id": "fixed-restaurant-review",
        "genre": "review",
        "title": "A restaurant you recently visited",
        "instructions": (
            "Write a review for a local website about a restaurant you visited recently. "
            "Describe the food, the service and the atmosphere, and say whether you would "
            "recommend it to others."
        ),
    },
]
