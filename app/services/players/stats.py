from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.base import TransfermarktBase

TMAPI_BASE = "https://tmapi-alpha.transfermarkt.technology"

# Statistics categories aggregated per game (matches Xc logic in player-performance-proxy bundle)
STAT_CATEGORIES = ["playingTimeStatistics", "cardStatistics", "goalStatistics", "generalStatistics"]

# Keys skipped during aggregation (age fields are not summed)
SKIP_KEYS = {"age", "ageDiscrepancyDays"}

# Keys treated as occurrence counters (value becomes the bucket, count incremented)
COUNTER_KEYS = {"absenceId", "injuryId", "participationState", "positionId", "shirtNumber"}


@dataclass
class TransfermarktPlayerStats(TransfermarktBase):
    """
    A class for retrieving and parsing player stats from Transfermarkt.

    Fetches per-game data from /ceapi/performance-game/{player_id} and
    aggregates it by season/competition/club.

    Args:
        player_id (str): The unique identifier of the player.
        URL (str): The ceapi endpoint for the player's performance data.
    """

    player_id: str = None
    URL: str = "https://www.transfermarkt.com/ceapi/performance-game/{player_id}"

    def __post_init__(self) -> None:
        """Fetch and validate raw performance data from the ceapi endpoint."""
        self.URL = self.URL.format(player_id=self.player_id)
        response = self.make_request(self.URL)
        self._ceapi_data = response.json()["data"]

    def __fetch_competition_meta(self, competition_id: str) -> dict:
        """Fetch competition metadata (name, thumbnail) from tmapi."""
        try:
            r = self.make_request(f"{TMAPI_BASE}/competition/{competition_id}", bypass_scraper=True)
            return r.json().get("data") or {}
        except Exception:
            return {}

    def __fetch_club_meta(self, club_id: str) -> dict:
        """Fetch club metadata (name) from tmapi."""
        try:
            r = self.make_request(f"{TMAPI_BASE}/club/{club_id}", bypass_scraper=True)
            return r.json().get("data") or {}
        except Exception:
            return {}

    def __aggregate_games(self, games: list) -> dict:
        """
        Group games by (seasonId, competitionId, clubId) and aggregate statistics.

        Replicates the Xc/Yc aggregation logic from the player-performance-proxy
        Svelte bundle on the Transfermarkt frontend.
        """
        groups: dict = {}

        for game in games:
            game_info = game["gameInformation"]
            clubs_info = game["clubsInformation"]
            stats = game["statistics"]

            season_id = game_info["season"]["id"]
            competition_id = game_info["competitionId"]
            club_id = str(clubs_info["club"]["clubId"])
            group_key = f"{season_id}-{competition_id}-{club_id}"

            if group_key not in groups:
                groups[group_key] = {
                    "seasonId": str(season_id),
                    "competitionId": competition_id,
                    "clubId": club_id,
                }

            row = groups[group_key]

            for cat in STAT_CATEGORIES:
                cat_stats = stats.get(cat) or {}
                for stat_key, value in cat_stats.items():
                    if stat_key in SKIP_KEYS:
                        continue
                    if stat_key in COUNTER_KEYS:
                        # Bucket-count: participationState="played" → {"played": N}
                        if not value:
                            continue
                        row.setdefault(stat_key, {})
                        row[stat_key][str(value)] = row[stat_key].get(str(value), 0) + 1
                    elif isinstance(value, dict) and value:
                        # Object events (e.g. yellowCard, redCard): count occurrences
                        row[stat_key] = row.get(stat_key, 0) + 1
                    else:
                        # Numeric fields: sum values
                        row[stat_key] = row.get(stat_key, 0) + (value or 0)

        return groups

    def __parse_player_stats(self) -> list:
        """
        Parse player statistics from the cached ceapi data.

        Returns:
            list: Each item represents stats for one season/competition/club combination.
        """
        games = self._ceapi_data.get("performance") or []
        competition_ids = self._ceapi_data.get("competitionIds") or []
        club_ids = self._ceapi_data.get("clubIds") or []

        # Fetch competition and club metadata concurrently
        comp_meta: dict = {}
        club_meta: dict = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            comp_futures = {
                executor.submit(self.__fetch_competition_meta, cid): cid
                for cid in competition_ids
            }
            club_futures = {
                executor.submit(self.__fetch_club_meta, cid): cid
                for cid in club_ids
            }
            for future in as_completed(comp_futures):
                comp_meta[comp_futures[future]] = future.result()
            for future in as_completed(club_futures):
                club_meta[club_futures[future]] = future.result()

        groups = self.__aggregate_games(games)

        result = []
        for row in groups.values():
            comp = comp_meta.get(row["competitionId"]) or {}
            club = club_meta.get(row["clubId"]) or {}

            images = (comp.get("historical") or {}).get("images") or []
            thumbnail = images[0]["url"] if images else ""

            participation = row.get("participationState") or {}

            result.append({
                "competitionId": row["competitionId"],
                "competitionThumbnail": thumbnail,
                "clubId": row["clubId"],
                "clubName": club.get("name", ""),
                "seasonId": row["seasonId"],
                "competitionName": comp.get("name", ""),
                "appearances": participation.get("played", 0),
                "goals": row.get("goalsScoredTotal") or 0,
                "assists": row.get("assists") or 0,
                "yellowCards": row.get("yellowCard") or 0,
                "secondYellowCards": row.get("yellowRedCard") or 0,
                "redCards": row.get("redCard") or 0,
                "minutesPlayed": row.get("playedMinutes") or 0,
            })

        return result

    def get_player_stats(self) -> dict:
        """
        Retrieve and parse player statistics from Transfermarkt.

        Returns:
            dict: Player id, stats list, and last-updated timestamp.
        """
        self.response["id"] = self.player_id
        self.response["stats"] = self.__parse_player_stats()
        return self.response
