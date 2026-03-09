"""TMDB API tools for movie/TV search and details."""

import httpx
from langchain_core.tools import tool

TMDB_BASE = "https://api.themoviedb.org/3"


def _client(api_key: str, language: str = "zh-CN") -> httpx.Client:
    return httpx.Client(
        base_url=TMDB_BASE,
        params={"api_key": api_key, "language": language},
        timeout=10.0,
    )


def search_movie(api_key: str, query: str, language: str = "zh-CN") -> list[dict]:
    """Search movies by query. Returns list of {id, title, release_date, overview}."""
    with _client(api_key, language) as c:
        r = c.get("/search/movie", params={"query": query})
        r.raise_for_status()
        data = r.json()
    results = data.get("results", [])
    return [
        {
            "id": x["id"],
            "title": x.get("title", ""),
            "release_date": x.get("release_date", "")[:4] if x.get("release_date") else None,
            "overview": x.get("overview", ""),
        }
        for x in results[:10]
    ]


def search_tv(api_key: str, query: str, language: str = "zh-CN") -> list[dict]:
    """Search TV shows by query. Returns list of {id, name, first_air_date, overview}."""
    with _client(api_key, language) as c:
        r = c.get("/search/tv", params={"query": query})
        r.raise_for_status()
        data = r.json()
    results = data.get("results", [])
    return [
        {
            "id": x["id"],
            "title": x.get("name", ""),
            "first_air_date": x.get("first_air_date", "")[:4] if x.get("first_air_date") else None,
            "overview": x.get("overview", ""),
        }
        for x in results[:10]
    ]


def get_movie_detail(api_key: str, movie_id: int, language: str = "zh-CN") -> dict | None:
    """Get movie details by TMDB ID."""
    with _client(api_key, language) as c:
        r = c.get(f"/movie/{movie_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


def get_tv_detail(api_key: str, tv_id: int, language: str = "zh-CN") -> dict | None:
    """Get TV show details by TMDB ID."""
    with _client(api_key, language) as c:
        r = c.get(f"/tv/{tv_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


def search_multi(api_key: str, query: str, language: str = "zh-CN") -> list[dict]:
    """Search movies and TV in one request."""
    with _client(api_key, language) as c:
        r = c.get("/search/multi", params={"query": query})
        r.raise_for_status()
        data = r.json()
    results = data.get("results", [])
    out = []
    for x in results[:10]:
        kind = x.get("media_type", "")
        if kind == "movie":
            out.append({
                "media_type": "movie",
                "id": x["id"],
                "title": x.get("title", ""),
                "release_date": x.get("release_date", "")[:4] if x.get("release_date") else None,
                "overview": x.get("overview", ""),
            })
        elif kind == "tv":
            out.append({
                "media_type": "tv",
                "id": x["id"],
                "title": x.get("name", ""),
                "first_air_date": x.get("first_air_date", "")[:4] if x.get("first_air_date") else None,
                "overview": x.get("overview", ""),
            })
    return out


def make_tmdb_tools(api_key: str, language: str = "zh-CN") -> list:
    """Create LangChain tools for LLM, bound with api_key."""

    @tool
    def search_movies(query: str) -> str:
        """Search movies on TMDB by title or keyword. Use for identifying movie titles."""
        results = search_movie(api_key, query, language)
        import json
        return json.dumps(results, ensure_ascii=False)

    @tool
    def search_tv_shows(query: str) -> str:
        """Search TV shows on TMDB by title or keyword. Use for identifying TV titles."""
        results = search_tv(api_key, query, language)
        import json
        return json.dumps(results, ensure_ascii=False)

    @tool
    def get_movie_details(movie_id: int) -> str:
        """Get movie details by TMDB movie ID. Use after search_movies to confirm."""
        detail = get_movie_detail(api_key, movie_id, language)
        import json
        return json.dumps(detail, ensure_ascii=False) if detail else "{}"

    @tool
    def get_tv_details(tv_id: int) -> str:
        """Get TV show details by TMDB TV ID. Use after search_tv_shows to confirm."""
        detail = get_tv_detail(api_key, tv_id, language)
        import json
        return json.dumps(detail, ensure_ascii=False) if detail else "{}"

    return [search_movies, search_tv_shows, get_movie_details, get_tv_details]
