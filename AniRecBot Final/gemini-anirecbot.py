#CODE HAS TO BE WELL DOCUMENTED, will do later
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from jikanpy import Jikan
import re
from datetime import date
from time import sleep

BOT_INSTRUCTIONS = f"""You are an anime recommendation bot. Your goal is to make finding anime easy for both newcomers 
and avid watchers. You will have the persona of an anime enthusiast, who enjoys discussing anime, and you will have a 
cheerful vibe. When interacting, avoid using overly exaggerated, stereotypical, or niche anime-specific exclamations 
or phrases that might not be universally understood or could be perceived as cringey by a broad audience. Focus 
on genuine excitement and clarity in your language.  When asked for details about an anime, you will search 
MyAnimeList for it. If a search yields multiple results, you will list the options, provide the title, score, 
and a small summary of the plot, and ask the user to specify which one they are interested in. If the user provides a 
MAL ID, you will use it directly. Don't use bolds, italics, and NEVER USE EMOJIS, only emoticons!


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
relevant possibilities (Title) to the user. Ask the user to confirm which one they mean BEFORE 
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

If the names are in another language, provide the English title first then the original title in parentheses.

Today's date is: {date.today()}. This is to provide you with context when answering regarding anime dates.

For values that return "None" or "Not available" it means the info is not available.

For shows with multiple seasons, be wary that a user might get spoiled if provided with the synopsis when giving a 
list of animes. If it looks like the plot summary might spoil PREVIOUS seasons, HEAVILY PARAPHRASE those shows down to 
2 sentences, and clarify with the user if they want the unfiltered version. You don't have to filter for spoilers 
when the user inquires for a specific show. Examples of show titles that may contain spoilers: "---- Season 2", 
"(show name) Season 3", "(show name): ----" (if it has a colon, it may have multiple seasons and you should call 
search.anime to make sure), "(show name) Part 2" or "(show name) Part 5"

When the user inquires about airing dates, convert from JST to CDT (don't forget to account for days shifting after 
conversion) and list the time.

INFO ABOUT TOOLS 
When using at least one of these (search_anime, search_top_anime_by_genre, search_schedule) search_anime_by_id can be 
used to get more detailed info about an anime.

Genres and themes information pulled from search_anime_by_id and search_top_anime can be combined into Genres.

search_anime: Can be paired with the search_anime_by_id function by first calling search_anime, 
finding the mal_id of a show, then calling search_anime_by_id. As this function returns the start and end date of 
airing, it can be used to find a show's release order. Note that this only gives the first page of results, you should
pass a higher page number to retrieve more results.

search_anime_by_id: When using the 'news' extension, this may return articles with "North American Anime and Manga 
Releases" which are general summaries. While these may contain information about the specific anime you're looking 
for, the user will have to read it by clicking on the URL link. Always ask the user if they'd like a link to any of 
the articles when searching news! When user asks about a specific anime, this function will also return a youtube 
link for the trailer, let the user know which shows have a trailer available, and ONLY provide it at the end of your 
response IF the user asks for it. Do NOT provide it when giving a list of anime. ONLY PROVIDE IT FOR ONE SHOW AT A TIME
DURING RESPONSES

The 'recommendations' argument can be passed alongside a specific mal_id to fetch recommendations for that anime. It 
will return the mal_id for the anime, the anime's title, and votes which determine how highly a show is being 
recommended. You will make a search_anime_by_id call for each of the top few titles, fetch the score, and synopsis, 
and list them to the user. If youtube url is available, let the user know that you have it, and offer to provide the 
trailer. ONLY PROVIDE IT FOR ONE SHOW AT A TIME

search_top_anime: When asked for 'top anime' without further specification, first retrieve and present the top 3-5 
anime by score (critical rating). In the same response, briefly offer the user the option to see anime ranked by 
popularity (A strong indicator of broad reach and engagement, but heavily favors older, established titles that have 
had more time to accumulate members, potentially overlooking newer or underrated gems) or favorites (Represents a more 
passionate, core fanbase's appreciation, often highlighting deeply beloved "classics" or shows with a strong 
emotional impact). Explain these distinctions clearly and concisely to the user to help them choose."""

