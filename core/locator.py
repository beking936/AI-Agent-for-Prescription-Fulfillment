# # core/locator.py

# import time
# import requests
# from math import radians, sin, cos, sqrt, atan2
# from typing import List, Dict, Optional
# import re

# from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults


# class EmergencyLocatorAgent:
#     def __init__(self):
#         """تهيئة الـ Agent"""
#         self.user_location: Optional[tuple] = None
#         self.nominatim_url = "https://nominatim.openstreetmap.org"
#         self.user_agent = "EmergencyLocator/1.0"

#         # DuckDuckGo Tools
#         self.search_run = DuckDuckGoSearchRun()
#         self.search_results = DuckDuckGoSearchResults()

#         print("✅ تم تهيئة Agent مع DuckDuckGo Search")

#     # ------------------- Location helpers -------------------

#     def get_location_from_ip(self) -> Optional[tuple]:
#         try:
#             print("🔍 جاري تحديد موقعك من خلال IP...")
#             response = requests.get("http://ip-api.com/json/", timeout=5)
#             data = response.json()

#             if data.get("status") == "success":
#                 lat = data["lat"]
#                 lon = data["lon"]
#                 city = data.get("city", "غير معروف")
#                 country = data.get("country", "غير معروف")

#                 print(f"✅ تم تحديد موقعك: {city}, {country}")
#                 print(f"📍 الإحداثيات: {lat}, {lon}")

#                 self.user_location = (lat, lon)
#                 return lat, lon
#             else:
#                 raise Exception("فشل تحديد الموقع من IP")

#         except Exception as e:
#             print(f"❌ خطأ في تحديد الموقع: {e}")
#             return None

#     def get_location_from_address(self, address: str) -> Optional[tuple]:
#         try:
#             print(f"🔍 جاري البحث عن العنوان: {address}")

#             params = {"q": address, "format": "json", "limit": 1}
#             headers = {"User-Agent": self.user_agent}

#             response = requests.get(
#                 f"{self.nominatim_url}/search",
#                 params=params,
#                 headers=headers,
#                 timeout=5,
#             )

#             data = response.json()
#             if data:
#                 lat = float(data[0]["lat"])
#                 lon = float(data[0]["lon"])
#                 display_name = data[0]["display_name"]

#                 print(f"✅ تم العثور على: {display_name}")
#                 print(f"📍 الإحداثيات: {lat}, {lon}")

#                 self.user_location = (lat, lon)
#                 return lat, lon

#             print("❌ لم يتم العثور على العنوان")
#             return None

#         except Exception as e:
#             print(f"❌ خطأ في البحث عن العنوان: {e}")
#             return None

#     def ensure_location(
#         self,
#         address: Optional[str] = None,
#         use_ip_fallback: bool = True,
#     ) -> bool:
#         if self.user_location is not None:
#             return True

#         loc = None
#         if address:
#             loc = self.get_location_from_address(address)
#         elif use_ip_fallback:
#             loc = self.get_location_from_ip()

#         if loc is None:
#             return False

#         self.user_location = loc
#         return True

#     # ------------------- Distance & utilities -------------------

#     def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#         R = 6371
#         lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1

#         a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
#         c = 2 * atan2(sqrt(a), sqrt(1 - a))
#         return R * c

#     def _format_address(self, tags: Dict) -> str:
#         parts = []
#         if "addr:street" in tags:
#             parts.append(tags["addr:street"])
#         if "addr:housenumber" in tags:
#             parts.append(tags["addr:housenumber"])
#         if "addr:city" in tags:
#             parts.append(tags["addr:city"])
#         return ", ".join(parts) if parts else "غير متوفر"

#     def get_directions_url(self, dest_lat: float, dest_lon: float) -> str:
#         if not self.user_location:
#             return "يجب تحديد موقعك أولاً"
#         lat, lon = self.user_location
#         return f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={dest_lat},{dest_lon}"

#     # ------------------- Nearest pharmacies / hospitals -------------------

#     def find_nearest_pharmacies(self, radius_km: float = 5.0) -> List[Dict]:
#         if not self.user_location:
#             print("❌ يجب تحديد موقعك أولاً!")
#             return []
#         return self._find_places("pharmacy", radius_km)

