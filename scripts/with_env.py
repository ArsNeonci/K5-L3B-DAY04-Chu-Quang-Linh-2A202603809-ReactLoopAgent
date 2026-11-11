"""Nạp cấu hình .env an toàn rồi chạy CLI, không execute nội dung .env.

Ví dụ: python scripts/with_env.py evals/run_evals.py --output eval_before.json
"""
import os
from pathlib import Path
import runpy
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    'PROVIDER', 'MODEL', 'JUDGE_PROVIDER', 'JUDGE_MODEL',
    'OPENAI_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY',
    'OPENROUTER_API_KEY', 'STATUS_USER_AGENT',
}


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Dùng: python scripts/with_env.py <script.py> [arguments]')
    env_path = ROOT / '.env'
    if env_path.exists():
        for number, raw in enumerate(env_path.read_text(encoding='utf-8-sig').splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            name, separator, raw_value = line.removeprefix('export ').partition('=')
            if not separator or name.strip() not in ALLOWED:
                continue
            try:
                parts = shlex.split(raw_value, comments=True)
            except ValueError:
                raise SystemExit(f'.env dòng {number}: dấu nháy không hợp lệ.') from None
            os.environ[name.strip()] = ' '.join(parts)

    target = (ROOT / sys.argv[1]).resolve()
    if not target.is_relative_to(ROOT) or target.suffix != '.py' or not target.is_file():
        raise SystemExit('Script phải là file .py trong repo.')
    sys.argv = [str(target), *sys.argv[2:]]
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(target.parent))
    runpy.run_path(str(target), run_name='__main__')


if __name__ == '__main__':
    main()
