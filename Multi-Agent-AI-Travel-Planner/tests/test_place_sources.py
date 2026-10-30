import unittest
from unittest.mock import patch

from src.schemas import Place
from src.tools import places
from src.tools.mythainguyen import _detail_links, parse_detail, fetch_catalog
from src import api
from src.api import build_itinerary


class SourceParserTests(unittest.TestCase):
    def test_list_parser_uses_verified_card_structure_and_relative_urls(self):
        markup = '''<ul id="data-pagination"><li class="item-city"><div class="media-body"><h3 class="place-name"><a href="/vi/denduom">Đền Đuổm</a></h3><span>Xã Phú Lương, Tỉnh Thái Nguyên</span><p class="intro">Giới thiệu ngắn</p></div></li></ul>'''
        row = _detail_links(markup)[0]
        self.assertEqual(row["url"], "https://mythainguyen.vn/vi/denduom")
        self.assertEqual(row["name"], "Đền Đuổm")
        self.assertIn("Phú Lương", row["address"])

    def test_detail_parser_prefers_full_modal_and_ignores_tours(self):
        full = "Lịch sử đầy đủ của địa điểm. Có nhiều thông tin hữu ích."
        markup = f'''<div class="example5"><div>KHU DI TÍCH ATK ĐỊNH HÓA</div></div><h2>Giới thiệu</h2><div>Địa chỉ: Xã Phú Lương, Tỉnh Thái Nguyên</div><img data-src="/Uploads/den.jpg"><p>Đoạn rút gọn...</p><div id="myModal1"><div class="cls_modal-body"><p>{full}</p></div></div><div>Lịch trình mẫu Giá vé tham quan 120.000 đ</div>'''
        result = parse_detail(markup, "https://mythainguyen.vn/vi/denduom", {"name": "Đền Đuổm"})
        self.assertEqual(result["name"], "KHU DI TÍCH ATK ĐỊNH HÓA")
        self.assertEqual(result["introduction"], full)
        self.assertNotIn("Lịch trình mẫu", result["introduction"])
        self.assertNotIn("120.000", result["introduction"])
        self.assertEqual(result["images"], ["https://mythainguyen.vn/Uploads/den.jpg"])

    def test_detail_parser_reads_paired_coordinate_attributes_and_records_source(self):
        markup = '''<div class="place-detail" data-lat="21.7001" data-lng="105.7002"></div><div class="example5">Đền Đuổm</div>'''
        result = parse_detail(markup, "https://mythainguyen.vn/vi/denduom", {"name": "Đền Đuổm"})
        self.assertEqual((result["latitude"], result["longitude"]), (21.7001, 105.7002))
        self.assertEqual(result["coordinate_source"], "mythainguyen_detail")

    def test_detail_parser_supports_longitude_and_map_object_link_but_ignores_viewport(self):
        attrs = parse_detail('''<div class="map" data-latitude="21.7" data-longitude="105.8"></div>''',
                             "https://mythainguyen.vn/vi/den", {"name": "Đền"})
        self.assertEqual((attrs["latitude"], attrs["longitude"]), (21.7, 105.8))
        data_lon = parse_detail('''<div data-lat="21.7" data-lon="105.8"></div>''',
                                "https://mythainguyen.vn/vi/den", {"name": "Đền"})
        self.assertEqual((data_lon["latitude"], data_lon["longitude"]), (21.7, 105.8))
        pin = parse_detail('''<a href="https://maps.google.com/?q=21.71,105.81">Bản đồ</a>''',
                           "https://mythainguyen.vn/vi/den", {"name": "Đền"})
        self.assertEqual((pin["latitude"], pin["longitude"]), (21.71, 105.81))
        embedded_pin = parse_detail('''<a href="https://maps.google.com/maps/place/den/data=!3d21.72!4d105.82">Bản đồ</a>''',
                                    "https://mythainguyen.vn/vi/den", {"name": "Đền"})
        self.assertEqual((embedded_pin["latitude"], embedded_pin["longitude"]), (21.72, 105.82))
        viewport = parse_detail('''<a href="https://maps.google.com/@21.71,105.81,14z">Bản đồ</a>''',
                                "https://mythainguyen.vn/vi/den", {"name": "Đền"})
        self.assertIsNone(viewport["latitude"])

    def test_detail_parser_rejects_invalid_and_related_content_coordinates(self):
        invalid = parse_detail('''<div data-lat="nan" data-lng="105.8"></div>''',
                               "https://mythainguyen.vn/vi/den", {"name": "Đền"})
        related = parse_detail('''<div class="related-tours"><div data-lat="21.7" data-lng="105.8"></div></div>''',
                               "https://mythainguyen.vn/vi/den", {"name": "Đền"})
        self.assertIsNone(invalid["latitude"])
        self.assertIsNone(related["latitude"])

    def test_verified_ajax_pagination_is_followed_until_empty(self):
        card = lambda slug, name: f'<li class="item-city"><h3 class="place-name"><a href="/vi/{slug}">{name}</a></h3><span>Phường Linh Sơn</span></li>'
        responses = [f"<ul>{card('a','A')}</ul>", f"<ul>{card('b','B')}</ul>", ""]
        calls = []
        def fetcher(url, data=None):
            calls.append((url, data.decode() if data else None))
            return responses.pop(0)
        rows = fetch_catalog(max_pages=5, fetcher=fetcher)
        self.assertEqual([row["name"] for row in rows], ["A", "B"])
        self.assertIn("pageIndex=2", calls[1][1])
        self.assertIn("GetListPlaceNew", calls[1][0])


class PlacesIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.mytn = {"name": "Đền Đuổm", "address": "Xã Phú Lương, Tỉnh Thái Nguyên",
                     "introduction": "Đền cổ thờ danh nhân, di tích lịch sử.", "latitude": 21.7, "longitude": 105.7,
                     "url": "https://mythainguyen.vn/vi/denduom", "category_source": "Di tích",
                     "admission_fee_source": None, "contact_source": {}}
        self.wiki = {"name": "Đền Đuổm", "introduction": "Wikipedia extract.", "latitude": None, "longitude": None,
                     "pageid": 123, "url": "https://vi.wikipedia.org/wiki/Den_Duom", "language": "vi"}

    def _discover(self, wiki, mytn=None, interests=None):
        with patch.object(places, "fetch_mythainguyen_places", return_value=mytn if mytn is not None else [self.mytn]), \
             patch.object(places, "fetch_notable_places_wikipedia", return_value=wiki), \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)), \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            return places.search_places_osm("Thái Nguyên", interests=interests or ["Heritage & Architecture"])

    def test_thai_nguyen_never_calls_wikipedia_and_keeps_mytn_provenance(self):
        with patch.object(places, "fetch_mythainguyen_places", return_value=[self.mytn]), \
             patch.object(places, "fetch_notable_places_wikipedia") as wiki, \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)), \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            output = places.search_places_osm("Thái Nguyên", interests=["Heritage & Architecture"])
        wiki.assert_not_called()
        place = next(p for p in output if p["name"] == "Đền Đuổm")
        self.assertEqual([x["name"] for x in place["sources"]], ["My Thái Nguyên"])
        self.assertTrue(place["sources"][0]["url"].startswith("https://mythainguyen.vn/"))

    def test_valid_source_coordinates_skip_nominatim_lookup(self):
        with patch.object(places, "fetch_mythainguyen_places", return_value=[self.mytn]), \
             patch.object(places, "fetch_notable_places_wikipedia", return_value=[]), \
             patch.object(places, "geocode_osm_place") as geocoder, \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            result = places.search_places_osm("Thái Nguyên", interests=["Heritage & Architecture"])
        geocoder.assert_not_called()
        item = next(p for p in result if p["name"] == self.mytn["name"])
        self.assertEqual(item["geocoding_status"], "source_coordinates")

    def test_mythainguyen_only_place_survives_without_wikipedia(self):
        only = dict(self.mytn, name="Di tích chỉ có trên cổng tỉnh")
        selected = dict(only, id="only", category="Heritage & Architecture", description="Di tích lịch sử.", images=[], sources=[{"name":"My Thái Nguyên", "url":only["url"]}], geocoding_status="source_coordinates", reference_data={})
        with patch.object(places, "fetch_mythainguyen_places", return_value=[only]), \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)):
            output = places.search_places_osm("Thái Nguyên", interests=[])
        self.assertEqual([x["name"] for x in output], [only["name"]])

    def test_same_name_distinct_addresses_are_not_merged(self):
        a = dict(self.mytn, name="Chùa Hang", address="Xã Định Hóa")
        b = dict(self.mytn, name="Chùa Hang", address="Phường Linh Sơn", url="https://mythainguyen.vn/vi/chuahang")
        with patch.object(places, "fetch_mythainguyen_places", return_value=[a, b]), \
             patch.object(places, "fetch_notable_places_wikipedia", return_value=[]), \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)), \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            output = places.search_places_osm("Thái Nguyên", limit=10, interests=["Heritage & Architecture"])
        self.assertEqual(len(output), 2)
        self.assertNotEqual(output[0]["id"], output[1]["id"])

    def test_specific_locality_and_city_scope(self):
        from src.tools.places import _in_scope
        self.assertTrue(_in_scope({"address": "Xã Định Hóa, Tỉnh Thái Nguyên"}, "Thái Nguyên"))
        self.assertTrue(_in_scope({"address": "Phường Linh Sơn, Tỉnh Thái Nguyên"}, "Thành phố Thái Nguyên"))
        self.assertFalse(_in_scope({"address": "Xã Định Hóa, Tỉnh Thái Nguyên"}, "Thành phố Thái Nguyên"))
        self.assertFalse(_in_scope({"address": "Xã Phú Lương"}, "Thái Nguyên, Định Hóa"))

    def test_limit_is_final_output_limit_and_no_coordinate_is_preserved(self):
        many = [dict(self.mytn, name=f"Di tích {i}", address=f"Xã {i}", url=f"https://mythainguyen.vn/vi/p{i}", latitude=None, longitude=None) for i in range(14)]
        with patch.object(places, "fetch_mythainguyen_places", return_value=many), \
             patch.object(places, "fetch_notable_places_wikipedia", return_value=[]), \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)), \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            output = places.search_places_osm("Thái Nguyên", limit=10)
        self.assertEqual(len(output), 10)
        self.assertIsNone(output[0]["latitude"])
        self.assertEqual(output[0]["geocoding_status"], "not_found")

    def test_outside_source_destination_still_uses_wikipedia(self):
        with patch.object(places, "fetch_mythainguyen_places") as mytn, \
             patch.object(places, "fetch_notable_places_wikipedia", return_value=[dict(self.wiki, introduction="An ancient temple located in Huế.")]), \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)), \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            output = places.search_places_osm("Huế", interests=["Heritage & Architecture"])
        mytn.assert_not_called()
        self.assertTrue(output)

    def test_wikipedia_results_must_be_local_attractions_not_people_companies_or_city_pages(self):
        from src.tools.places import _category_from_source
        self.assertIsNone(_category_from_source("AirAsia", "AirAsia is a Malaysian airline headquartered in Kuala Lumpur."))
        self.assertIsNone(_category_from_source("Balendra Shah", "Balendra Shah is a Nepalese politician and rapper."))
        self.assertIsNone(_category_from_source("Bengaluru", "Bengaluru is the capital city of Karnataka."))
        self.assertIsNone(_category_from_source("Avenue Road", "Avenue Road is a road in Bengaluru."))
        self.assertEqual(_category_from_source("Lalbagh Botanical Garden", "A botanical garden located in Bengaluru."), "Parks & Leisure")
        candidates = [
            dict(self.wiki, name="AirAsia", introduction="AirAsia is a Malaysian airline headquartered in Kuala Lumpur."),
            dict(self.wiki, name="Balendra Shah", introduction="Balendra Shah is a Nepalese politician and rapper."),
            dict(self.wiki, name="Bengaluru", introduction="Bengaluru is the capital city of Karnataka."),
            dict(self.wiki, name="Avenue Road", introduction="Avenue Road is a road in Bengaluru."),
            dict(self.wiki, name="Lalbagh Botanical Garden", introduction="A botanical garden located in Bengaluru."),
            dict(self.wiki, name="Nandi Hills", introduction="Nandi Hills is a hill station near Bengaluru."),
        ]
        with patch.object(places, "fetch_mythainguyen_places") as mytn, \
             patch.object(places, "fetch_notable_places_wikipedia", return_value=candidates), \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)), \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            output = places.search_places_osm("Bengaluru", interests=["Parks & Leisure", "Trekking & Adventure"])
        mytn.assert_not_called()
        self.assertEqual({place["name"] for place in output}, {"Lalbagh Botanical Garden", "Nandi Hills"})

    def test_bengaluru_geocoder_accepts_common_bangalore_name_variant_only_in_destination(self):
        from src.tools.places import _name_variants, _valid_geocode_hit, _geocode_queries
        self.assertIn("Bangalore Palace", _name_variants("Bengaluru Palace"))
        self.assertTrue(any("Bangalore Palace" in query for query in _geocode_queries("Bengaluru Palace", "Bengaluru", None)))
        hit = self._nominatim_fixture(
            name="Bangalore Palace", namedetails={"name": "Bangalore Palace"},
            address={"country": "India", "country_code": "in", "state": "Karnataka", "city": "Bengaluru"},
            display_name="Bangalore Palace, Bengaluru, Karnataka, India",
        )
        self.assertEqual(_valid_geocode_hit(hit, "Bengaluru Palace", "Bengaluru"), (21.7001, 105.7002))
        wrong_city = dict(hit, address={**hit["address"], "city": "Chennai", "state": "Tamil Nadu"},
                          display_name="Bangalore Palace, Chennai, Tamil Nadu, India")
        self.assertIsNone(_valid_geocode_hit(wrong_city, "Bengaluru Palace", "Bengaluru"))

    def test_wikipedia_language_tracks_destination_script(self):
        from src.tools.places import fetch_notable_places_wikipedia
        with patch.object(places, "_wiki_search", return_value=[]) as search:
            fetch_notable_places_wikipedia("Bengaluru")
        self.assertEqual([call.args[1] for call in search.call_args_list], ["en"])
        with patch.object(places, "_wiki_search", return_value=[]) as search:
            fetch_notable_places_wikipedia("Thái Nguyên")
        self.assertEqual([call.args[1] for call in search.call_args_list], ["vi", "en"])

    def test_legacy_curator_empty_interests_remain_unchanged_outside_thai_nguyen(self):
        candidates = [
            {"id": "temple", "name": "Chùa Hang", "introduction": "Ngôi chùa trong hang.", "category": "Heritage & Architecture"},
            {"id": "lake", "name": "Hồ Núi Cốc", "introduction": "Hồ và khu du lịch.", "category": "Parks & Leisure"},
        ]
        with patch.object(places, "get_llm") as llm:
            output = places._ai_curate(candidates, [], "Bengaluru", 10)
        llm.assert_not_called()
        self.assertEqual({place["id"] for place in output}, {"temple", "lake"})

    def test_api_interest_default_is_empty(self):
        request = api.RequirementsRequest()
        self.assertEqual(request.interests, [])

    def test_mythainguyen_failure_does_not_fall_back_to_wikipedia(self):
        with patch.object(places, "fetch_mythainguyen_places", side_effect=RuntimeError("catalog offline")), \
             patch.object(places, "fetch_notable_places_wikipedia") as wiki, \
             patch.object(places, "geocode_osm_place", return_value=(None, None, False)), \
             patch.object(places, "get_llm", side_effect=RuntimeError("LLM offline")):
            output = places.search_places_osm("Thái Nguyên", interests=["Heritage & Architecture"])
        wiki.assert_not_called()
        self.assertEqual(output, [])
        self.assertIn("MyThaiNguyen", places.get_places_notice())

    def test_api_discovery_itinerary_modification_and_final_dossier(self):
        record = {"id": "den-duom", "name": "Đền Đuổm", "category": "Heritage & Architecture", "description": "Di tích",
                  "introduction": "Giới thiệu đầy đủ", "address": "Phú Lương", "latitude": 21.7, "longitude": 105.7,
                  "sources": [{"name": "My Thái Nguyên", "url": self.mytn["url"], "retrieved_at": "fixture"}],
                  "geocoding_status": "source_coordinates"}
        request = api.RequirementsRequest(destination="Thái Nguyên", number_of_days=1, number_of_travelers=1,
                                          transportation_preference="Cab", interests=["Heritage & Architecture"])
        with patch.object(api, "search_places_osm", return_value=[record]), \
             patch.object(api, "calculate_route", return_value={"distance_km": 1, "duration_minutes": 3, "source": "fixture"}), \
             patch.object(api, "modify_selection_with_llm", return_value=[record]):
            available = api.initiate_trip(request)["available_places"]
            plan = api.generate_itinerary(api.GenerateItineraryRequest(destination="Thái Nguyên", number_of_days=1,
                         transportation_preference="Cab", selected_places=available))
            changed = api.modify_itinerary(api.ModifyItineraryRequest(feedback="giữ nguyên", available_places=available,
                         selected_places=available, destination="Thái Nguyên", number_of_days=1, transportation_preference="Cab"))
        self.assertEqual(changed["selected_places"][0]["sources"], record["sources"])
        activity = next(x for x in plan["itinerary"]["days"][0]["schedule"] if x.get("place_id"))
        self.assertEqual(activity["sources"], record["sources"])
        dossier = api.finalize_trip(api.FinalizeTripRequest(destination="Thái Nguyên", number_of_days=1, number_of_travelers=1,
                   transportation_preference="Cab", itinerary=changed["itinerary"], selected_accommodation={"price_per_night": 10},
                   routes=[], selected_places=changed["selected_places"]))
        self.assertEqual(dossier["selected_places"][0]["sources"], record["sources"])

    def test_schema_itinerary_and_modification_keep_place_provenance(self):
        record = {"id": "den-duom", "name": "Đền Đuổm", "category": "Heritage & Architecture", "description": "Di tích",
                  "latitude": 21.7, "longitude": 105.7, "introduction": "Giới thiệu đầy đủ", "address": "Phú Lương",
                  "sources": [{"name": "My Thái Nguyên", "url": self.mytn["url"]}], "geocoding_status": "source_coordinates"}
        normalized = Place(**record).model_dump()
        self.assertEqual(normalized["sources"], record["sources"])
        itin = build_itinerary([normalized], 1, "Cab", lambda *a: {})
        activity = next(x for x in itin["days"][0]["schedule"] if x.get("place_id"))
        self.assertEqual(activity["place_id"], "den-duom")
        self.assertEqual(activity["sources"], record["sources"])

    def test_api_keeps_place_and_marks_missing_coordinates_without_route(self):
        place = {"id": "unknown", "name": "Địa điểm chưa có tọa độ", "category": "Heritage & Architecture",
                 "description": "Nguồn", "latitude": None, "longitude": None, "geocoding_status": "unavailable",
                 "sources": [{"name": "My Thái Nguyên", "url": self.mytn["url"]}]}
        with patch.object(api, "retry_missing_coordinates", return_value=[place]):
            result = api.generate_itinerary(api.GenerateItineraryRequest(destination="Thái Nguyên", number_of_days=1,
                         transportation_preference="Cab", selected_places=[place]))
        self.assertEqual(result["routes"], [])
        activity = next(x for x in result["itinerary"]["days"][0]["schedule"] if x.get("place_id"))
        self.assertEqual(activity["geocoding_status"], "unavailable")
        self.assertIn("Chưa xác định được tọa độ", activity["details"])

    def _nominatim_fixture(self, **overrides):
        result = {"lat": "21.7001", "lon": "105.7002", "name": "Đền Đuổm",
                  "namedetails": {"name": "Đền Đuổm", "name:en": "Duom Temple"},
                  "category": "tourism", "type": "attraction", "addresstype": "tourism",
                  "address": {"country": "Việt Nam", "country_code": "vn", "state": "Thái Nguyên", "county": "Phú Lương"},
                  "display_name": "Đền Đuổm, Phú Lương, Thái Nguyên, Việt Nam",
                  "osm_type": "way", "osm_id": "123", "importance": 0.42,
                  "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://www.openstreetmap.org/copyright"}
        return dict(result, **overrides)

    def test_nominatim_matches_alias_and_jsonv2_request_params(self):
        from src.tools.places import _geocode_nominatim_place, _geo_cache, _nominatim_request
        _geo_cache.clear()
        fixture = self._nominatim_fixture(name="Duom Temple", namedetails={"name:vi": "Đền Đuổm"})
        with patch("src.tools.places._nominatim_request", return_value=[fixture]) as request:
            result = _geocode_nominatim_place("Di tích Đền Đuổm", "Thái Nguyên", "Phú Lương", aliases=["Duom Temple"])
        self.assertEqual(result["status"], "nominatim_verified")
        self.assertEqual((result["latitude"], result["longitude"]), (21.7001, 105.7002))
        self.assertEqual(result["coordinate_source"], "Nominatim")
        self.assertIn("OpenStreetMap", result["attribution"])
        request.assert_called_once()
        self.assertLessEqual(len(request.call_args.args), 2)

    def test_nominatim_validation_rejects_name_country_region_type_and_coordinates(self):
        from src.tools.places import _valid_geocode_hit
        valid = self._nominatim_fixture()
        self.assertEqual(_valid_geocode_hit(valid, "Đền Đuổm", "Thái Nguyên", "Phú Lương"), (21.7001, 105.7002))
        variants = [dict(valid, name="Đền khác", namedetails={"name": "Đền khác"}),
                    dict(valid, address={**valid["address"], "country_code": "us"}),
                    dict(valid, address={**valid["address"], "state": "Hà Nội"},
                         display_name="Đền Đuổm, Phú Lương, Hà Nội, Việt Nam"),
                    dict(valid, category="place", type="city", addresstype="city"),
                    dict(valid, category="highway", type="residential", addresstype="road"),
                    dict(valid, lat="nan"), dict(valid, lon="181")]
        for candidate in variants:
            self.assertIsNone(_valid_geocode_hit(candidate, "Đền Đuổm", "Thái Nguyên", "Phú Lương"), candidate)
        alias = dict(valid, name="Duom Temple", namedetails={"name:vi": "Đền Đuổm"})
        self.assertIsNotNone(_valid_geocode_hit(alias, "Đền Đuổm", "Thái Nguyên", "Phú Lương", ["Duom Temple"]))

    def test_invalid_existing_coordinates_are_discarded_and_retried(self):
        record = {"id": "bad", "name": "Điểm có tọa độ lỗi", "latitude": 999, "longitude": 105.7}
        with patch.object(places, "geocode_osm_place", return_value=(None, None, False)) as geocoder:
            places.retry_missing_coordinates([record], "Huế")
        geocoder.assert_called_once()
        self.assertIsNone(record["latitude"])
        self.assertIsNone(record["longitude"])
        self.assertEqual(record["geocoding_status"], "not_found")

    def test_nominatim_empty_rejected_ambiguous_dedup_and_retry_cache(self):
        from src.tools.places import _geocode_nominatim_place, _geo_cache
        _geo_cache.clear()
        with patch("src.tools.places._nominatim_request", return_value=[]) as lookup:
            missing = _geocode_nominatim_place("Điểm vắng", "Thái Nguyên")
            cached = _geocode_nominatim_place("Điểm vắng", "Thái Nguyên")
            _geocode_nominatim_place("Điểm vắng", "Thái Nguyên", retry=True)
        self.assertEqual(missing["status"], "not_found")
        self.assertTrue(cached["cache_hit"])
        self.assertEqual(lookup.call_count, 2)
        _geo_cache.clear()
        wrong = self._nominatim_fixture(name="Đền khác", namedetails={"name": "Đền khác"})
        with patch("src.tools.places._nominatim_request", return_value=[wrong]):
            self.assertEqual(_geocode_nominatim_place("Đền Đuổm", "Thái Nguyên")["status"], "rejected")
        _geo_cache.clear()
        first = self._nominatim_fixture(osm_id="123", importance=0.5)
        duplicate = dict(first, lat="21.7001")
        second = self._nominatim_fixture(osm_id="456", lat="21.8", importance=0.5)
        with patch("src.tools.places._nominatim_request", return_value=[first, duplicate, second]):
            self.assertEqual(_geocode_nominatim_place("Đền Đuổm", "Thái Nguyên")["status"], "ambiguous")

    def test_nominatim_uses_country_filter_only_for_thai_nguyen_and_identifiable_ua(self):
        from unittest.mock import MagicMock
        from src.tools.places import _nominatim_request
        urls, agents = [], []
        def open_response(request, timeout):
            urls.append(request.full_url); agents.append(request.get_header("User-agent"))
            response = MagicMock(); response.__enter__.return_value.read.return_value = b'[]'
            return response
        with patch("src.tools.places.urllib.request.urlopen", side_effect=open_response), \
             patch("src.tools.places.time.monotonic", side_effect=[100, 100, 100.2, 100.2]), \
             patch("src.tools.places.time.sleep") as sleeper:
            _nominatim_request("Đền Đuổm, Thái Nguyên", "Thái Nguyên")
            _nominatim_request("Đền cổ, Huế", "Huế")
        self.assertAlmostEqual(sleeper.call_args.args[0], 0.8)
        self.assertIn("format=jsonv2", urls[0]); self.assertIn("addressdetails=1", urls[0])
        self.assertIn("namedetails=1", urls[0]); self.assertIn("limit=5", urls[0])
        self.assertIn("accept-language=vi%2Cen", urls[0]); self.assertIn("countrycodes=vn", urls[0])
        self.assertNotIn("countrycodes", urls[1])
        self.assertTrue(all(agent.startswith("Multi-Agent-AI-Travel-Planner") for agent in agents))

    def test_nominatim_429_cooldown_403_timeout_and_bounded_5xx(self):
        import urllib.error
        from unittest.mock import MagicMock
        from src.tools import places as module
        module._geo_cache.clear(); module._nominatim_blocked_until = 0; module._last_nominatim_request = 0
        rate_error = urllib.error.HTTPError("https://nominatim.test/search", 429, "Too Many Requests", {"Retry-After": "60"}, None)
        with patch("src.tools.places.urllib.request.urlopen", side_effect=rate_error), patch("src.tools.places.time.monotonic", return_value=100), patch("src.tools.places.time.sleep") as sleeper:
            with self.assertRaisesRegex(RuntimeError, "rate_limited"):
                module._nominatim_request("x", "Huế")
            with self.assertRaisesRegex(RuntimeError, "rate_limited"):
                module._nominatim_request("y", "Huế")
            self.assertEqual(module._nominatim_blocked_until, 160)
            sleeper.assert_not_called()
        module._nominatim_blocked_until = 0
        forbidden = urllib.error.HTTPError("https://nominatim.test/search", 403, "Forbidden", {}, None)
        with patch("src.tools.places.urllib.request.urlopen", side_effect=forbidden):
            with self.assertRaisesRegex(RuntimeError, "access_forbidden"):
                module._nominatim_request("x", "Huế")
        module._geo_cache.clear()
        with patch("src.tools.places._nominatim_request", side_effect=RuntimeError("access_forbidden")):
            denied = module._geocode_nominatim_place("Điểm", "Huế")
        self.assertEqual((denied["status"], denied["reason"]), ("service_error", "access_forbidden"))
        for malformed, expected in ((b"{broken", "invalid_json"), (b'{"results": []}', "invalid_response_schema")):
            response = MagicMock()
            response.__enter__.return_value.read.return_value = malformed
            with patch("src.tools.places.urllib.request.urlopen", return_value=response), patch("src.tools.places.time.sleep"):
                with self.assertRaisesRegex(RuntimeError, expected):
                    module._nominatim_request("x", "Huế")
        timeout = urllib.error.URLError("timed out")
        with patch("src.tools.places.urllib.request.urlopen", side_effect=timeout) as opener, patch("src.tools.places.time.sleep"):
            with self.assertRaisesRegex(RuntimeError, "network_or_timeout"):
                module._nominatim_request("x", "Huế")
            self.assertEqual(opener.call_count, 2)
        server = urllib.error.HTTPError("https://nominatim.test/search", 503, "Unavailable", {}, None)
        with patch("src.tools.places.urllib.request.urlopen", side_effect=server) as opener, patch("src.tools.places.time.sleep"):
            with self.assertRaisesRegex(RuntimeError, "service_unavailable"):
                module._nominatim_request("x", "Huế")
            self.assertEqual(opener.call_count, 2)

    def test_nominatim_invalid_payload_cache_scope_and_attribution_in_api_cli(self):
        import contextlib, io
        from pathlib import Path
        from src.tools.places import _geocode_nominatim_place, _geo_cache
        from src.main import itinerary_agent_node, human_itinerary_gate_node
        _geo_cache.clear()
        with patch("src.tools.places._nominatim_request", side_effect=RuntimeError("invalid_response_schema")):
            self.assertEqual(_geocode_nominatim_place("Đền", "Huế")["reason"], "invalid_response_schema")
        _geo_cache.clear()
        fixture = self._nominatim_fixture()
        with patch("src.tools.places._nominatim_request", return_value=[fixture]) as lookup:
            one = _geocode_nominatim_place("Đền Đuổm", "Thái Nguyên")
            two = _geocode_nominatim_place("Đền Đuổm", "Thái Nguyên")
        self.assertTrue(two["cache_hit"]); self.assertEqual(lookup.call_count, 1)
        self.assertTrue(any(key.startswith("nominatim:") for key in _geo_cache))
        html = Path("src/static/index.html").read_text()
        self.assertIn('s.geocoding_status !== "nominatim_verified"', html)
        self.assertIn("https://www.openstreetmap.org/copyright", html)
        self.assertNotIn("Powered by", html)
        record = {"id": "osm-place", "name": "Đền Đuổm", "category": "Heritage & Architecture", "description": "Nguồn",
                  "latitude": 21.7, "longitude": 105.7, "geocoding_status": "nominatim_verified", "coordinate_source": "Nominatim",
                  "coordinate_attribution": one["attribution"], "sources": [{"name": "My Thái Nguyên", "url": self.mytn["url"]}]}
        with patch.object(api, "retry_missing_coordinates", return_value=[record]), patch.object(api, "calculate_route", return_value={"distance_km": 1, "duration_minutes": 3, "source": "fixture"}):
            response = api.generate_itinerary(api.GenerateItineraryRequest(destination="Thái Nguyên", number_of_days=1,
                transportation_preference="Cab", selected_places=[record]))
        activity = next(x for x in response["itinerary"]["days"][0]["schedule"] if x.get("place_id"))
        self.assertEqual(activity["geocoding_status"], "nominatim_verified")
        with patch("src.main.retry_missing_coordinates", return_value=[record]), patch("src.main.calculate_route", return_value={"distance_km": 1, "duration_minutes": 3}):
            cli_result = itinerary_agent_node({"destination": "Thái Nguyên", "number_of_days": 1, "selected_places": [record]})
        cli_item = next(x for x in cli_result["itinerary"]["days"][0]["schedule"] if x.get("place_id"))
        console = io.StringIO()
        with contextlib.redirect_stdout(console), patch("builtins.input", return_value="1"):
            human_itinerary_gate_node({"itinerary": cli_result["itinerary"]})
        self.assertIn("Nguồn tọa độ: Nominatim / OpenStreetMap", console.getvalue())

if __name__ == "__main__":
    unittest.main()