#     def find_nearest_hospitals(self, radius_km: float = 5.0) -> List[Dict]:
#         if not self.user_location:
#             print("❌ يجب تحديد موقعك أولاً!")
#             return []
#         return self._find_places("hospital", radius_km)

#     def _find_places(self, place_type: str, radius_km: float) -> List[Dict]:
#         places = self._try_overpass_api(place_type, radius_km)
#         if places:
#             return places

#         print("⚠️ Overpass فشل، جاري التبديل إلى Nominatim...")
#         places = self._try_nominatim_search(place_type, radius_km)
#         if places:
#             return places

#         print("⚠️ Nominatim فشل، جاري استخدام DuckDuckGo كحل أخير...")
#         places = self._try_search_fallback(place_type, radius_km)
#         return places

#     def _try_overpass_api(self, place_type: str, radius_km: float) -> List[Dict]:
#         try:
#             lat, lon = self.user_location
#             radius_m = int(radius_km * 1000)

#             print(f"\n🔍 [Overpass] البحث عن {place_type} في نطاق {radius_km} كم...")

#             if place_type == "pharmacy":
#                 query = f'[out:json][timeout:30];node["amenity"="pharmacy"](around:{radius_m},{lat},{lon});out body;'
#             else:
#                 query = (
#                     '[out:json][timeout:30];'
#                     f'(node["amenity"="hospital"](around:{radius_m},{lat},{lon});'
#                     f'node["amenity"="clinic"](around:{radius_m},{lat},{lon}););out body;'
#                 )

#             servers = [
#                 "https://overpass-api.de/api/interpreter",
#                 "https://overpass.kumi.systems/api/interpreter",
#                 "https://overpass.openstreetmap.ru/api/interpreter",
#             ]

#             for server in servers:
#                 try:
#                     response = requests.post(
#                         server,
#                         data={"data": query},
#                         headers={"Content-Type": "application/x-www-form-urlencoded"},
#                         timeout=30,
#                     )
#                     if response.status_code == 200:
#                         data = response.json()
#                         places = []

#                         for element in data.get("elements", []):
#                             if "lat" in element and "lon" in element:
#                                 place_lat = element["lat"]
#                                 place_lon = element["lon"]
#                             elif "center" in element:
#                                 place_lat = element["center"]["lat"]
#                                 place_lon = element["center"]["lon"]
#                             else:
#                                 continue

#                             distance = self.calculate_distance(lat, lon, place_lat, place_lon)
#                             tags = element.get("tags", {})
#                             name = tags.get("name", tags.get("operator", "غير معروف"))
#                             address = self._format_address(tags)
#                             phone = tags.get("phone", tags.get("contact:phone", "غير متوفر"))
#                             opening_hours = tags.get("opening_hours", "غير متوفر")

#                             places.append({
#                                 "name": name,
#                                 "distance_km": round(distance, 2),
#                                 "latitude": place_lat,
#                                 "longitude": place_lon,
#                                 "address": address,
#                                 "phone": phone,
#                                 "opening_hours": opening_hours,
#                                 "type": tags.get("amenity", place_type),
#                             })

#                         places.sort(key=lambda x: x["distance_km"])
#                         if places:
#                             print(f"✅ [Overpass] تم العثور على {len(places)} {place_type}")
#                             return places

#                 except Exception as e:
#                     print(f"⚠️ فشل الخادم {server}: {e}")
#                     continue

#             return []

#         except Exception as e:
#             print(f"❌ [Overpass] خطأ غير متوقع: {e}")
#             return []

#     def _try_nominatim_search(self, place_type: str, radius_km: float) -> List[Dict]:
#         try:
#             lat, lon = self.user_location
#             print(f"\n🔍 [Nominatim] البحث عن {place_type}...")

#             reverse_url = f"{self.nominatim_url}/reverse"
#             params = {"lat": lat, "lon": lon, "format": "json"}
#             headers = {"User-Agent": self.user_agent}

#             response = requests.get(reverse_url, params=params, headers=headers, timeout=10)
#             location_data = response.json()

#             address = location_data.get("address", {})
#             city = (
#                 address.get("city")
#                 or address.get("town")
#                 or address.get("village")
#                 or address.get("state", "القاهرة")
#             )