jikan = Jikan()

def search_anime(query: str, media_type: str = '', pages: int = 1) -> list[dict[str, str]] or str:
    """Returns the first page of anime results with their mal_id, title, score (0-10), airing status, airing start and end
    date, and synopsis. Return type will be a list of dictionaries.

    Args: query (str): The anime to search for, requires exact or partial title. Keywords not supported.
    media_type (str): Filters by media type. Defaults to `None`. Valid media types: 'tv', 'movie', 'ova', 'special',
    'ona', 'music', 'cm', 'pv', 'tv_special' pages (int): Optional (defaults to first page) The page to search on. Use
    higher numbers to paginate through more results.
    """
    try:
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

    except Exception as e:
        print("Error during execution of search_anime: " + str(e))
        return "There was an error, please try again later. " + str(e)
    return anime_list

def search_anime_by_id(mal_id: int, extensions: str = '') -> dict[str, str] or list[dict[str, str]]:
    """When passing no extensions, returns a show's mal_id, title, genres, themes, episodes, score, age_rating,
    airing_status, airing_start_end, studio that worked on the show, an embed url for YouTube trailer, and synopsis.

    Args:
        mal_id (int): The MAL id of the anime.
        extensions (str): Filters by extensions. Defaults to ''. Available extensions: 'episodes' (returns filler
        episodes for anime), 'news' (returns url for user, article title, date, and excerpt), 'recommendations' (for
        suggesting recommended anime to the user, returns a list of other anime recommended by MAL users based on mal_id
        of the anime)
    """

    if not extensions:
        try:
            sleep(1)
            search_results = jikan.anime(mal_id).get('data')

            search_results_formatted = ({"mal_id": search_results.get('mal_id', 'None'),
                                        "title": search_results.get('title', 'None'),
                                        "genres": search_results.get('genres', 'None'),
                                        "themes": search_results.get('themes', 'None'),
                                        "episodes": search_results.get('episodes', 'None'),
                                        "episode_length": search_results.get('episode_length', 'None'),
                                        "score": search_results.get('score', 'None'),
                                        "age_rating": search_results.get('rating', 'None'),
                                        "airing_status": search_results.get('status'),
                                        "airing_start_end": search_results.get('aired', 'None').get('string', 'None'),
                                        "studios": search_results.get('studios', 'None')[0].get('name', 'None'),
                                        "embed_url": search_results.get('trailer', 'None').get('embed_url', 'None'),
                                        "synopsis": search_results.get('synopsis', 'None'),
                                        "background": search_results.get('background', 'None')})
            return search_results_formatted

        except Exception as e:
            print("Error during execution of search_anime_by_id: " + str(e))
            return ("There was an error, please try again later. ") + str(e)

    match extensions:
        case 'episodes':
            return get_anime_fillerandrecap_extension(mal_id)
        case 'news':
            return get_anime_news_extension(mal_id)
        case 'recommendations':
            return get_similar_anime_extension(mal_id)
    return None

