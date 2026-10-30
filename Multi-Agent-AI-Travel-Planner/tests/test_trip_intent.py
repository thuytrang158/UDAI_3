import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from src import api
from src.tools import intent, mythainguyen, accommodation


class GroundedIntentTests(unittest.TestCase):
    def setUp(self):
        self.atk = {"id": "atk", "name": "Khu di tích lịch sử Quốc gia đặc biệt ATK Định Hóa",
                    "category": "Heritage & Architecture", "introduction": "Khu di tích tại Phú Đình.",
                    "latitude": 21.78, "longitude": 105.51, "description": "Khu di tích.",
                    "sources": [{"name": "My Thái Nguyên", "url": "https://mythainguyen.vn/vi/atkthainguyen"}]}
        self.other = {"id": "other", "name": "ATK Chợ Đồn", "category": "Heritage & Architecture",
                      "description": "Di tích khác.", "latitude": 22.16, "longitude": 105.60}
        self.requirements = {"required_places": ["ATK Định Hóa"], "excluded_places": [],
                             "preferences": [], "pace": "relaxed", "interests": ["Parks & Leisure"]}

    def test_required_place_survives_score_category_and_display_limit(self):
        model = Mock()
        model.invoke.return_value = SimpleNamespace(content=json.dumps({"places": [
            {"id": "atk", "score": 0, "reason": "Đúng điểm bạn yêu cầu", "required_for": []},
            {"id": "other", "score": 100, "reason": "Một di tích khác", "required_for": []},
            {"id": "invented", "score": 100, "required_for": ["ATK Định Hóa"]},
        ]}))
        with patch.object(intent, "get_llm", return_value=model):
            selected = intent.rank_for_intent([self.other, self.atk], self.requirements, limit=1)
        self.assertEqual([p["id"] for p in selected], ["atk"])
        self.assertEqual(selected[0]["required_for"], ["ATK Định Hóa"])
        self.assertEqual(selected[0]["sources"], self.atk["sources"])
        self.assertEqual(intent.requirement_report(selected, self.requirements)[0]["status"], "matched")

    def test_missing_required_place_is_reported_not_fabricated(self):
        report = intent.requirement_report([self.other], self.requirements)
        self.assertEqual(report[0]["status"], "missing")
        with self.assertRaises(ValueError):
            intent.validate_selection([self.other], self.requirements)

    def test_irrelevant_candidates_do_not_pad_the_recommendations(self):
        model = Mock()
        model.invoke.return_value = SimpleNamespace(content=json.dumps({"places": [
            {"id": "atk", "score": 100, "reason": "Điểm bắt buộc"},
            {"id": "other", "score": 20, "reason": "Ít liên quan", "suitable": False},
        ]}))
        with patch.object(intent, "get_llm", return_value=model):
            selected = intent.rank_for_intent([self.atk, self.other], self.requirements, limit=10)
        self.assertEqual([p["id"] for p in selected], ["atk"])

    def test_same_district_or_model_claim_cannot_substitute_named_venue(self):
        nearby = {"id": "nearby", "name": "Chùa Hang (Định Hóa)", "required_for": ["ATK Định Hóa"]}
        self.assertEqual(intent.required_for(nearby, self.requirements), [])
        self.assertEqual(intent.requirement_report([nearby], self.requirements)[0]["status"], "missing")
        self.assertTrue(intent.matches_place("ATK Định Hóa", {"name": "Khu di tích An toàn khu Định Hóa"}))

    def test_exclusions_override_soft_recommendations(self):
        requirements = {"excluded_places": ["ATK Chợ Đồn"]}
        with patch.object(intent, "get_llm") as model:
            self.assertEqual(intent.rank_for_intent([self.other], requirements, 10), [])
        model.assert_not_called()

    def test_detail_budget_prioritizes_named_place_and_keeps_catalog_evidence(self):
        rows = [{"name": "Một địa điểm khác", "address": "Thái Nguyên", "url": "https://mythainguyen.vn/vi/other", "snippet": "Nguồn danh mục"},
                {"name": self.atk["name"], "address": "Phú Đình", "url": "https://mythainguyen.vn/vi/atkthainguyen", "snippet": "Khu di tích"}]
        with patch.object(mythainguyen, "fetch_catalog", return_value=rows), \
             patch.object(mythainguyen, "cached_fetch", return_value="source") as fetch, \
             patch.object(mythainguyen, "parse_detail", side_effect=lambda html, url, row: dict(row)):
            result = mythainguyen.fetch_mythainguyen_places(max_details=1, requested_names=["ATK Định Hóa"])
        self.assertEqual(fetch.call_args_list[0].args[0], "https://mythainguyen.vn/vi/atkthainguyen")
        self.assertEqual(len(result), 2)

    def test_generate_and_modify_cannot_lose_required_place(self):
        with self.assertRaises(HTTPException) as missing:
            api.generate_itinerary(api.GenerateItineraryRequest(destination="Thái Nguyên", number_of_days=3,
                transportation_preference="Cab", selected_places=[self.other], trip_requirements=self.requirements))
        self.assertEqual(missing.exception.status_code, 409)
        with patch.object(api, "modify_selection_with_llm", return_value=[self.other]):
            with self.assertRaises(HTTPException):
                api.modify_itinerary(api.ModifyItineraryRequest(feedback="bỏ điểm đầu", available_places=[self.atk, self.other],
                    selected_places=[self.atk], trip_requirements=self.requirements))

    def test_stay_and_final_report_receive_same_intent_and_required_place(self):
        with patch.object(api, "retry_missing_coordinates", side_effect=lambda p, d: p):
            generated = api.generate_itinerary(api.GenerateItineraryRequest(destination="Thái Nguyên", number_of_days=3,
                transportation_preference="Cab", selected_places=[self.atk], trip_requirements=self.requirements))
        with patch.object(api, "search_accommodations", return_value=[]) as search:
            api.get_stays(api.SearchStaysRequest(destination="Thái Nguyên", selected_places=[self.atk], trip_requirements=self.requirements))
        context = search.call_args.kwargs["trip_context"]
        self.assertEqual(context["requirements"]["required_places"], ["ATK Định Hóa"])
        self.assertEqual(context["selected_places"][0]["name"], self.atk["name"])
        finalized = api.finalize_trip(api.FinalizeTripRequest(destination="Thái Nguyên", number_of_days=3, number_of_travelers=2,
            transportation_preference="Cab", itinerary=generated["itinerary"], selected_accommodation={"price_per_night": 1000000},
            selected_places=[self.atk], routes=[], trip_requirements=self.requirements))
        self.assertEqual(finalized["requirement_report"][0]["status"], "matched")

    def test_finalize_rejects_required_place_missing_from_actual_schedule(self):
        schedule = {"days": [{"day_number": 1, "schedule": [{"time": "09:00", "activity": "Khởi hành", "details": "..."}]}]}
        with self.assertRaises(HTTPException):
            api.finalize_trip(api.FinalizeTripRequest(destination="Thái Nguyên", number_of_days=1, number_of_travelers=2,
                transportation_preference="Cab", itinerary=schedule, selected_accommodation={"price_per_night": 1000000},
                selected_places=[self.atk], routes=[], trip_requirements=self.requirements))

    def test_stay_model_failure_does_not_fabricate_fallback_hotels(self):
        with patch.object(accommodation, "get_llm", side_effect=ConnectionError):
            with self.assertRaises(RuntimeError):
                accommodation.search_accommodations("Thái Nguyên")

    def test_schedule_keeps_minutes_and_respects_relaxed_visit_duration(self):
        second = dict(self.atk, id="second", name="Điểm bổ sung")
        itinerary = api.build_itinerary([self.atk, second], 1, "Cab",
            lambda *args: {"distance_km": 12, "duration_minutes": 37}, {"pace": "relaxed"})
        schedule = itinerary["days"][0]["schedule"]
        first_visit = next(item for item in schedule if item.get("place_id") == "atk")
        second_visit = next(item for item in schedule if item.get("place_id") == "second")
        minutes = lambda value: int(value[:2]) * 60 + int(value[3:])
        self.assertEqual(minutes(second_visit["time"]) - minutes(first_visit["time"]), 150 + 60 + 37)
        times = [minutes(item["time"]) for item in schedule]
        self.assertEqual(times, sorted(times))

    def test_nearby_required_and_complementary_stop_share_a_day_and_routes_match(self):
        cave = dict(self.atk, id="cave", name="Chùa Hang Định Hóa", latitude=21.91, longitude=105.49)
        temple = dict(self.atk, id="temple", name="Đền Đuổm", latitude=21.755, longitude=105.707)
        memorial = dict(self.atk, id="memorial", name="Di tích 27/7", latitude=21.628, longitude=105.633)
        with patch.object(api, "retry_missing_coordinates", side_effect=lambda p, d: p), \
             patch.object(api, "calculate_route", return_value={"distance_km": 18, "duration_minutes": 37, "source": "test"}):
            plan = api.generate_itinerary(api.GenerateItineraryRequest(destination="Thái Nguyên", number_of_days=3,
                transportation_preference="Cab", selected_places=[self.atk, cave, temple, memorial], trip_requirements=self.requirements))
        first_day_ids = [item.get("place_id") for item in plan["itinerary"]["days"][0]["schedule"] if item.get("place_id")]
        self.assertEqual(first_day_ids, ["atk", "cave"])
        self.assertEqual(len(plan["routes"]), 1)
        self.assertEqual(plan["routes"][0]["day_number"], 1)
        self.assertEqual(plan["routes"][0]["origin_name"], self.atk["name"])


if __name__ == "__main__":
    unittest.main()