#             search_term = f"{place_type} in {city}"
#             search_params = {
#                 "q": search_term,
#                 "format": "json",
#                 "limit": 50,
#                 "addressdetails": 1,
#             }

#             time.sleep(1)
#             response = requests.get(
#                 f"{self.nominatim_url}/search",
#                 params=search_params,
#                 headers=headers,
#                 timeout=10,
#             )

#             results = response.json()
#             places = []

#             for result in results:
#                 place_lat = float(result["lat"])
#                 place_lon = float(result["lon"])
#                 distance = self.calculate_distance(lat, lon, place_lat, place_lon)

#                 if distance <= radius_km:
#                     name = result.get("display_name", "").split(",")[0]
#                     address_parts = result.get("display_name", "").split(",")[1:3]
#                     addr = ", ".join(address_parts).strip() if address_parts else "غير متوفر"

#                     places.append({
#                         "name": name,
#                         "distance_km": round(distance, 2),
#                         "latitude": place_lat,
#                         "longitude": place_lon,
#                         "address": addr,
#                         "phone": "غير متوفر",
#                         "opening_hours": "غير متوفر",
#                         "type": place_type,
#                     })

#             places.sort(key=lambda x: x["distance_km"])
#             if places:
#                 print(f"✅ [Nominatim] تم العثور على {len(places)} {place_type}")
#             return places

#         except Exception as e:
#             print(f"❌ [Nominatim] خطأ: {e}")
#             return []

#     def _try_search_fallback(self, place_type: str, radius_km: float) -> List[Dict]:
#         try:
#             lat, lon = self.user_location
#             print(f"\n🔍 [DuckDuckGo] البحث عن {place_type}...")

#             reverse_url = f"{self.nominatim_url}/reverse"
#             params = {"lat": lat, "lon": lon, "format": "json"}
#             headers = {"User-Agent": self.user_agent}

#             response = requests.get(reverse_url, params=params, headers=headers, timeout=10)
#             location_data = response.json()

#             address = location_data.get("address", {})
#             city = address.get("city") or address.get("town") or "القاهرة"

#             if place_type == "pharmacy":
#                 query = f"pharmacies near {city} location address phone"
#             else:
#                 query = f"hospitals near {city} emergency location address"

#             search_result = self.search_run.run(query)

#             places = [{
#                 "name": f"نتائج البحث: {place_type} قريب من {city}",
#                 "distance_km": 0.0,
#                 "latitude": lat,
#                 "longitude": lon,
#                 "address": search_result[:200],
#                 "phone": "استخدم البحث أعلاه للتفاصيل",
#                 "opening_hours": "غير متوفر",
#                 "type": place_type,
#             }]

#             print("💡 [DuckDuckGo] تم الحصول على معلومات عامة")
#             return places

#         except Exception as e:
#             print(f"❌ [DuckDuckGo] خطأ: {e}")
#             return []

#     # ------------------- High-level chat formatting -------------------

#     def get_nearest_places(
#         self,
#         place_kind: str,
#         radius_km: float = 5.0,
#         address: Optional[str] = None,
#         use_ip_fallback: bool = True,
#     ) -> List[Dict]:
#         if not self.ensure_location(address=address, use_ip_fallback=use_ip_fallback):
#             print("❌ لا يمكن تحديد موقعك (لا عنوان ولا IP).")
#             return []

#         if place_kind == "pharmacy":
#             return self.find_nearest_pharmacies(radius_km=radius_km)
#         else:
#             return self.find_nearest_hospitals(radius_km=radius_km)

#     def format_places_for_chat(
#         self,
#         places: List[Dict],
#         place_label: str,
#         max_results: int = 3,
#     ) -> str:
#         if not places:
#             return f"❌ لم أستطع العثور على أي {place_label} قريبة بناءً على موقعك الحالي."

#         lines = [f"📍 أقرب {place_label} بناءً على موقعك:\n"]

#         for i, place in enumerate(places[:max_results], start=1):
#             name = place.get("name", "غير معروف")
#             distance = place.get("distance_km", 0.0)
#             address = place.get("address", "غير متوفر")
#             phone = place.get("phone", "غير متوفر")
#             opening_hours = place.get("opening_hours", "غير متوفر")

