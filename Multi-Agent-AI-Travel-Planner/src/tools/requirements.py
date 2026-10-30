"""LLM-backed extraction and Pydantic validation for trip requirements."""
import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_llm, GROQ_API_KEYS, GROQ_MODEL, OLLAMA_MODEL
from src.schemas import ExtractedTripRequirements


class RequirementsOutputError(ValueError):
    """The model response could not be validated after a repair attempt."""


def requirements_model_info() -> dict[str, str]:
    return {"provider": "Groq" if GROQ_API_KEYS else "Ollama",
            "model": GROQ_MODEL if GROQ_API_KEYS else OLLAMA_MODEL}


def extract_trip_requirements(text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Extract only requirements stated by the traveler and validate them."""
    llm = get_llm(json_mode=True, num_predict=900, temperature=0.1)
    messages = [
        SystemMessage(content=(
            "Bạn là trợ lý thu thập yêu cầu chuyến đi. Trích xuất thông tin người dùng nêu rõ; "
            "không tự đoán giá trị còn thiếu. Các trường không được đề cập phải là null; "
            "không ghi đè điểm đến trong biểu mẫu nếu mô tả không nêu điểm đến mới. "
            "destination chỉ gồm tên thành phố hoặc khu vực, không thêm quốc gia. "
            "Một điểm tham quan được yêu cầu (ví dụ ATK Định Hóa) phải vào required_places, "
            "KHÔNG thay destination của biểu mẫu thành tên điểm tham quan. "
            "Phân biệt muốn đến (required_places), không muốn đến (excluded_places), "
            "sở thích mềm (preferences) và nhịp độ (pace: relaxed/balanced/active). "
            "Không bỏ sót tên địa điểm cụ thể. Giữ nguyên tên người dùng để đối chiếu nguồn. "
            "Chuẩn hóa transportation_preference về Cab and Metro, Only Metro / Public Transit "
            "(xe buýt/tàu điện), hoặc Private Cab Only (taxi riêng) khi phù hợp. "
            "Trích xuất interests từ các trải nghiệm được yêu cầu, dùng đúng các giá trị trong schema. "
            "Giữ nguyên đơn vị ngân sách, không coi ngân sách cả chuyến là mỗi ngày mỗi người. "
            "Trả duy nhất JSON object theo schema: "
            + json.dumps(ExtractedTripRequirements.model_json_schema(), ensure_ascii=False)
        )),
        HumanMessage(content=(
            "Biểu mẫu hiện tại (chỉ làm ngữ cảnh): "
            + json.dumps(context or {}, ensure_ascii=False)
            + "\nMô tả mới của người dùng:\n" + text
        )),
    ]
    for attempt in range(2):
        response = llm.invoke(messages)
        try:
            content = response.content
            if isinstance(content, list):
                content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
            raw = re.sub(r"<think>.*?</think>", "", str(content), flags=re.DOTALL).strip()
            start, end = raw.find("{"), raw.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("Mô hình không trả về JSON hợp lệ.")
            validated = ExtractedTripRequirements.model_validate(json.loads(raw[start:end + 1]))
            return validated.model_dump(exclude_none=True)
        except (ValueError, TypeError) as error:
            if attempt:
                raise RequirementsOutputError("Kết quả AI không đúng schema yêu cầu chuyến đi.") from error
            messages.append(HumanMessage(content=(
                "Kết quả vừa rồi không đúng schema. Hãy trích xuất lại từ mô tả ban đầu, "
                "dùng null cho thông tin chưa biết, số ngày phải từ 1 đến 30 và số người ít nhất 1."
            )))
