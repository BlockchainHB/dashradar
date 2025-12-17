from math import radians, sin, cos, sqrt, atan2
from typing import List

from bot.models import Restaurant


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Uses the Haversine formula to calculate the shortest distance over
    the earth's surface.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def calculate_distances(
    restaurants: List[Restaurant],
    user_lat: float,
    user_lng: float
) -> List[Restaurant]:
    """
    Calculate distance from user to each restaurant.

    Args:
        restaurants: List of Restaurant objects
        user_lat: User's latitude
        user_lng: User's longitude

    Returns:
        Same list with distance_km field populated
    """
    for restaurant in restaurants:
        distance = haversine_distance(
            user_lat, user_lng,
            restaurant.lat, restaurant.lng
        )
        restaurant.distance_km = round(distance, 2)

    return restaurants


def filter_by_distance(
    restaurants: List[Restaurant],
    user_lat: float,
    user_lng: float,
    max_distance_km: float
) -> List[Restaurant]:
    """
    Filter restaurants within a radius and sort by distance.

    Args:
        restaurants: List of Restaurant objects
        user_lat: User's latitude
        user_lng: User's longitude
        max_distance_km: Maximum distance in kilometers

    Returns:
        Filtered and sorted list of restaurants within radius
    """
    results = []

    for restaurant in restaurants:
        distance = haversine_distance(
            user_lat, user_lng,
            restaurant.lat, restaurant.lng
        )

        if distance <= max_distance_km:
            restaurant.distance_km = round(distance, 2)
            results.append(restaurant)

    # Sort by distance (closest first)
    return sorted(results, key=lambda r: r.distance_km)


def sort_by_distance(restaurants: List[Restaurant]) -> List[Restaurant]:
    """
    Sort restaurants by distance (must have distance_km set).

    Args:
        restaurants: List of Restaurant objects with distance_km populated

    Returns:
        Sorted list (closest first)
    """
    return sorted(
        restaurants,
        key=lambda r: r.distance_km if r.distance_km is not None else float('inf')
    )


# Common radius options in km
RADIUS_OPTIONS = {
    "1km": 1.0,
    "3km": 3.0,
    "5km": 5.0,
    "10km": 10.0,
}

DEFAULT_RADIUS_KM = 5.0