#             directions_url = self.get_directions_url(
#                 place.get("latitude"),
#                 place.get("longitude"),
#             )

#             lines.append(
#                 f"#{i} - {name}\n"
#                 f"  • المسافة: حوالي {distance} كم\n"
#                 f"  • العنوان: {address}\n"
#                 f"  • الهاتف: {phone}\n"
#                 f"  • مواعيد العمل: {opening_hours}\n"
#                 f"  • الاتجاهات على الخرائط: {directions_url}\n"
#             )

#         lines.append(
#             "\n⚠️ هذه معلومات تقريبية من مصادر عامة، "
#             "يفضل الاتصال بالمكان قبل الذهاب في حالات الطوارئ."
#         )
#         return "\n".join(lines)


# # ------------------- Intent detection -------------------

# PHARMACY_KEYWORDS = [
#     "nearest pharmacy",
#     "nearby pharmacy",
#     "pharmacy near me",
#     "صيدلية قريبة",
#     "اقرب صيدلية",
# ]

# HOSPITAL_KEYWORDS = [
#     "nearest hospital",
#     "hospital near me",
#     "مستشفى قريبة",
#     "اقرب مستشفى",
# ]


# def detect_locator_intent(user_message: str) -> Optional[str]:
#     """
#     Very simple intent detector:
#     Returns 'pharmacy' | 'hospital' | None
#     """
#     text = user_message.lower()

#     if any(k.lower() in text for k in PHARMACY_KEYWORDS):
#         return "pharmacy"
#     if any(k.lower() in text for k in HOSPITAL_KEYWORDS):
#         return "hospital"

#     if re.search(r"\bpharmacy\b", text):
#         return "pharmacy"
#     if re.search(r"\bhospital\b", text):
#         return "hospital"

#     return None
# _______________________________
# core/locator.py

import time
import re
from math import radians, sin, cos, sqrt, atan2
from typing import List, Dict, Optional, Tuple

import requests
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults


Coordinates = Tuple[float, float]