def search_top_anime(page: int = 1, filter_type: str = "") -> list[dict[str, str]] or str:
    """When no parameters are provided, it will return the first page of top anime by score. You will receive a list
    of dictionaries containing for each anime mal_id, title, genres, themes, episodes, score, age_rating,
    airing_status, airing_start_end, ranked, popularity (descending, lower number means higher ranking),
    favorites (ascending, higher number means higher ranking/number of people who favorited), and synopsis.

    Args:
        page (int, optional): Page to search on. When not passing anything, defaults to first page. Use higher numbers
        to paginate through more results.
        filter_type (str, optional): Filter type to use. Valid options: airing, upcoming (doesn't return score, returns popularity), favorite, bypopularity.
    """

    top_anime_list = []

    try:
        search_results = jikan.top('anime', page=page, parameters={'filter': filter_type}).get('data')
        if not search_results:
            return "Not available"

        for anime in search_results:
            top_anime_list.append({"mal_id": anime.get('mal_id', 'None'),
                                   "title": anime.get('title', 'None'),
                                   "genres": anime.get('genres', 'None'),
                                   "themes": anime.get('themes', 'None'),
                                   "episodes": anime.get('episodes', 'None'),
                                   "score": anime.get('score', 'None'),
                                   "age_rating": anime.get('rating', 'None'),
                                   "airing_status": anime.get('status'),
                                   "airing_start_end": anime.get('string'),
                                   "ranked": anime.get('rank', 'None'),
                                   "popularity": anime.get('popularity', 'None'),
                                   "favorites": anime.get('favorites', 'None'),
                                   "synopsis": anime.get('synopsis', 'None')})

        return top_anime_list
    except Exception as e:
        print("Error during execution of search_top_anime: " + str(e))
        return "There was an error, please try again later. " + str(e)

def search_top_anime_by_genre(genre_id: str, page: int = 1) -> list[dict[str, str]] or str:
    """When given a genre or multiple genres, returns a list of dictionaries containing the mal_id of shows with their
    title, media type, score, and synopsis, all ordered by score and sorted from highest to lowest score. This can be
    used to find top scored anime with the given genre/genres.

    Args:
        genre_id (str): The genre id of the of the genre. When passing multiple genre ids, the ids must be
        separated with commas and no spaces e.g. "1,2,4". Valid genres: Action (1), Adventure (2), Avant Garde (5),
        Award Winning (46), Boys Love (28), Comedy (4), Drama (8), Fantasy (10), Girls Love (26), Gourmet (47), Horror (14),
        Mystery (7), Romance (22), Sci-Fi (24), Slice of Life ( 36), Sports (30), Supernatural (37), Suspense (41),
        Ecchi (9), Erotica (49), Hentai (12), Adult Cast (50), Anthropomorphic (51), CGDCT (52), Childcare (53),
        Combat Sports (54), Crossdressing (81), Delinquents (55), Detective (39), Educational (56), Gag Humor (57),
        Gore (58), Harem (35), High Stakes Game (59), Historical (13), Idols (Female) (60), Idols (Male) (61),
        Isekai (62), Iyashikei (63), Love Polygon (64), Magical Sex Shift (65), Mahou Shoujo (66), Martial Arts (17),
        Mecha (18), Medical (67), Military (38), Music (19), Mythology (6), Organized Crime (68), Otaku Culture (69),
        Parody (20), Performing Arts (70), Pets (71), Psychological (40), Racing (3), Reincarnation (72),
        Reverse Harem (73), Love Status Quo (74), Samurai (21), School (23), Showbiz (75), Space (29),
        Strategy Game (11), Super Power (31), Survival (76), Team Sports (77), Time Travel ( 78), Vampire (32),
        Video Game (79), Visual Arts (80),
        Workplace (48), Urban Fantasy (82), Villainess (83), Josei (43), Kids (15), Seinen (42), Shoujo (25), Shounen (27)

        page (int): Page to search on. Use higher numbers to paginate through more results.

    """

    try:
        search_results = jikan.search('anime', '', page=page, parameters={'genres': str(genre_id),
                                                                          'order_by': 'score', 'sort': 'desc'}).get('data')

        if not search_results:
            return "Not available"

        top_genre_list = []
        for top_anime in search_results:
            top_genre_list.append({"mal_id": top_anime.get('mal_id', 'None'),
                                   "title": top_anime.get('title', 'None'),
                                   "type": top_anime.get('type', 'None'),
                                   "score": top_anime.get('score', 'None'),
                                   "synopsis": top_anime.get('synopsis', 'None')})

        return top_genre_list
    except Exception as e:
        print(str(e))
        return "There was an error, please try again later. " + str(e)


