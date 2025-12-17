import pytest

from bot.geocoding import simplify_address, _abbreviate_province


class TestSimplifyAddress:
    def test_simplifies_long_address(self):
        """Test simplification of typical Nominatim address."""
        full = "138 Chillery Avenue, Malvern, Scarborough, Toronto, Golden Horseshoe, Ontario, M1J 2N8, Canada"
        result = simplify_address(full)

        # Should contain street and city/province
        assert "138 Chillery Avenue" in result
        # Should not contain country or postal code
        assert "Canada" not in result
        assert "M1J" not in result

    def test_keeps_street_and_city(self):
        """Test that street and city are preserved."""
        full = "123 Main Street, Downtown, Toronto, Ontario, M5V 1A1, Canada"
        result = simplify_address(full)

        assert "123 Main Street" in result
        assert "Toronto" in result or "Downtown" in result

    def test_abbreviates_province(self):
        """Test that province names are abbreviated."""
        full = "456 Test Road, Vancouver, British Columbia, V6B 1S2, Canada"
        result = simplify_address(full)

        # Should use BC instead of British Columbia
        assert "BC" in result or "British Columbia" not in result

    def test_short_address_unchanged(self):
        """Test that short addresses pass through."""
        short = "123 Main St"
        result = simplify_address(short)

        assert result == short or "123 Main St" in result

    def test_handles_missing_parts(self):
        """Test handling of addresses with missing parts."""
        partial = "Test Location, Toronto"
        result = simplify_address(partial)

        # Should not crash
        assert result is not None


class TestAbbreviateProvince:
    def test_ontario(self):
        assert _abbreviate_province("Ontario") == "ON"

    def test_british_columbia(self):
        assert _abbreviate_province("British Columbia") == "BC"

    def test_quebec(self):
        assert _abbreviate_province("Quebec") == "QC"

    def test_alberta(self):
        assert _abbreviate_province("Alberta") == "AB"

    def test_unknown_province(self):
        """Unknown provinces should pass through unchanged."""
        assert _abbreviate_province("Unknown State") == "Unknown State"

    def test_all_provinces_covered(self):
        """Test that all Canadian provinces/territories are covered."""
        provinces = [
            "Ontario", "Quebec", "British Columbia", "Alberta",
            "Manitoba", "Saskatchewan", "Nova Scotia", "New Brunswick",
            "Newfoundland and Labrador", "Prince Edward Island",
            "Northwest Territories", "Nunavut", "Yukon"
        ]

        for province in provinces:
            result = _abbreviate_province(province)
            # All should return 2-letter codes
            assert len(result) == 2
            assert result.isupper()