class EmergencyLocatorAgent:
    """
    Agent responsible for:
      - Resolving user location (address → lat/lon or IP → lat/lon)
      - Querying different data sources (Overpass, Nominatim, DuckDuckGo)
      - Returning structured place information
      - Formatting a chat-friendly answer
    """

    def __init__(self) -> None:
        self.user_location: Optional[Coordinates] = None
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        self.user_agent = "EmergencyLocator/1.0 (PharmaBot)"

        # DuckDuckGo tools (last-resort fallback)
        self.search_run = DuckDuckGoSearchRun()
        self.search_results = DuckDuckGoSearchResults()

        print("✅ EmergencyLocatorAgent initialized with DuckDuckGo + OSM")

    # ============================================================
    # Location helpers
    # ============================================================

    def get_location_from_ip(self) -> Optional[Coordinates]:
        """
        Try to infer location from IP address.
        Uses ip-api.com (free IP geolocation).
        """
        try:
            print("🔍 Trying to detect your location via IP...")
            response = requests.get("http://ip-api.com/json/", timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                lat = float(data["lat"])
                lon = float(data["lon"])
                city = data.get("city", "غير معروف")
                country = data.get("country", "غير معروف")

                print(f"✅ Location from IP: {city}, {country} ({lat}, {lon})")
                self.user_location = (lat, lon)
                return lat, lon

            print("❌ IP location status not success")
            return None

        except Exception as e:
            print(f"❌ Error while detecting location from IP: {e}")
            return None

    def get_location_from_address(self, address: str) -> Optional[Coordinates]:
        """
        Geocode a user-provided address using Nominatim.
        """
        try:
            print(f"🔍 Geocoding address: {address!r}")

            params = {"q": address, "format": "json", "limit": 1}
            headers = {"User-Agent": self.user_agent}

            response = requests.get(
                f"{self.nominatim_url}/search",
                params=params,
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                display_name = data[0]["display_name"]

                print(f"✅ Found address: {display_name} ({lat}, {lon})")
                self.user_location = (lat, lon)
                return lat, lon

            print("❌ No results for this address")
            return None

        except Exception as e:
            print(f"❌ Error while geocoding address: {e}")
            return None

    def ensure_location(
        self,
        address: Optional[str] = None,
        use_ip_fallback: bool = True,
    ) -> bool:
        """
        Ensure self.user_location is set:
          - If already set → True
          - Else, try address
          - Else, optionally fall back to IP
        """
        if self.user_location is not None:
            return True

        loc: Optional[Coordinates] = None

        if address:
            loc = self.get_location_from_address(address)
        elif use_ip_fallback:
            loc = self.get_location_from_ip()

        if loc is None:
            print("❌ Could not determine user location (no address/IP).")
            return False

        self.user_location = loc
        return True

    # ============================================================
    # Distance & utilities
    # ============================================================

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Haversine distance in kilometers between two lat/lon points.
        """
        R = 6371.0  # Earth radius in km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _format_address(self, tags: Dict) -> str:
        parts = []
        if "addr:street" in tags:
            parts.append(tags["addr:street"])
        if "addr:housenumber" in tags:
            parts.append(tags["addr:housenumber"])
        if "addr:city" in tags:
            parts.append(tags["addr:city"])
        return ", ".join(parts) if parts else "غير متوفر"

    def get_directions_url(self, dest_lat: float, dest_lon: float) -> str:
        """
        Build a Google Maps directions URL from user_location to dest.
        """
        if not self.user_location:
            return "يجب تحديد موقعك أولاً"
        lat, lon = self.user_location
        return (
            "https://www.google.com/maps/dir/"
            f"?api=1&origin={lat},{lon}&destination={dest_lat},{dest_lon}"
        )

    # ============================================================
    # Nearest pharmacies / hospitals
    # ============================================================

    def find_nearest_pharmacies(self, radius_km: float = 5.0) -> List[Dict]:
        if not self.user_location:
            print("❌ User location is not set before searching pharmacies.")
            return []
        return self._find_places("pharmacy", radius_km)

    def find_nearest_hospitals(self, radius_km: float = 5.0) -> List[Dict]:
        if not self.user_location:
            print("❌ User location is not set before searching hospitals.")
            return []
        return self._find_places("hospital", radius_km)

    def _find_places(self, place_type: str, radius_km: float) -> List[Dict]:
        """
        Try multiple backends in order:
          1. Overpass API
          2. Nominatim search
          3. DuckDuckGo (fallback, general info)
        """
        places = self._try_overpass_api(place_type, radius_km)
        if places:
            return places

        print("⚠️ Overpass failed, falling back to Nominatim...")
        places = self._try_nominatim_search(place_type, radius_km)
        if places:
            return places

        print("⚠️ Nominatim failed, using DuckDuckGo as last resort...")
        return self._try_search_fallback(place_type, radius_km)

    def _try_overpass_api(self, place_type: str, radius_km: float) -> List[Dict]:
        try:
            if not self.user_location:
                return []
            lat, lon = self.user_location
            radius_m = int(radius_km * 1000)

            print(f"\n🔍 [Overpass] Searching for {place_type} within {radius_km} km...")

            if place_type == "pharmacy":
                query = (
                    '[out:json][timeout:30];'
                    f'node["amenity"="pharmacy"](around:{radius_m},{lat},{lon});'
                    "out body;"
                )
            else:
                query = (
                    '[out:json][timeout:30];'
                    f'(node["amenity"="hospital"](around:{radius_m},{lat},{lon});'
                    f' node["amenity"="clinic"](around:{radius_m},{lat},{lon}););'
                    "out body;"
                )

            servers = [
                "https://overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter",
                "https://overpass.openstreetmap.ru/api/interpreter",
            ]

            for server in servers:
                try:
                    response = requests.post(
                        server,
                        data={"data": query},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        timeout=30,
                    )
                    if response.status_code != 200:
                        print(f"⚠️ Overpass server {server} returned {response.status_code}")
                        continue

                    data = response.json()
                    places: List[Dict] = []

                    for element in data.get("elements", []):
                        if "lat" in element and "lon" in element:
                            place_lat = element["lat"]
                            place_lon = element["lon"]
                        elif "center" in element:
                            place_lat = element["center"]["lat"]
                            place_lon = element["center"]["lon"]
                        else:
                            continue

                        distance = self.calculate_distance(lat, lon, place_lat, place_lon)
                        tags = element.get("tags", {})
                        name = tags.get("name", tags.get("operator", "غير معروف"))
                        address = self._format_address(tags)
                        phone = tags.get("phone", tags.get("contact:phone", "غير متوفر"))
                        opening_hours = tags.get("opening_hours", "غير متوفر")

                        places.append(
                            {
                                "name": name,
                                "distance_km": round(distance, 2),
                                "latitude": place_lat,
                                "longitude": place_lon,
                                "address": address,
                                "phone": phone,
                                "opening_hours": opening_hours,
                                "type": tags.get("amenity", place_type),
                            }
                        )

                    places.sort(key=lambda x: x["distance_km"])
                    if places:
                        print(f"✅ [Overpass] Found {len(places)} {place_type}(s)")
                        return places

                except Exception as e:
                    print(f"⚠️ Overpass server {server} failed: {e}")
                    continue

            return []

        except Exception as e:
            print(f"❌ [Overpass] Unexpected error: {e}")
            return []

    def _try_nominatim_search(self, place_type: str, radius_km: float) -> List[Dict]:
        try:
            if not self.user_location:
                return []
            lat, lon = self.user_location

            print(f"\n🔍 [Nominatim] Searching for {place_type}...")

            reverse_url = f"{self.nominatim_url}/reverse"
            params = {"lat": lat, "lon": lon, "format": "json"}
            headers = {"User-Agent": self.user_agent}

            reverse_resp = requests.get(reverse_url, params=params, headers=headers, timeout=10)
            reverse_resp.raise_for_status()
            location_data = reverse_resp.json()

            address = location_data.get("address", {})
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("state", "القاهرة")
            )

            search_term = f"{place_type} in {city}"
            search_params = {
                "q": search_term,
                "format": "json",
                "limit": 50,
                "addressdetails": 1,
            }

            time.sleep(1)  # Be nice to Nominatim
            search_resp = requests.get(
                f"{self.nominatim_url}/search",
                params=search_params,
                headers=headers,
                timeout=10,
            )
            search_resp.raise_for_status()
            results = search_resp.json()

            places: List[Dict] = []
            for result in results:
                place_lat = float(result["lat"])
                place_lon = float(result["lon"])
                distance = self.calculate_distance(lat, lon, place_lat, place_lon)

                if distance <= radius_km:
                    name = result.get("display_name", "").split(",")[0]
                    address_parts = result.get("display_name", "").split(",")[1:3]
                    addr = ", ".join(address_parts).strip() if address_parts else "غير متوفر"

                    places.append(
                        {
                            "name": name,
                            "distance_km": round(distance, 2),
                            "latitude": place_lat,
                            "longitude": place_lon,
                            "address": addr,
                            "phone": "غير متوفر",
                            "opening_hours": "غير متوفر",
                            "type": place_type,
                        }
                    )

            places.sort(key=lambda x: x["distance_km"])
            if places:
                print(f"✅ [Nominatim] Found {len(places)} {place_type}(s)")
            return places

        except Exception as e:
            print(f"❌ [Nominatim] Error: {e}")
            return []

    def _try_search_fallback(self, place_type: str, radius_km: float) -> List[Dict]:
        """
        Last-resort: use DuckDuckGo to get general information (no precise distance).
        """
        try:
            if not self.user_location:
                return []
            lat, lon = self.user_location

            print(f"\n🔍 [DuckDuckGo] Searching for {place_type} via web...")

            reverse_url = f"{self.nominatim_url}/reverse"
            params = {"lat": lat, "lon": lon, "format": "json"}
            headers = {"User-Agent": self.user_agent}

            reverse_resp = requests.get(reverse_url, params=params, headers=headers, timeout=10)
            reverse_resp.raise_for_status()
            location_data = reverse_resp.json()

            address = location_data.get("address", {})
            city = address.get("city") or address.get("town") or "القاهرة"

            if place_type == "pharmacy":
                query = f"pharmacies near {city} location address phone"
            else:
                query = f"hospitals near {city} emergency location address"

            search_result = self.search_run.run(query)

            places = [
                {
                    "name": f"نتائج البحث: {place_type} قريب من {city}",
                    "distance_km": 0.0,
                    "latitude": lat,
                    "longitude": lon,
                    "address": search_result[:200],
                    "phone": "استخدم البحث أعلاه للتفاصيل",
                    "opening_hours": "غير متوفر",
                    "type": place_type,
                }
            ]

            print("💡 [DuckDuckGo] Got generic information from web search")
            return places

        except Exception as e:
            print(f"❌ [DuckDuckGo] Error: {e}")
            return []

    # ============================================================
    # High-level chat helpers
    # ============================================================

    def get_nearest_places(
        self,
        place_kind: str,
        radius_km: float = 5.0,
        address: Optional[str] = None,
        use_ip_fallback: bool = True,
    ) -> List[Dict]:
        """
        Public entry for the router:
          - Makes sure we have a user location.
          - Calls the right place finder based on place_kind.
        """
        if not self.ensure_location(address=address, use_ip_fallback=use_ip_fallback):
            print("❌ ensure_location() failed.")
            return []

        if place_kind == "pharmacy":
            return self.find_nearest_pharmacies(radius_km=radius_km)
        else:
            return self.find_nearest_hospitals(radius_km=radius_km)

    def format_places_for_chat(
        self,
        places: List[Dict],
        place_label: str,
        max_results: int = 3,
    ) -> str:
        """
        Convert a list of places into a human-readable answer for Chat UI.
        """
        if not places:
            return f"❌ لم أستطع العثور على أي {place_label} قريبة بناءً على موقعك الحالي."

        lines = [f"📍 أقرب {place_label} بناءً على موقعك:\n"]

        for i, place in enumerate(places[:max_results], start=1):
            name = place.get("name", "غير معروف")
            distance = place.get("distance_km", 0.0)
            address = place.get("address", "غير متوفر")
            phone = place.get("phone", "غير متوفر")
            opening_hours = place.get("opening_hours", "غير متوفر")

            directions_url = self.get_directions_url(
                place.get("latitude"),
                place.get("longitude"),
            )

            lines.append(
                f"#{i} - {name}\n"
                f"  • المسافة: حوالي {distance} كم\n"
                f"  • العنوان: {address}\n"
                f"  • الهاتف: {phone}\n"
                f"  • مواعيد العمل: {opening_hours}\n"
                f"  • الاتجاهات على الخرائط: {directions_url}\n"
            )

        lines.append(
            "\n⚠️ هذه معلومات تقريبية من مصادر عامة، "
            "يفضل الاتصال بالمكان قبل الذهاب في حالات الطوارئ."
        )
        return "\n".join(lines)


# ============================================================
# Intent detection
# ============================================================

PHARMACY_KEYWORDS = [
    "nearest pharmacy",
    "nearby pharmacy",
    "pharmacy near me",
    "pharmacy from me",
    "pharmacy close to me",
    "صيدلية قريبة",
    "اقرب صيدلية",
]

HOSPITAL_KEYWORDS = [
    "nearest hospital",
    "hospital near me",
    "hospital from me",
    "emergency hospital",
    "مستشفى قريبة",
    "اقرب مستشفى",
]


def detect_locator_intent(user_message: str) -> Optional[str]:
    """
    Very simple intent detector:
      - Returns 'pharmacy' | 'hospital' | None

    We combine:
      1) Exact-ish keywords (English + Arabic)
      2) Simple fuzzy patterns to survive spelling mistakes like 'pharmrcy'
    """
    text = user_message.lower()

    # 1) Direct keyword match
    if any(k in text for k in PHARMACY_KEYWORDS):
        return "pharmacy"
    if any(k in text for k in HOSPITAL_KEYWORDS):
        return "hospital"

    # 2) Simple fuzzy logic:
    #    - If the text contains "pharm" and words like "near", "nearest", "close"
    if "pharm" in text and any(w in text for w in ["near", "nearest", "close", "around", "قريبة", "قريب"]):
        return "pharmacy"

    #    - If the text contains "hospital" (even with extra chars) and "near/nearest"
    #      e.g. "hosptial near me"
    if "hosp" in text and any(w in text for w in ["near", "nearest", "close", "around", "قريبة", "قريب"]):
        return "hospital"

    # 3) Last check with regex for exact words
    if re.search(r"\bpharmacy\b", text):
        return "pharmacy"
    if re.search(r"\bhospital\b", text):
        return "hospital"

    return None