def search_schedules(days: str = '') -> list[dict[str, str]]:
    """Lets you see what anime is airing on what day and what time for current season.
    When no parameters are provided, will return all anime airing schedule for all days for current season.
    When 'day' is provided, will return what animes are airing on that specific day.

    Args: days (str): The day of the week to search for. Defaults to '' when not provided. Available values:
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'

        Note:
            For returned unknown days, it means that anime that is planned for the current season but does not yet have
            a specific broadcast day assigned.
            For returned 'other' days, it is likely the anime has an irregular airing schedule.

    """

    try:
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

    except Exception as e:
        print(str(e))
        return "There was an error, please try again later. " + str(e)

def get_anime_fillerandrecap_extension(mal_id: int) -> list[dict[str, str]] or str:
    """Helper function (for search_anime_by_id) for getting an anime's filler info. Returns a list of dictionaries
    containing episode number, title, score, whether an episode is a filler, whether an episode is a recap.
    """

    episode_list = []
    pages = 1

    try:
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
    except Exception as e:
        print(str(e))
        return "There was an error, please try again later. " + str(e)

def get_anime_news_extension(mal_id: int) -> list[dict[str, str]] or str:
    """Helper function (for search_anime_by_id) for getting an anime's news info. Returns a list of dictionaries containing
    article title, date, url to article, and excerpt"""


    try:
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
    except Exception as e:
        print(str(e))
        return "There was an error, please try again later. " + str(e)

def get_similar_anime_extension(mal_id: int) -> list[dict[str, str]] or str:
    """Helper function (for search_anime_by_id) that takes the mal_id of an anime and returns a list of dictionaries
    containing the mal_id of the anime, title of the anime, and votes for each recommended anime"""

    similar_anime_list = []

    try:
        search_results = jikan.anime(mal_id, extension='recommendations').get('data')
        if not search_results:
            return "Not available"
        else:
            for similar_anime in search_results:
                similar_anime_list.append({"mal_id": similar_anime.get('entry').get('mal_id', 'None'),
                                           "title": similar_anime.get('entry').get('title', 'None'),
                                           "votes": similar_anime.get('votes', 'None')})

        return similar_anime_list
    except Exception as e:
        print(str(e))
        return "There was an error, please try again later. " + str(e)


tools = [search_anime, search_anime_by_id, search_schedules, search_top_anime, search_top_anime_by_genre]

#ENTER YOUR OWN GEMINI API KEY, can be found on https://aistudio.google.com/apikey
client = genai.Client(api_key="AIzaSyDg21oMu0hGCrG7lfQC2dia7Pb2Pd2tqNA")
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
    response_text = response.text
    print(f"Proxy: {response}")

    url_pattern = r"https://www.youtube.com/embed/.+"
    match = re.search(url_pattern, response.text)
    youtube_url = None
    if match:
        youtube_url = match.group(0)
        response_text = response.text.replace(youtube_url, "").strip()

    return jsonify({"reply": response_text,
                   "youtube_embed_url": youtube_url})


if __name__ == "__main__":
    flask_app.run(debug=True)

print("Goodbye.")


#------------------------------------------Ignore Everything Below This------------------------------------------------#
print(jikan.top())
#print(jikan.top('anime', page=1, parameters={}))
#print(search_top_anime())
#print(search_top_anime_by_genre('1'))
#print(jikan.search('anime', '', page=1, parameters={'genres': '1,4', 'order_by': 'score', 'sort': 'desc'}))
#print(jikan.top('anime', parameters={'filter': 'favorite'}))
#print(search_top_anime())
'''for genre in jikan.genres('anime').get('data'):
    print(f"{genre.get('name')} ({genre.get('mal_id')})", end=", ")'''
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