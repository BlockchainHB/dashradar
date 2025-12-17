import pytest

from bot.distance import (
    haversine_distance,
    calculate_distances,
    filter_by_distance,
    sort_by_distance,
    RADIUS_OPTIONS,
    DEFAULT_RADIUS_KM
)
from bot.models import Restaurant


def make_restaurant(name: str, lat: float, lng: float) -> Restaurant:
    """Helper to create a Restaurant with minimal required fields."""
    return Restaurant(
        name=name,
        address=f"{name} Address",
        kgmid=f"/g/{name.lower().replace(' ', '')}",
        place_id=f"place_{name}",
        lat=lat,
        lng=lng
    )


class TestHaversineDistance:
    def test_same_point_is_zero(self):
        """Distance between same point should be 0."""
        distance = haversine_distance(43.65, -79.38, 43.65, -79.38)
        assert distance == 0

    def test_known_distance(self):
        """Test a known distance (Toronto to New York ~550km)."""
        # Toronto: 43.6532, -79.3832
        # New York: 40.7128, -74.0060
        distance = haversine_distance(43.6532, -79.3832, 40.7128, -74.0060)

        # Should be approximately 550km
        assert 540 < distance < 560

    def test_short_distance(self):
        """Test a short distance (~1km)."""
        # Two points about 1km apart in Toronto
        lat1, lon1 = 43.6532, -79.3832
        lat2, lon2 = 43.6622, -79.3832  # ~1km north

        distance = haversine_distance(lat1, lon1, lat2, lon2)
        assert 0.9 < distance < 1.1

    def test_symmetric(self):
        """Distance should be same in both directions."""
        d1 = haversine_distance(43.65, -79.38, 40.71, -74.00)
        d2 = haversine_distance(40.71, -74.00, 43.65, -79.38)
        assert abs(d1 - d2) < 0.001


class TestCalculateDistances:
    def test_populates_distance_km(self):
        """Test that distance_km is populated for all restaurants."""
        restaurants = [
            make_restaurant("Near", 43.6532, -79.3832),
            make_restaurant("Far", 43.7, -79.4)
        ]

        # User location
        user_lat, user_lng = 43.6532, -79.3832

        result = calculate_distances(restaurants, user_lat, user_lng)

        assert all(r.distance_km is not None for r in result)
        assert result[0].distance_km == 0  # Same location
        assert result[1].distance_km > 0   # Different location

    def test_distance_rounded(self):
        """Test that distances are rounded to 2 decimal places."""
        restaurants = [make_restaurant("Test", 43.7, -79.4)]

        result = calculate_distances(restaurants, 43.6532, -79.3832)

        # Check it's rounded to 2 decimals
        distance_str = str(result[0].distance_km)
        if "." in distance_str:
            decimals = len(distance_str.split(".")[1])
            assert decimals <= 2


class TestFilterByDistance:
    def test_filters_within_radius(self):
        """Test that only restaurants within radius are returned."""
        restaurants = [
            make_restaurant("Near", 43.654, -79.38),    # ~0.1km
            make_restaurant("Medium", 43.68, -79.38),  # ~3km
            make_restaurant("Far", 43.75, -79.38),     # ~10km
        ]

        user_lat, user_lng = 43.6532, -79.3832

        # Filter to 5km
        result = filter_by_distance(restaurants, user_lat, user_lng, 5.0)

        assert len(result) == 2  # Near and Medium
        assert all(r.distance_km <= 5.0 for r in result)

    def test_sorted_by_distance(self):
        """Test that results are sorted by distance."""
        restaurants = [
            make_restaurant("Far", 43.7, -79.4),
            make_restaurant("Near", 43.655, -79.385),
            make_restaurant("Medium", 43.67, -79.39),
        ]

        user_lat, user_lng = 43.6532, -79.3832

        result = filter_by_distance(restaurants, user_lat, user_lng, 10.0)

        # Should be sorted closest first
        distances = [r.distance_km for r in result]
        assert distances == sorted(distances)

    def test_empty_when_none_in_radius(self):
        """Test that empty list returned when no restaurants in radius."""
        restaurants = [
            make_restaurant("Far", 44.0, -79.0),  # Very far
        ]

        user_lat, user_lng = 43.6532, -79.3832

        result = filter_by_distance(restaurants, user_lat, user_lng, 1.0)
        assert result == []

    def test_distance_populated(self):
        """Test that distance_km is populated on filtered results."""
        restaurants = [make_restaurant("Test", 43.66, -79.39)]

        result = filter_by_distance(restaurants, 43.6532, -79.3832, 5.0)

        assert len(result) == 1
        assert result[0].distance_km is not None


class TestSortByDistance:
    def test_sorts_by_distance(self):
        """Test sorting by distance_km."""
        restaurants = [
            make_restaurant("A", 0, 0),
            make_restaurant("B", 0, 0),
            make_restaurant("C", 0, 0),
        ]

        restaurants[0].distance_km = 5.0
        restaurants[1].distance_km = 1.0
        restaurants[2].distance_km = 3.0

        result = sort_by_distance(restaurants)

        assert [r.distance_km for r in result] == [1.0, 3.0, 5.0]

    def test_none_distances_at_end(self):
        """Test that restaurants without distance go to end."""
        restaurants = [
            make_restaurant("A", 0, 0),
            make_restaurant("B", 0, 0),
        ]

        restaurants[0].distance_km = None
        restaurants[1].distance_km = 5.0

        result = sort_by_distance(restaurants)

        assert result[0].distance_km == 5.0
        assert result[1].distance_km is None


class TestConstants:
    def test_radius_options(self):
        """Test radius options are defined correctly."""
        assert "1km" in RADIUS_OPTIONS
        assert "3km" in RADIUS_OPTIONS
        assert "5km" in RADIUS_OPTIONS
        assert "10km" in RADIUS_OPTIONS

        assert RADIUS_OPTIONS["1km"] == 1.0
        assert RADIUS_OPTIONS["5km"] == 5.0

    def test_default_radius(self):
        """Test default radius is reasonable."""
        assert DEFAULT_RADIUS_KM == 5.0
