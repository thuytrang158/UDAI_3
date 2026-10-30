"""
AI accommodation suggestions using the configured model.
Estimated rates and availability must be checked with the booking provider.
"""
import json
import re
import urllib.parse
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from src.config import get_llm


def extract_json_object(raw_text: str) -> dict:
    """
    Strips reasoning tokens, markdown codeblocks, and isolates top-level JSON object.
    """
    # 1. Remove <think>...</think> reasoning tags
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

    # 2. Extract content from markdown code fences if present
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        # 3. Find outermost JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    return json.loads(text)


def search_accommodations(
    destination: str,
    stay_type: str = "Hotel",
    max_budget: int = 5000,
    preferred_area: str = "City Center",
    trip_context: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Prompts Ollama to dynamically discover real accommodations matching
    the user's destination, property type, budget ceiling, and neighborhood.
    """
    clean_dest = (destination or "Bengaluru").strip().title()
    clean_type = (stay_type or "Hotel").strip()
    clean_area = (preferred_area or "City Center").strip()

    print(f"\n[AI Stay Agent] Querying model for accommodations in {clean_dest}...")
    print(f"                       • Type    : {clean_type}")
    print(f"                       • Budget  : <= ₹{max_budget:,} INR")
    print(f"                       • Area    : {clean_area}")

    system_prompt = (
        "You are a travel accommodation recommendation assistant. Suggest up to five known authentic properties "
        "that match the requested parameters. Do not invent property names. Return an empty list if no known property fits. "
        "Rates are estimates, not live quotes; availability must be verified with the booking provider."
    )

    user_prompt = f"""
Search parameters:
- Destination: {clean_dest}
- Required Property Type: {clean_type} (Every recommendation MUST be a {clean_type})
- Nightly Budget Limit: At or below ₹{max_budget:,} INR
- Location / Neighborhood: In or near {clean_area}

Output a STRICT JSON object with this EXACT structure:
{{
  "accommodations": [
    {{
      "name": "Actual Real Property Name",
      "stay_type": "{clean_type}",
      "area_type": "{clean_area}",
      "price_per_night": 2400,
      "rating": 4.3,
      "highlights": "Why this property fits the criteria"
    }}
  ]
}}

STRICT RULES:
1. Every property MUST be a {clean_type}. Do NOT suggest other property types.
2. Every price_per_night MUST be an integer at or below ₹{max_budget:,} INR.
3. Every property MUST be situated in or adjacent to {clean_area}, {clean_dest}.
4. Return up to 5 distinct known properties under the budget limit. Never pad the list with invented properties.
5. Return ONLY the valid JSON object starting with '{{' and ending with '}}'.
"""

    accommodations = []
    if trip_context:
        user_prompt += (
            "\nTrip context: " + json.dumps(trip_context, ensure_ascii=False)
            + "\nExplain why each stay fits the actual selected stops, travel pace and accommodation preferences. "
            "Treat the selected property type, area and budget as explicit current choices. "
            "Do not assume all travelers stay in the city center when their itinerary visits rural districts."
        )
    try:
        # Invoke Ollama in native JSON mode with 1200 token limit
        llm = get_llm(json_mode=True, num_predict=1200, temperature=0.4)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        data = extract_json_object(response.content)
        accommodations = data.get("accommodations", [])
        print(f"[AI Stay Agent] Generated {len(accommodations)} suggestions to verify.")

    except Exception as exc:
        print(f"[AI Stay Agent] Model call or JSON validation failed ({type(exc).__name__}).")

    if not accommodations:
        raise RuntimeError("Stay Agent chưa trả về chỗ ở phù hợp; vui lòng thử lại model.")

    # Post-process: attach live Booking.com search links
    results = []
    for item in accommodations:
        name = item.get("name", f"{clean_type} in {clean_dest}")
        query = urllib.parse.quote_plus(f"{name} {clean_dest}")
        booking_url = f"https://www.booking.com/searchresults.html?ss={query}"

        # Ensure price is an integer within budget
        raw_price = item.get("price_per_night", max_budget)
        try:
            price_val = int(re.sub(r"[^\d]", "", str(raw_price)))
        except ValueError:
            price_val = max_budget
        if price_val <= 0 or price_val > max_budget:
            continue

        results.append({
            "name": name,
            "stay_type": item.get("stay_type", clean_type),
            "area_type": item.get("area_type", clean_area),
            "price_per_night": price_val,
            "rating": float(item.get("rating", 4.3)),
            "latitude": None,
            "longitude": None,
            "booking_url": booking_url,
            "tag": f"{item.get('stay_type', clean_type)} • {item.get('area_type', clean_area)}",
            "recommendation_reason": str(item.get("highlights", "")),
            "disclaimer": "AI suggestion; estimated rates and availability must be verified on the booking provider."
        })

    if not results:
        raise RuntimeError("Không có gợi ý AI nào trong giới hạn ngân sách đã chọn.")
    return results
