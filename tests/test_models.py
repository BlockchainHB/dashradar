import pytest
from bot.models import Restaurant, DeliveryProvider


class TestDeliveryProvider:
    def test_create_delivery_provider(self):
        provider = DeliveryProvider(
            name="DoorDash",
            url="https://www.doordash.com/store/test-123"
        )
        assert provider.name == "DoorDash"
        assert provider.url == "https://www.doordash.com/store/test-123"


class TestRestaurant:
    def test_create_restaurant_minimal(self):
        restaurant = Restaurant(
            name="Test Restaurant",
            address="123 Test St",
            kgmid="/g/11abc123",
            place_id="ChIJ123",
            lat=43.6532,
            lng=-79.3832
        )
        assert restaurant.name == "Test Restaurant"
        assert restaurant.address == "123 Test St"
        assert restaurant.kgmid == "/g/11abc123"
        assert restaurant.doordash_url is None
        assert restaurant.delivery_providers == []

    def test_create_restaurant_full(self):
        provider = DeliveryProvider(name="DoorDash", url="https://doordash.com/store/test")
        restaurant = Restaurant(
            name="Full Restaurant",
            address="456 Full St",
            kgmid="/g/11xyz789",
            place_id="ChIJ456",
            phone="(416) 555-1234",
            website="https://example.com",
            rating=4.5,
            lat=43.6532,
            lng=-79.3832,
            doordash_url="https://doordash.com/store/test",
            delivery_providers=[provider],
            distance_km=1.5
        )
        assert restaurant.phone == "(416) 555-1234"
        assert restaurant.website == "https://example.com"
        assert restaurant.rating == 4.5
        assert restaurant.doordash_url == "https://doordash.com/store/test"
        assert len(restaurant.delivery_providers) == 1
        assert restaurant.distance_km == 1.5

    def test_distance_km_optional(self):
        """Test that distance_km defaults to None."""
        restaurant = Restaurant(
            name="Test",
            address="123 Test St",
            kgmid="/g/test",
            place_id="test",
            lat=0,
            lng=0
        )
        assert restaurant.distance_km is None
