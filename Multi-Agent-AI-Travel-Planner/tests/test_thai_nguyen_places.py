import unittest
from unittest.mock import patch

from src.tools import places


class ThaiNguyenSourceOnlyTests(unittest.TestCase):
    def test_recommendations_use_only_mythainguyen_without_any_llm(self):
        source_place = {
            "name": "Đền Đuổm",
            "address": "Xã Động Đạt, huyện Phú Lương, Thái Nguyên",
            "introduction": "Đền Đuổm là di tích lịch sử tại huyện Phú Lương, tỉnh Thái Nguyên.",
            "category_source": "Di tích lịch sử",
            "latitude": 21.7,
            "longitude": 105.7,
            "url": "https://mythainguyen.vn/vi/denduom",
            "retrieved_at": "2026-10-01T00:00:00Z",
        }
        with patch.object(places, "fetch_mythainguyen_places", return_value=[source_place]) as mytn, \
             patch.object(places, "fetch_notable_places_wikipedia") as wikipedia, \
             patch.object(places, "get_llm") as llm:
            result = places.search_places_osm("Thái Nguyên", interests=["Heritage & Architecture"])

        mytn.assert_called_once()
        wikipedia.assert_not_called()
        llm.assert_not_called()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Đền Đuổm")
        self.assertEqual(result[0]["sources"][0]["name"], "My Thái Nguyên")
        self.assertEqual(result[0]["latitude"], 21.7)


if __name__ == "__main__":
    unittest.main()
