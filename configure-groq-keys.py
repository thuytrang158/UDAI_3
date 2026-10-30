"""Interactively store up to six Groq API keys in the shared .env file."""

from getpass import getpass
from pathlib import Path
import re

env_path = Path(__file__).resolve().parent / ".env"
lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
values = {}
for line in lines:
    match = re.match(r"^\s*(?:export\s+)?(GROQ_API_KEY_[1-6])\s*=\s*(.*)$", line)
    if match:
        values[match.group(1)] = match.group(2).strip().strip("\"'")

for index in range(1, 7):
    name = f"GROQ_API_KEY_{index}"
    while True:
        value = getpass(f"Nhập {name} (Enter để giữ nguyên): ").strip()
        if not value:
            break
        if not re.fullmatch(r"gsk_[A-Za-z0-9_-]+", value) or value.find("gsk_", 4) != -1:
            print("Khóa không đúng định dạng. Hãy dán một khóa Groq duy nhất.")
            continue
        if value in values.values() and value != values.get(name):
            print("Khóa này đã được nhập ở dòng trước; mỗi biến cần một khóa riêng.")
            continue
        values[name] = value
        break

for index in range(1, 7):
    name = f"GROQ_API_KEY_{index}"
    assignment = f"{name}={values.get(name, '')}"
    for line_index, line in enumerate(lines):
        if re.match(rf"^\s*(?:export\s+)?{name}\s*=", line):
            lines[line_index] = assignment
            break
    else:
        lines.append(assignment)

env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
env_path.chmod(0o600)
print(f"Đã lưu {sum(bool(values.get(f'GROQ_API_KEY_{index}')) for index in range(1, 7))} khóa vào {env_path}; giá trị khóa không được hiển thị.")
