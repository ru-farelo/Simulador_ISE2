"""Fixed Reading exams transcribed from real Trinity ISE II class material
(context/Trinity/Julio2026/). Answer keys were cross-checked against the
source texts by hand — see the class worksheets for the tutor's originals.
"""

FIXED_EXAMS: list[dict] = [
    {
        "id": "trinity-julio-2026",
        "source": "fixed",
        "task1": {
            "title": "Emotional Intelligence",
            "paragraphs": [
                {
                    "id": "1",
                    "text": (
                        "In a famous experiment, a group of four year-olds were left alone with candy and "
                        "they were told that they could not eat any until the adult returned. Years later, "
                        "when the children were grown-ups, researchers did a follow-up to the experiment. "
                        "It turned out that children who resisted the temptation became more successful "
                        "later in life. Traditionally, psychologists described intelligence in terms of "
                        "problem-solving and memory. This test shows the importance of another kind of "
                        "intelligence, so-called emotional intelligence. IQ tests are only one way to see "
                        "how successful someone may become in life. Social and emotional abilities seem "
                        "even more important."
                    ),
                },
                {
                    "id": "2",
                    "text": (
                        "Emotional intelligence is a buzz word that is often heard. So, what does it really "
                        "mean? The term 'emotional intelligence' was coined in 1990. Emotional intelligence "
                        "has to do with knowing when to express emotions and knowing when to control them. "
                        "Empathy is a particularly important part of emotional intelligence. This is "
                        "basically the ability to recognise other people's emotions."
                    ),
                },
                {
                    "id": "3",
                    "text": (
                        "It is necessary though to make a distinction between emotional intelligence and "
                        "emotional competence. Let me illustrate this with an example. We already mentioned "
                        "empathy as the ability to understand what someone else is feeling. Emotional "
                        "competence would then mean transforming this into a skill. Empathy can actually be "
                        "used to influence other people's behavior. Obviously we are talking about influence "
                        "in a positive manner as opposed to manipulation."
                    ),
                },
                {
                    "id": "4",
                    "text": (
                        "Emotional intelligence is important for a successful performance at work but how "
                        "can it be promoted? First and foremost, the competencies that are important are "
                        "different from job to job, so it is essential to know what these are for your "
                        "field. Self-awareness is here the core competence to develop. So employees should "
                        "learn how their feelings and behavior affect themselves and others. After that, "
                        "look at the individual and try to find out if they have the necessary social "
                        "skills for a particular job. Then, share this information with the individual and "
                        "when doing so, try to be as clear as possible. Always conduct feedback in a "
                        "constructive manner because then it is more likely to be taken on board. Another "
                        "advantage of constructive criticism is that it minimizes defensiveness."
                    ),
                },
                {
                    "id": "5",
                    "text": (
                        "Hiring competent trainers is key. Good trainers have empathy and are genuinely "
                        "caring. They should adopt a step-by-step approach because a change in behaviour is "
                        "more likely to happen if it is manageable and achievable. Trainers should provide "
                        "ongoing feedback and help develop the skill of self-reflection. If there is no "
                        "follow-up training, then the whole process is likely not to be taken seriously."
                    ),
                },
            ],
            "exercise_a": {
                "instructions": (
                    "Read the text quickly. Choose the best title for each paragraph. There is one more "
                    "title than you need."
                ),
                "items": [{"id": p, "text": f"Paragraph {p}"} for p in ["1", "2", "3", "4", "5"]],
                "options": [
                    {"id": "A", "text": "Turning emotional intelligence into a skill"},
                    {"id": "B", "text": "Emotional intelligence in the workplace"},
                    {"id": "C", "text": "Train the trainers"},
                    {"id": "D", "text": "Cognitive and emotional intelligence"},
                    {"id": "E", "text": "Choosing the right people"},
                    {"id": "F", "text": "Its true meaning"},
                ],
                "allow_repeat_options": False,
                "correct": {"1": "D", "2": "F", "3": "A", "4": "B", "5": "E"},
            },
            "exercise_b": {
                "instructions": "What different words or phrases can be found in the text for the following?",
                "items": [
                    {"id": "b1", "text": "turning"},
                    {"id": "b2", "text": "in the workplace"},
                    {"id": "b3", "text": "cognitive intelligence"},
                    {"id": "b4", "text": "emotional intelligence"},
                    {"id": "b5", "text": "choosing the right people"},
                    {"id": "b6", "text": "its true meaning"},
                ],
                "accepted_answers": {
                    "b1": ["transforming"],
                    "b2": ["at work", "job", "at their job", "job to job"],
                    "b3": ["problem-solving and memory", "problem-solving, memory"],
                    "b4": ["social and emotional abilities"],
                    "b5": ["hiring competent trainers"],
                    "b6": ["so, what does it really mean", "what does it really mean"],
                },
            },
            "exercise_c": {
                "instructions": "Read the text again. Are the statements True or False?",
                "statements": [
                    {"id": "c1", "text": "There was no correlation between eating the candy and later achievements."},
                    {"id": "c2", "text": "Part of emotional intelligence is being able to put yourself in someone else's shoes."},
                    {"id": "c3", "text": "We should distinguish influence from manipulation."},
                    {"id": "c4", "text": "People may get hostile when talking about their job performance."},
                    {
                        "id": "c5",
                        "text": (
                            "It is sufficient to give the employee information about their performance "
                            "since it is their own responsibility to improve."
                        ),
                    },
                ],
                "correct": {"c1": False, "c2": True, "c3": True, "c4": True, "c5": False},
            },
            "exercise_d": {
                "instructions": "Complete the sentences with information from the text.",
                "items": [
                    {"id": "d1", "text": "I'm very proud of myself as last night I ___ to smoke."},
                    {"id": "d2", "text": "My manager likes using trendy words. Self-reflection seems to be his new ___ at the moment."},
                    {"id": "d3", "text": "He is obviously not able to ___ his true feelings."},
                    {"id": "d4", "text": "Drinking a lot of water is ___ if you want to survive."},
                    {"id": "d5", "text": "He seems to have ___ my advice ___, as he is a lot more polite now."},
                ],
                "accepted_answers": {
                    "d1": ["resisted the temptation", "resisted"],
                    "d2": ["buzz word"],
                    "d3": ["express"],
                    "d4": ["essential"],
                    "d5": ["taken my advice on board", "taken ... on board", "taken on board"],
                },
            },
        },
        "task2": {
            "title": "Bullying",
            "texts": [
                {
                    "id": "A",
                    "text": (
                        "Bullying is of all times, but a more recent phenomenon is cyberbullying in which "
                        "the bully uses email, text messages, twitter and other social media or online "
                        "forums to hurt the victim. It is no surprise that celebrities who are constantly in "
                        "the public eye are cyberbullied relentlessly. Celebrities are critized literally "
                        "for every move they make. A lot of the comments are about looks. Celebrities need "
                        "to have a thick skin to deal with this constant stream of criticism. Some seem to "
                        "do fine though. This may have to do with past experiences as surprisingly many "
                        "celebrities have been the victim of bullying when they were young. Bullying is a "
                        "serious problem to such an extent that many children and teenagers are afraid to "
                        "go to school. The main reasons for becoming a victim of bullying are appearance and "
                        "social status. Bullies attack their victims physically and psychologically. "
                        "Bullying can have terrible effects on its victims. Schoolwork may suffer, but also "
                        "health. Research suggests that victims may suffer from mental health problems "
                        "later in life such as depression, low self-esteem and anxiety. This doesn't have to "
                        "be the case though. Many famous people have been bullied as a child and despite "
                        "this experience have become very successful."
                    ),
                },
                {
                    "id": "B",
                    "text": (
                        "We cited appearance as a major reason for being bullied. Ironically, the exact "
                        "reason for being bullied has made some celebrities successful. Supermodel Tyra "
                        "Banks for example was made fun of for being so thin. This exact thin physique "
                        "helped her to have a very successful career as a model. Athlete Michael Phelps was "
                        "bullied in school for his long arms. Later he won several medals at the Olympic "
                        "Games and those long arms will certainly not have been at his disadvantage."
                    ),
                },
                {
                    "id": "C",
                    "text": (
                        "Batman actor Christian Bale used to be beaten up a lot when he was a kid. He feels "
                        "that it has made him stronger. It was for him a lesson for life. Christian didn't "
                        "hit back. Violence often makes things worse as you don't know what the bully's "
                        "response will be. Using violence could in the end have brought him more trouble. "
                        "Holding the anger cannot be easy but perhaps humor can be thrown in to fend the "
                        "bully off. Comic actor Chris Rock for example claims he developed his quick wit as "
                        "a response to being bullied."
                    ),
                },
                {
                    "id": "D",
                    "text": (
                        "Actor and singer Selena Gomez was bullied all the way through elementary and middle "
                        "school. She said that it was her energy and focus that made her a target. "
                        "Ultimately, the experience has made her a stronger person. A similar story we hear "
                        "from colleague singer Rihanna. She also got bullied in school but now she is even "
                        "grateful as the teasing has made her tough. Extravagant pop star Lady Gaga went "
                        "even further as she actively uses her experience of being bullied to reach out to "
                        "her fans and this way tries to give them hope. Singer and actor Brittany Snow also "
                        "used her negative experience for something positive by setting up a non-profit "
                        "organization that seeks to put an end to bullying."
                    ),
                },
            ],
            "exercise_a": {
                "instructions": "Read the four texts and decide which text each question refers to.",
                "items": [
                    {"id": "1", "text": "shows how negative traits can become positive?"},
                    {"id": "2", "text": "mentions further steps to end the problem discussed?"},
                    {"id": "3", "text": "refers to a more modern variant of the problem mentioned?"},
                    {"id": "4", "text": "gives reasons and consequences of bullying?"},
                    {"id": "5", "text": "gives advice on how to deal with aggression?"},
                ],
                "options": [{"id": t, "text": f"Text {t}"} for t in ["A", "B", "C", "D"]],
                "allow_repeat_options": True,
                "correct": {"1": "B", "2": "D", "3": "A", "4": "A", "5": "C"},
            },
            "exercise_b": {
                "instructions": "Tick the five statements from 1-8 that are true according to the four texts.",
                "options": [
                    {"id": "o1", "text": "Cyberbullying is a modern form of bullying."},
                    {"id": "o2", "text": "A number of celebrities are hardened by their negative experience."},
                    {"id": "o3", "text": "Bullying can have a negative influence on someone's performance at school."},
                    {"id": "o4", "text": "Christian Bale used to react violently to being bullied."},
                    {"id": "o5", "text": "After having lost weight, Tyra Banks became successful."},
                    {"id": "o6", "text": "Some comedic actors think they learned how to be funny thanks to the problems they had with bullies."},
                    {"id": "o7", "text": "Selena Gomez was bullied when she was a kid."},
                    {"id": "o8", "text": "Lady Gaga set up a charity with her colleague Brittany Snow to end bullying."},
                ],
                "select_count": 5,
                "correct": ["o1", "o2", "o3", "o6", "o7"],
            },
            "exercise_c": {
                "instructions": "Complete the summary notes with suitable words or phrases from the texts.",
                "items": [
                    {"id": "c1", "text": "Celebrities are often the victim of cyberbullying which means constant ___ through social media."},
                    {"id": "c2", "text": "Bullying can have an impact on schoolwork and ___, often psychological problems in later life."},
                    {"id": "c3", "text": "T. Banks and M. Phelps were bullied because of their appearance but ironically later thanked their ___ to it."},
                    {"id": "c4", "text": "Ch. Bale and Ch. Rock didn't use ___ in response to their bullies."},
                    {"id": "c5", "text": "Lady Gaga wants to give hope to her fans and B. Snow started a ___ to end bullying."},
                ],
                "accepted_answers": {
                    "c1": ["criticism"],
                    "c2": ["health"],
                    "c3": ["success"],
                    "c4": ["violence"],
                    "c5": ["non-profit organisation", "non-profit organization", "charity"],
                },
            },
        },
        "task3": {
            "title": "Family Business",
            "texts": [
                {
                    "id": "A",
                    "text": (
                        "The continued growth of family businesses. Family businesses today are a very "
                        "important part of the economy as they account for 65% of all private enterprises "
                        "and for 40% of all private sector employment. But how successful are they?\n\n"
                        "It is claimed that family businesses are more effective than other businesses "
                        "because they are more concerned with the long-term future of the company as they "
                        "want to transfer the business to the next generation. They also would like to "
                        "extend the family's reputation locally, nationally, or even internationally. There "
                        "is usually little disagreement as to the financial benefits each family member "
                        "should take from the business.\n\n"
                        "However, there are drawbacks to family enterprises too. The head of the family "
                        "business may want to give relatives a chance when there are other people outside "
                        "the family who are better qualified to do the job. It is also rare for more than "
                        "one family member to have the required skills to drive the business in an "
                        "increasingly competitive environment."
                    ),
                },
                {
                    "id": "B",
                    "text": (
                        "We asked members of the public if they would like to work in a family business.\n\n"
                        "Frederic: I think it would be really nice. We would all have to take "
                        "responsibility to create something we could be proud of as a family.\n\n"
                        "Ling: I wouldn't really like it because I think it would be pretty boring. I want "
                        "to meet lots of different people in a large and dynamic workplace.\n\n"
                        "Cathy: We could never get away from work. Some people say they couldn't work with "
                        "families, but I couldn't work without them.\n\n"
                        "Adam (@Ling): I used to work in a big company and it is not as stimulating as you "
                        "might think. Colleagues you thought were friends aren't always!\n\n"
                        "Sanjit: I want to be an international lawyer so to achieve this is not so easy with "
                        "a family business. Besides, I would rather have my own independence and be able to "
                        "pursue my own career path."
                    ),
                },
                {
                    "id": "C",
                    "text": (
                        "Wednesday, 26th June\n\n"
                        "I am so excited! Tomorrow Mum and I will go and see our first customers. I can't "
                        "believe it is only 6 weeks ago since I suggested to Mum the idea of starting up our "
                        "own wedding planning business. All because my friend Sandy wanted to organise a "
                        "different sort of wedding and she couldn't find anyone to help her to do it. And we "
                        "helped her realise her special day. She was so happy with the venue, food, "
                        "flowers, everything!\n\n"
                        "It is essential we do a really good job with these first few customers so we can "
                        "build up a good reputation. Dad told us having your own business isn't as easy as "
                        "we might think. He said it's far more time consuming than we could imagine, but the "
                        "sense of satisfaction can be amazing.\n\n"
                        "I should sleep now as it's already 1am. I've just realised I spent 3 hours "
                        "researching stuff for tomorrow!"
                    ),
                },
                {
                    "id": "D",
                    "text": (
                        "Chart — Longevity of Family Businesses: a large majority of family businesses "
                        "never get past the first generation; of those that do, a further share never gets "
                        "past the second generation; a smaller share still is lost before the third "
                        "generation; only a small minority make it to the fourth generation and beyond."
                    ),
                },
            ],
            "exercise_1_5": {
                "instructions": (
                    "Read questions 1-5 first, then read Texts A-D. Decide which text each question refers "
                    "to. You can use any letter more than once."
                ),
                "items": [
                    {"id": "1", "text": "talks about the prospects for a new business she is starting?"},
                    {"id": "2", "text": "analyses the long-term success of family businesses?"},
                    {"id": "3", "text": "expresses personal feelings about working in family firms?"},
                    {"id": "4", "text": "outlines some of the benefits and weaknesses of a family business?"},
                    {"id": "5", "text": "compares the economic importance of family businesses with other businesses?"},
                ],
                "options": [{"id": t, "text": f"Text {t}"} for t in ["A", "B", "C", "D"]],
                "allow_repeat_options": True,
                "correct": {"1": "C", "2": "D", "3": "B", "4": "A", "5": "A"},
            },
            "exercise_6_10": {
                "instructions": "Choose the five statements from A-H below that are TRUE according to the texts.",
                "options": [
                    {"id": "A", "text": "Family businesses employ more people than other types of businesses."},
                    {"id": "B", "text": "Family relatives are often not as qualified as outsiders to work in family businesses."},
                    {"id": "C", "text": "Adam thinks Ling should be careful of colleagues she chooses to be friends."},
                    {"id": "D", "text": "Sanjit thinks he can achieve his ambitions within a family business structure."},
                    {"id": "E", "text": "The diary writer doesn't believe that she would have had the idea for a business if her friend Sandy hadn't had a problem."},
                    {"id": "F", "text": "The diary writer was surprised how quickly the time had gone."},
                    {"id": "G", "text": "The majority of family businesses are passed onto a second generation."},
                    {"id": "H", "text": "There is a steady decline of the success of family businesses with each passing generation."},
                ],
                "select_count": 5,
                "correct": ["B", "C", "E", "F", "H"],
            },
        },
    }
]
