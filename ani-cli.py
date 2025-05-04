#!/usr/bin/env -S uv run
# /// script
# requires-python=">3.9"
# dependencies = [
#   "requests",
#   "tabulate",
# ]
# ///


import requests
import tabulate
import sys
import json

def search_anime(query, mode, allanime_api):
    search_gql = """
    query($search: SearchInput, $limit: Int, $page: Int, $translationType: VaildTranslationTypeEnumType, $countryOrigin: VaildCountryOriginEnumType) {
        shows(search: $search, limit: $limit, page: $page, translationType: $translationType, countryOrigin: $countryOrigin) {
            edges {
                _id
                name
                availableEpisodes
                __typename
            }
        }
    }
    """

    variables = {
        "search": {
            "allowAdult": False,
            "allowUnknown": False,
            "query": query
        },
        "limit": 40,
        "page": 1,
        "translationType": mode,
        "countryOrigin": "ALL"
    }

    params = {
        "variables": json.dumps(variables),
        "query": search_gql
    }

    response = requests.get(f"{allanime_api}/api", headers=headers, params=params)
    data = response.json()

    results = []
    for edge in data['data']['shows']['edges']:
        _id = edge['_id']
        name = edge['name']
        available_episodes = edge['availableEpisodes']
        results.append((_id, name, available_episodes, f"{_id}\t{name} ({available_episodes} episodes)"))

    return results

# def time_until_next_ep(query):
#     animeschedule = "https://animeschedule.net"

#     # Search for the anime
#     search_response = requests.get(f"https://animeschedule.net/api/v3/anime", params={"q": query})
#     search_data = search_response.json()

#     for anime in search_data:
#         anime_route = anime.get("route")
#         if anime_route:
#             # Fetch the anime details page
#             anime_response = requests.get(f"{animeschedule}/anime/{anime_route}")

#             # Print the extracted data
#             for key, value in data.items():
#                 print(f"{key}: {value}")

#             # Determine the status
#             status = "Ongoing"
#             color = "33"
#             if "Next Raw Release" not in data:
#                 status = "Finished"
#                 color = "32"

#             print(f"Status:  \033[1;{color}m{status}\033[0m\n---\n")

def get_episodes_list(show_id, mode, allanime_api):
    episodes_list_gql = """
    query ($showId: String!) {
        show(_id: $showId) {
            _id
            availableEpisodesDetail
        }
    }
    """

    variables = {
        "showId": show_id
    }

    params = {
        "variables": json.dumps(variables),
        "query": episodes_list_gql
    }

    response = requests.get(f"{allanime_api}/api", headers=headers, params=params)
    data = response.json()

    episodes = data['data']['show']['availableEpisodesDetail'].get(mode, [])
    episodes.sort(key=lambda x: float(x))  # Sort episodes numerically

    return episodes

def get_episode_url(show_id, mode, episode_string, allanime_api):
    episode_embed_gql = """
    query ($showId: String!, $translationType: VaildTranslationTypeEnumType!, $episodeString: String!) {
        episode(showId: $showId, translationType: $translationType, episodeString: $episodeString) {
            episodeString
            sourceUrls
        }
    }
    """

    variables = {
        "showId": show_id,
        "translationType": mode,
        "episodeString": episode_string
    }

    params = {
        "variables": json.dumps(variables),
        "query": episode_embed_gql
    }

    response = requests.get(f"{allanime_api}/api", headers=headers, params=params)
    data = response.json()

    source_urls = data['data']['episode']['sourceUrls']
    return source_urls


def word_wrap(text, width=30):
    """Wrap text to a specified width."""
    if text is None:
        return ""
    wrapped_text = []
    for line in text.split('\n'):
        while len(line) > width:
            # Find the last space within the width limit
            space_index = line.rfind(' ', 0, width)
            if space_index == -1:
                space_index = width
            wrapped_text.append(line[:space_index].strip())
            line = line[space_index:].strip()
        wrapped_text.append(line.strip())
    return '\n'.join(wrapped_text)


def search_anime_by_season(season, year, format=None):
    # Define the GraphQL query to fetch anime by season and year
    query = '''
    query ($season: MediaSeason, $year: Int, $format: MediaFormat) {
    Page(page: 1, perPage: 100) {
        media(season: $season, seasonYear: $year, type: ANIME, format: $format) {
        id
        title {
            romaji
            english
        }
        season
        seasonYear
        format
        episodes
        duration
        status
        genres
        averageScore
        popularity
        siteUrl
        }
    }
    }
    '''

    # Define the variables for the query
    variables = {
        'season': season,
        'year': int(year),
        **({"format": format} if format is not None else {}),
    }

    # Define the request URL
    url = 'https://graphql.anilist.co'

    # Make the request to the AniList API
    response = requests.post(url, json={'query': query, 'variables': variables}, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })

    data = [(
            word_wrap(row['title']['english']),
            word_wrap(row['title']['romaji']),
            row['format'],
            ','.join(row['genres']),
        ) for row in response.json()['data']['Page']['media']]
    table = tabulate.tabulate(
        data, 
        headers=["English", "Romanji", "Format", "Genres"], 
        tablefmt="grid"
    )
    print(table)

allanime_refr="https://allmanga.to"
allanime_api = "https://api.allanime.day"
agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
if __name__ == "__main__":
    query = sys.argv[1]
    if query in ('SPRING', "SUMMER", "WINTER", "FALL"):
        search_anime_by_season(*sys.argv[1:])
    else:
        mode = "sub"
        headers = {
                "User-Agent": agent,
                "Referer": allanime_refr
            }

        anime_results = search_anime(query, mode, allanime_api)
        for result in anime_results:
            print(result[-1])
            episodes = get_episodes_list(result[0], mode, allanime_api)
            for episode in episodes:
                for urls in get_episode_url(result[0], mode, episode, allanime_api):
                    print("   ", episode, urls['sourceUrl'])
                    if 'downloads' in urls:
                        print("  D", episode, urls['downloads']['downloadUrl'])
