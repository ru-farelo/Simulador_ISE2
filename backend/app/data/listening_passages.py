"""Fixed B2-level listening scripts for the Independent Listening task.
Written to be read aloud naturally (via TTS), ~180-200 words, followed by
one gist question and one detail question — matching the real task, where
the general question comes after the first play and the detail question
after the second.
"""

FIXED_PASSAGES: list[dict] = [
    {
        "id": "fixed-community-gardens",
        "topic": "Community gardens",
        "text": (
            "Over the past decade, more and more empty spaces in cities have been turned "
            "into something surprising: community gardens. What used to be abandoned lots, "
            "covered in rubbish and weeds, are now full of vegetables, flowers, and "
            "neighbours working side by side. The idea is simple. A group of residents "
            "gets permission from the local council to use a piece of unused land, and "
            "everyone who joins contributes a little time each week to look after it. In "
            "return, they share whatever they grow. Supporters say the benefits go far "
            "beyond the fresh produce. Many people who take part say they've made friends "
            "they would never have met otherwise, especially older residents who often "
            "feel isolated. Children get a chance to learn where food actually comes from, "
            "something increasingly rare in a world of supermarkets and delivery apps. Of "
            "course, not everything runs smoothly. Some gardens have struggled with "
            "disagreements over who does the work and who gets to keep the harvest. Even "
            "so, most cities that have tried the idea report having long waiting lists of "
            "people wanting to join, which suggests the model, imperfect as it is, has "
            "clearly struck a chord."
        ),
        "general_question": "What is this talk mainly about?",
        "detail_question": "According to the speaker, what problem have some community gardens experienced?",
    },
    {
        "id": "fixed-digital-detox",
        "topic": "Digital detox retreats",
        "text": (
            "A growing number of people are paying good money to do something that would "
            "have sounded strange a generation ago: switch off their phones completely for "
            "a weekend. These are called digital detox retreats, and they've become "
            "surprisingly popular among busy professionals. On arrival, guests are asked to "
            "hand in their phones, laptops and smartwatches at reception, sometimes for as "
            "long as five days. What they get instead is a schedule built entirely around "
            "things that don't involve a screen: long walks, cooking together, board games, "
            "and simply sitting in silence. Organisers say the first day is always the "
            "hardest. Many guests report feeling anxious, even reaching instinctively for a "
            "pocket that no longer holds a phone. By the second or third day, though, most "
            "people describe a kind of mental quiet they haven't experienced in years. "
            "Sleep improves, conversations get longer, and several guests have said they "
            "noticed things around them, like birdsong or the weather, that they'd stopped "
            "paying attention to. Critics argue that a few days away solves nothing if "
            "people go straight back to their old habits the moment they get their phone "
            "back. Retreat organisers admit this is a fair point, but insist that even a "
            "short break can be the push someone needs to make a lasting change."
        ),
        "general_question": "What is the speaker mainly describing?",
        "detail_question": (
            "What do critics say about digital detox retreats, and how do organisers "
            "respond to that criticism?"
        ),
    },
]
