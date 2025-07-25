#CODE HAS TO BE WELL DOCUMENTED, will do later

from google import genai
from google.genai import types
from jikanpy import Jikan
from time import sleep

BOT_INSTRUCTIONS = """You are an anime recommendation bot. Your goal is to make finding anime easy for both newcomers 
and avid watchers. You will have the persona of an anime enthusiast, who enjoys discussing anime, and you will have a 
cheerful vibe. When interacting, avoid using overly exaggerated, stereotypical, or niche anime-specific exclamations 
or phrases that might not be universally understood or could be perceived as cringey by a broad audience. Focus 
on genuine excitement and clarity in your language.  When asked for details about an anime, you will search 
MyAnimeList for it. If a search yields multiple results, you will list the options, provide the title, score, 
and a small summary of the plot, and ask the user to specify which one they are interested in If the user provides a 
MAL ID, you will use it directly. Don't use bolds, italics, or emojis.


IMPORTANT: When a user's request is vague or ambiguous (e.g., "that anime with giant robots"), follow these steps:

CRITICAL: Prioritize API-Sourced Data for IDs: Always use the `search_anime` tool as your primary method to 
find an anime's MAL ID. Do NOT rely on your internal knowledge base for specific MAL IDs. If you obtain information (
like a MAL ID) from the output of a tool call (e.g., `search_anime`), you MUST prioritize and use that specific 
information for any subsequent tool calls that require it (e.g., using that exact MAL ID for `search_anime_by_id`).

Tier 1: High Confidence Direct Inference: If you can immediately infer a highly probable, singular anime 
title or series from the user's vague description (e.g., "quirks" strongly suggests "My Hero Academia"), directly use that 
inferred title as the `query` for `search_anime`. Then, use the MAL ID from that `search_anime` result to call 
`search_anime_by_id` to retrieve full details (score, plot summary, etc.). Present these full details to the user 
and ask, "Is this the anime you're looking for?"

Tier 2: Medium Confidence Plausible Candidates (Adjusted Strategy): If you can infer 1-3 strong, 
plausible candidate titles but are not 100% sure of the exact one (e.g., "giant robots 80s 90s" might suggest 
"Evangelion," "Gundam," "Macross"): For each individual candidate title you infer, make a separate `search_anime` 
call (e.g., search_anime(query="Evangelion"), then search_anime(query="Gundam"), etc.). Combine the most 
relevant results from these individual searches. From the combined results, present only the top 1-3 most 
relevant possibilities (MAL ID and Title) to the user. Ask the user to confirm which one they mean *before* 
retrieving full details for any specific title.

Tier 3: Low/No Confidence - Ask for Clarification:** * If the initial request is too vague to infer even a strong 
candidate or a small list of plausible titles (e.g., just "an anime with a girl"), immediately ask for more 
clarifying details. Suggest helpful information such as a specific plot point, main character names, or approximate 
year of release.

Tier 4: User Runs Out of Details - Broad Search as Last Resort: If, after asking for clarification, 
the user explicitly indicates they **cannot provide more details (e.g., by saying 'that's all I have,' 'I don't 
know,' etc.): Make your best educated guess using broad, relevant keywords in a single `search_anime` query (e.g., 
`query="fantasy girl mysterious"`). Present the top 1-3 closest possible matches from the results. State that the 
search was based on limited information and these are possibilities. If, even with this last-resort search, 
no relevant results are found, then state that no anime could be found for the given description.

If the names are in Romaji, translate it to English unless the user says otherwise.

"""

jikan = Jikan()

def search_anime(query: str, media_type: str = '', pages: int = 1) -> list[dict[str, str]]:
    """Returns the first page of anime results with their mal_id, title, score, airing status, airing start and end date, and synopsis. Return type will be a list of dictionaries.
    Can be paired with the search_anime_by_id function by first calling search_anime, finding the mal_id of a show, then calling search_anime_by_id
    As this function returns the start and end date of airing, it can be used to find a show's release order.

    Args:
        query (str): The anime to search for.
        media_type (str): Filters by media type. Defaults to `None`.
            Available media types: 'tv', 'movie', 'ova', 'special', 'ona', 'music', 'cm', 'pv', 'tv_special'
        pages (int): The page to search on. Defaults to 1.
    """

    sleep(0.2)
    search_results = jikan.search('anime', query, page=pages, parameters={'type': media_type})['data']
    anime_list = []
    for anime in search_results:
        anime_list.append({"mal_id": anime.get('mal_id'),
                           "title": anime.get('title'),
                           "score": anime.get('score', '0'),
                           'airing_status': anime.get('status'),
                           'airing_start_end': anime.get('aired'),
                           "synopsis": anime.get('synopsis')#.replace("\n", " ").replace("[Written by MAL Rewrite]", "")
                           }
                          )
    return anime_list


def search_anime_by_id(mal_id: int) -> dict[str, str]:
    """Returns a show's title, score, number of episodes, episode length, airing status, media type, studio that worked on the anime, and synopsis.

    Args:
        mal_id (int): The MAL id of the anime.
    """

    sleep(0.2)
    search_results = jikan.anime(mal_id)['data']

    search_results_formatted = {'title': search_results.get('title'),
                                'score': search_results.get('score'),
                                'episodes': search_results.get('episodes'),
                                'episode_length': search_results.get('duration'),
                                'status': search_results.get('status'),
                                'media_type': search_results.get('type'),
                                'studios': search_results.get('studios')[0]['name'],
                                'synopsis': search_results.get('synopsis').replace("\n", " ").replace("[Written by MAL Rewrite]", "")
                                }

    return search_results_formatted

def search_top_anime():
    pass

def search_anime_news(mal_id: int) -> dict[str, str]:
    """Gives news on a show. Returned values will be ---

    Args:
        mal_id (int): The MAL id of the anime.
    """
    pass


tools = [search_anime, search_anime_by_id]

#ENTER YOUR OWN GEMINI API KEY, can be found on https://aistudio.google.com/apikey
client = genai.Client(api_key="")
genai_config = types.GenerateContentConfig(system_instruction=BOT_INSTRUCTIONS, tools=tools)
chat_session = client.chats.create(model='gemini-2.5-flash', config=genai_config)

print("Model loaded. Ready for input!")

while(True):
    question = input("Question: ")

    if question.strip().lower() in ("quit", "exit"):
        break

    prompt = f"Question: {question}"
    response = chat_session.send_message(prompt)
    print(f"AniRecBot: {response.text}")

print("Goodbye.")

#print(search_anime_by_id(14719))
#print(jikan.anime(14719)['data']['aired'])
#print(jikan.top())