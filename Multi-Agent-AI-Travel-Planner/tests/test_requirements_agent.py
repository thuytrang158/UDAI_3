import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from src import api
from src.tools import places, requirements


class RequirementsExtractionTests(unittest.TestCase):
    def extract(self, responses, context=None):
        model = Mock()
        model.invoke.side_effect = [SimpleNamespace(content=value) for value in responses]
        with patch.object(requirements, "get_llm", return_value=model):
            result = requirements.extract_trip_requirements("Đi hai ngày, thích công viên", context=context)
        return result, model

    def test_extraction_validates_json_and_supplies_existing_form_context(self):
        data = {"number_of_days": 2, "destination": None, "interests": ["Parks & Leisure"]}
        result, model = self.extract(["<think>reasoning</think>```json\n" + json.dumps(data) + "\n```"],
                                     context={"destination": "Bengaluru"})
        self.assertEqual(result, {"number_of_days": 2, "interests": ["Parks & Leisure"]})
        self.assertIn("Bengaluru", model.invoke.call_args.args[0][1].content)

    def test_invalid_response_is_repaired_once(self):
        result, model = self.extract(['{"number_of_days": 0}', '{"number_of_days": 2}'])
        self.assertEqual(result["number_of_days"], 2)
        self.assertEqual(model.invoke.call_count, 2)

    def test_invalid_json_never_silently_uses_form_defaults(self):
        with self.assertRaises(requirements.RequirementsOutputError):
            self.extract(["not json", '{"interests": ["invented category"]}'])

    def test_null_strings_cannot_become_a_destination(self):
        result, _ = self.extract(['{"destination": "null", "number_of_days": 2}'])
        self.assertNotIn("destination", result)


class RequirementsApiTests(unittest.TestCase):
    def test_ai_interests_and_days_reach_discovery_without_losing_form_fields(self):
        request = api.RequirementsRequest(destination="Bengaluru", request_text="Hai ngày, thích công viên",
                                          interests=["Heritage & Architecture"])
        with patch.object(api, "extract_trip_requirements", return_value={
            "number_of_days": 2, "interests": ["Parks & Leisure"]
        }) as extractor, patch.object(api, "search_places_osm", return_value=[{"id": "park"}]) as discovery:
            result = api.initiate_trip(request)
        self.assertEqual(result["number_of_days"], 2)
        self.assertEqual(result["destination"], "Bengaluru")
        self.assertEqual(result["number_of_travelers"], 2)
        self.assertEqual(result["requirements_agent"]["status"], "completed")
        self.assertEqual(discovery.call_args.kwargs["interests"], ["Heritage & Architecture", "Parks & Leisure"])
        self.assertEqual(extractor.call_args.kwargs["context"]["destination"], "Bengaluru")

    def test_model_unavailable_stops_before_discovery_with_explicit_503(self):
        with patch.object(api, "extract_trip_requirements", side_effect=ConnectionError), \
             patch.object(api, "search_places_osm") as discovery:
            with self.assertRaises(HTTPException) as raised:
                api.initiate_trip(api.RequirementsRequest(request_text="Đi hai ngày"))
        self.assertEqual(raised.exception.status_code, 503)
        discovery.assert_not_called()

    def test_invalid_model_output_reports_422(self):
        with patch.object(api, "extract_trip_requirements", side_effect=requirements.RequirementsOutputError), \
             patch.object(api, "search_places_osm") as discovery:
            with self.assertRaises(HTTPException) as raised:
                api.initiate_trip(api.RequirementsRequest(request_text="Đi hai ngày"))
        self.assertEqual(raised.exception.status_code, 422)
        discovery.assert_not_called()

    def test_empty_discovery_is_distinct_from_model_failure(self):
        with patch.object(api, "extract_trip_requirements", return_value={"number_of_days": 2}), \
             patch.object(api, "search_places_osm", return_value=[]), \
             patch.object(api, "get_places_notice", return_value="Nguồn tạm thời không truy cập được"):
            result = api.initiate_trip(api.RequirementsRequest(request_text="Đi hai ngày"))
        self.assertEqual(result["requirements_agent"]["status"], "completed")
        self.assertEqual(result["status"], "NO_PLACES_FOUND")


class DestinationScopeTests(unittest.TestCase):
    def test_country_qualifier_and_bangalore_alias_keep_local_attractions(self):
        place = {"name": "Bangalore Palace", "introduction": "A palace in Bangalore, Karnataka."}
        for destination in ["Bengaluru, India", "Bengaluru (Bangalore), India", "Bengaluru City"]:
            with self.subTest(destination=destination):
                self.assertTrue(places._in_scope(place, destination))
        self.assertFalse(places._in_scope(place, "Mumbai, India"))

    def test_source_outage_has_a_source_specific_message(self):
        with patch.object(places, "_wiki_search", side_effect=TimeoutError):
            self.assertEqual(places.fetch_notable_places_wikipedia("Bengaluru"), [])
        self.assertIn("Wikipedia", places.get_places_notice())


if __name__ == "__main__":
    unittest.main()
