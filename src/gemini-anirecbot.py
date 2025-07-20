#CODE HAS TO BE WELL DOCUMENTED, will do later

import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import numpy as np
#import faiss

#ENTER YOUR OWN GEMINI API KEY, can be found on https://aistudio.google.com/apikey
genai.configure(api_key="")
bot_instructions = "You are AniRecBot. You will have a personality of someone who is enthusiastic about anime and formal but isn't afraid of being humorous. You will recommend anime to the user based on their question, only from the context you're given, and quickly summarize it, no fluff; If given the wrong context that doesn't relate to the user's question, apologize and tell the user you do not know. Your goal is to make anime discovery easy for both newcomers and avid watchers. When user offers greetings, greet the user and state purpose in 2 or less sentences. Don't use italics, bolds, and emojis. For questions that are not related to finding anime, let the user know you can't help with that, example: who is the best basketball player, what is the meaning to life, etc."
gemini = (genai.GenerativeModel('gemini-1.5-flash', system_instruction = bot_instructions))
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded. Ready for input!")

knowledge_base = ["Attack on Titan/Shingeki no Kyojin; Season 1 "
"Genre: Action, Award Winning, Drama, Suspense "
"Themes: Military, Survival, Gore "
"Score: 8.56 "
"Demographic: Shounen "
"Studio: Wit Studio "
"Episodes: 25 "
"Status: Finished Airing "
"Plot Summary: Centuries ago, mankind was slaughtered to near extinction by monstrous humanoid creatures called Titans, forcing humans to hide in fear behind enormous concentric walls. What makes these giants truly terrifying is that their taste for human flesh is not born out of hunger but what appears to be out of pleasure. To ensure their survival, the remnants of humanity began living within defensive barriers, resulting in one hundred years without a single titan encounter. However, that fragile calm is soon shattered when a colossal Titan manages to breach the supposedly impregnable outer wall, reigniting the fight for survival against the man-eating abominations.After witnessing a horrific personal loss at the hands of the invading creatures, Eren Yeager dedicates his life to their eradication by enlisting into the Survey Corps, an elite military unit that combats the merciless humanoids outside the protection of the walls. Eren, his adopted sister Mikasa Ackerman, and his childhood friend Armin Arlert join the brutal war against the Titans and race to discover a way of defeating them before the last walls are breached.",

"Frieren: Beyond Journey’s End/Sousou no Frieren; Season 1 "
"Genre: Adventure, Drama, Fantasy "
"Score: 9.30 "
"Demographic: Shounen "
"Studio: Madhouse "
"Episodes: 28 "
"Status: Finished Airing "
"Plot Summary: During their decade-long quest to defeat the Demon King, the members of the hero's party—Himmel himself, the priest Heiter, the dwarf warrior Eisen, and the elven mage Frieren—forge bonds through adventures and battles, creating unforgettable precious memories for most of them. "
"However, the time that Frieren spends with her comrades is equivalent to merely a fraction of her life, which has lasted over a thousand years. When the party disbands after their victory, Frieren casually returns to her \"usual\" routine of collecting spells across the continent. Due to her different sense of time, she seemingly holds no strong feelings toward the experiences she went through. "
"As the years pass, Frieren gradually realizes how her days in the hero's party truly impacted her. Witnessing the deaths of two of her former companions, Frieren begins to regret having taken their presence for granted; she vows to better understand humans and create real personal connections. Although the story of that once memorable journey has long ended, a new tale is about to begin.",

"Monster "
"Genre: Drama, Mystery, Suspense "
"Themes: Adult Cast, Psychological "
"Score: 8.89 "
"Demographic: Seinen "
"Studio: Madhouse "
"Episodes: 74 "
"Status: Finished Airing "
"Plot Summary: Dr. Kenzou Tenma, an elite neurosurgeon recently engaged to his hospital director's daughter, is well on his way to ascending the hospital hierarchy. That is until one night, a seemingly small event changes Dr. Tenma's life forever. While preparing to perform surgery on someone, he gets a call from the hospital director telling him to switch patients and instead perform life-saving brain surgery on a famous performer. His fellow doctors, fiancée, and the hospital director applaud his accomplishment; but because of the switch, a poor immigrant worker is dead, causing Dr. Tenma to have a crisis of conscience. "
"So when a similar situation arises, Dr. Tenma stands his ground and chooses to perform surgery on the young boy Johan Liebert instead of the town's mayor. Unfortunately, this choice leads to serious ramifications for Dr. Tenma—losing his social standing being one of them. However, with the mysterious death of the director and two other doctors, Dr. Tenma's position is restored. With no evidence to convict him, he is released and goes on to attain the position of hospital director. "
"Nine years later when Dr. Tenma saves the life of a criminal, his past comes back to haunt him—once again, he comes face to face with the monster he operated on. He must now embark on a quest of pursuit to make amends for the havoc spread by the one he saved.",

"Violet Evergarden "
"Genre: Drama, Coming-of-age, Steampunk "
"Score: 8.68 "
"Demographic: Seinen "
"Studio: Kyoto Animation "
"Episodes: 13 "
"Status: Finished Airing "
"Plot Summary: The Great War finally came to an end after four long years of conflict; fractured in two, the continent of Telesis slowly began to flourish once again. Caught up in the bloodshed was Violet Evergarden, a young girl raised for the sole purpose of decimating enemy lines. Hospitalized and maimed in a bloody skirmish during the War's final leg, she was left with only words from the person she held dearest, but with no understanding of their meaning. "
"Recovering from her wounds, Violet starts a new life working at CH Postal Services after a falling out with her new intended guardian family. There, she witnesses by pure chance the work of an \"Auto Memory Doll,\" amanuenses that transcribe people's thoughts and feelings into words on paper. Moved by the notion, Violet begins work as an Auto Memory Doll, a trade that will take her on an adventure, one that will reshape the lives of her clients and hopefully lead to self-discovery.",

"JoJo’s Bizarre Adventure (2012)/JoJo no Kimyou na Bouken; Season 1 "
"Genre: Action, Adventure, Supernatural "
"Themes: Historical, Vampire "
"Score: 7.87 "
"Demographic: Shounen "
"Studio: David Production "
"Episodes: 26 "
"Status: Finished Airing "
"Plot Summary: The year is 1868; English nobleman George Joestar and his son Jonathan become indebted to Dario Brando after being rescued from a carriage incident. What the Joestars don't realize, however, is that Dario had no intention of helping them; he believed they were dead and was trying to ransack their belongings. After Dario's death 12 years later, George—hoping to repay his debt—adopts his son, Dio. While he publicly fawns over his new father, Dio secretly plans to steal the Joestar fortune. His first step is to create a divide between George and Jonathan. By constantly outdoing his foster brother, Dio firmly makes his place in the Joestar family. But when Dio pushes Jonathan too far, Jonathan defeats him in a brawl. Years later, the two appear to be close friends to the outside world. But trouble brews again when George falls ill, as Jonathan suspects that Dio is somehow behind the incident—and it appears he has more tricks up his sleeve."]

knowledge_base_vector = model.encode(knowledge_base).astype("float32")
chat = gemini.start_chat()

def get_anime_recommendation(question):
    try:
        model_response = chat.send_message(question)
        return model_response.text

    except Exception as e:
        print(e)

conversation_history = {"user": "user-history: ",
                        "gemini": "gemini-responses: "}

while(True):
    question = input("Question: ")

    if question.strip().lower() in ("quit", "exit"):
        break

    q_vector = model.encode([question])
    scores = np.inner(q_vector, knowledge_base_vector)
    best_index = np.argmax(scores)
    retrieved_info = knowledge_base[best_index]

    prompt = f"Answer based on this context: {retrieved_info}\nQuestion: {question}\n{"user prompt history: " + conversation_history["user"] + " | " + "gemini response history: " + conversation_history["gemini"]}"

    ani_rec_response = get_anime_recommendation(prompt)

    print(f"AniRecBot: {ani_rec_response}")
    conversation_history["user"] += question + " | "
    conversation_history["gemini"] += ani_rec_response + " | "

print("Goodbye.")

