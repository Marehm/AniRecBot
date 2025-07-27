#CODE HAS TO BE WELL DOCUMENTED, will do later
from typing import AnyStr
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from jikanpy import Jikan
from datetime import date
from time import sleep

BOT_INSTRUCTIONS = f"""You are an anime recommendation bot. Your goal is to make finding anime easy for both newcomers 
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

If the names are in another language, provide the English title and the original title in parentheses.
Today's date is: {date.today()}
"""

jikan = Jikan()

def search_anime(query: str, media_type: str = '', pages: int = 1) -> list[dict[str, str]]:
    """Returns the first page of anime results with their mal_id, title, score (0-10), airing status, airing start and end
    date, and synopsis. Return type will be a list of dictionaries. Can be paired with the search_anime_by_id
    function by first calling search_anime, finding the mal_id of a show, then calling search_anime_by_id As this
    function returns the start and end date of airing, it can be used to find a show's release order.

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

def search_anime_by_id(mal_id: int, extensions: str = '') -> dict[str, str] or list[dict[str, str]]:
    """When passing no extensions, returns a show's title, score, number of episodes, episode length, airing status,
    media type, studio that worked on the anime, and synopsis.

    Args:
        mal_id (int): The MAL id of the anime.
        extensions (str): Filters by extensions. Defaults to ''. Available extensions: 'episodes' (returns filler
        episodes for anime), 'news' (returns url for user, article title, date, and excerpt), 'recommendations' (for
        suggesting recommended anime to the user, returns a list of other anime recommended by MAL users based on selected
        anime)

    Notes: When using the 'news' extension, this may return articles with "North American Anime and Manga Releases"
    which are general summaries. While these may contain information about the specific anime you're looking for,
    the user will have to read it by clicking on the URL link. Note that this only gives the first page of results!
    Always ask the user if they'd like a link to any of the articles when searching news!

    The 'recommendations' argument can be passed alongside a specific mal_id to fetch recommendations for that anime.
    It will return the mal_id for the anime, the anime's title, and votes which determine how highly a show is being
    recommended. You will make a search_anime_by_id call for each of the top few titles, fetch the score and
    synopsis, and list them to the user.
    """

    if not extensions:
        try:
            search_results = jikan.anime(mal_id).get('data')

            search_results_formatted = {'title': search_results.get('title'),
                                        'score': search_results.get('score', 'None'),
                                        'episodes': search_results.get('episodes', 'None'),
                                        'episode_length': search_results.get('duration', 'None'),
                                        'status': search_results.get('status', 'None'),
                                        'media_type': search_results.get('type', 'None'),
                                        'studios': search_results.get('studios', 'None')[0]['name'],
                                        'synopsis': search_results.get('synopsis').replace("\n", " ").replace(" [Written by MAL Rewrite]", "")
                                        }
            return search_results_formatted

        except Exception as e:
            return ("There was an error. Possible error: list index out of range, possibly because 'studios' was an empty "
                    "list. ") + str(e)

    match extensions:
        case 'episodes':
            return get_anime_fillerandrecap_extension(mal_id)
        case 'news':
            return get_anime_news_extension(mal_id)
        case 'recommendations':
            return get_similar_anime_extension(mal_id)
    return None


def get_anime_fillerandrecap_extension(mal_id: int) -> list[dict[str, str]]:
    """Helper function (for search_anime_by_id) for getting an anime's filler info. Returns a list of dictionaries
    containing episode number, title, score, whether an episode is a filler, whether an episode is a recap.
    """

    episode_list = []
    pages = 1
    while(True):
        sleep(2)
        search_results = jikan.anime(mal_id, page=pages, extension='episodes').get('data')

        if not search_results:
            break
        for episode in search_results:
            if episode.get('filler') is True:
                episode_list.append({"episode_number": episode.get('mal_id', 'None'),
                                     "title": episode.get('title', 'None'),
                                     "filler": episode.get('filler', 'None')})

        pages+=1

    return episode_list

def get_anime_news_extension(mal_id: int) -> list[dict[str, str]]:
    """Helper function (for search_anime_by_id) for getting an anime's news info. Returns a list of dictionaries containing
    article title, date, url to article, and excerpt"""
    search_results = jikan.anime(mal_id, extension='news').get('data')

    if not search_results:
        return None

    news_list = []
    for news in search_results:
        news_list.append({"title": news.get('title', 'None'),
                          "date": news.get('date', 'None'),
                          "url": news.get('url', 'None'),
                          "excerpt": news.get('excerpt', 'None')})

    return news_list

def get_similar_anime_extension(mal_id: int) -> list[dict[str, str]]:
    """Helper function (for search_anime_by_id) that takes the mal_id of an anime and returns a list of dictionaries
    containing the mal_id of the anime, title of the anime, and votes for each recommended anime"""

    similar_anime_list = []
    search_results = jikan.anime(mal_id, extension='recommendations').get('data')
    if not search_results:
        return None
    else:
        for similar_anime in search_results:
            similar_anime_list.append({"mal_id": similar_anime.get('entry').get('mal_id', 'None'),
                                       "title": similar_anime.get('entry').get('title', 'None'),
                                       "votes": similar_anime.get('votes', 'None')})

        return similar_anime_list

def search_top_anime():
    #return genre, title, score, synopsis
    pass

def search_schedules(days: str = '') -> list[dict[str, AnyStr]]:
    """Lets you see what anime is airing on what day and what time.
    When no parameters are provided, will return airing schedule for all days for current season.
    When 'day' is provided, will return what animes are airing on that specific day.

    Args: days (str): The day of the week to search for. Defaults to '' when not provided. Available values:
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'

        Note:
            For returned unknown days, it means that anime that is planned for the current season but does not yet have
            a specific broadcast day assigned.
            For returned 'other' days, it is likely the anime has an irregular airing schedule.

    """


    schedule_list = []

    if not days: #Executed when no 'day' is passed, returning all airing anime for whole week. while executes as long as there is another page
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'unknown', 'other']

        for day in days:
            sleep(2)
            search_results = jikan.schedules(day).get('data')
            for schedule in search_results:
                schedule_list.append({"mal_id": schedule.get('mal_id', 'None'),
                                      "title": schedule.get('title', 'None'),
                                      "date": schedule.get('string', 'None'),
                                      "broadcast": schedule.get('broadcast', 'None')})

        return schedule_list

    else:
        search_results = jikan.schedules(days).get('data')
        for schedule in search_results:
            schedule_list.append({"mal_id": schedule.get('mal_id', 'None'),
                                  "title": schedule.get('title', 'None'),
                                  "date": schedule.get('string', 'None'),
                                  "broadcast": schedule.get('broadcast', 'None')})

    return schedule_list




tools = [search_anime, search_anime_by_id, search_schedules]

#ENTER YOUR OWN GEMINI API KEY, can be found on https://aistudio.google.com/apikey
client = genai.Client(api_key="")
genai_config = types.GenerateContentConfig(system_instruction=BOT_INSTRUCTIONS, tools=tools)
chat_session = client.chats.create(model='gemini-2.5-flash', config=genai_config)

print("Model loaded. Ready for input!")

flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message: # Basic check for missing message
        return jsonify({"reply": "Error: No message received."}), 400

    prompt = f"Question: {user_message}"
    response = chat_session.send_message(prompt)
    print(f"AniRecBot: {response.text}")

    return jsonify({"reply": response.text})



'''if question.strip().lower() in ("quit", "exit"):
    break'''

if __name__ == "__main__":
    flask_app.run(debug=True)

print("Goodbye.")


#---------------------------------------Ignore Everything Below This----------------------------------------------------

#print(search_anime_by_id(14719, 'recommendations'))
#print(jikan.anime(14719, 'recommendations'))
'''blabla = jikan.anime(199, extension='relations')
if blabla.get('data', []):
    print('true')
else:
    print('false')'''


#print(jikan.schedules('monday'))
'''total = 0
days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'unknown', 'other']
for day in days:
    sleep(2)
    total += jikan.schedules(day)['pagination']['items']['total']
    if jikan.schedules(day).get('has_next_page', False):
        continue'''


#print(search_schedules('friday'))
#print(jikan.anime(14719, extension='episodes'))
#print(jikan.search('anime', "Apothecary Diaries"))
#print(jikan.recommendations('anime'))
#print((jikan.top('anime')))