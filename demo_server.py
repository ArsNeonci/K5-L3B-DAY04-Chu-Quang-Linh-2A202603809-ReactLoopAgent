"""Local demo UI. Run via: python scripts/with_env.py demo_server.py."""
import argparse
import json
import os
from pathlib import Path
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time

from agent import run_agent
from bonus.tools import BonusTools
from providers import Provider
from status_tools import StatusTools

ROOT = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)


class DemoHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send_json(self, code, value):
        data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/api/config':
            self.send_json(200, {'token': TOKEN, 'provider': os.getenv('PROVIDER', 'openai'),
                                'model': os.getenv('MODEL', ''),
                                'key_ready': bool(os.getenv({'openai': 'OPENAI_API_KEY',
                                    'gemini': 'GEMINI_API_KEY', 'anthropic': 'ANTHROPIC_API_KEY',
                                    'openrouter': 'OPENROUTER_API_KEY'}.get(os.getenv('PROVIDER', 'openai'), ''))),
                                'replay_ready': (ROOT / 'eval_after.json').is_file()})
        elif self.path in ('/', '/app.js', '/style.css'):
            name = 'index.html' if self.path == '/' else self.path[1:]
            data = (ROOT / 'demo' / name).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', {'index.html': 'text/html', 'app.js': 'text/javascript',
                                             'style.css': 'text/css'}[name] + '; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_json(404, {'error': 'Không tìm thấy.'})

    def do_POST(self):
        if self.path != '/api/run':
            return self.send_json(404, {'error': 'Không tìm thấy.'})
        if self.headers.get('X-Demo-Token') != TOKEN:
            return self.send_json(403, {'error': 'Hãy tải lại trang demo.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 20000:
                raise ValueError('Yêu cầu quá lớn hoặc rỗng.')
            args = json.loads(self.rfile.read(size))
            if not isinstance(args, dict):
                raise ValueError('Yêu cầu phải là JSON object.')
            source = args.get('source', 'snapshot')
            if source not in ('snapshot', 'live', 'replay'):
                raise ValueError('Chế độ không hợp lệ.')
            steps = args.get('max_steps', 16)
            if type(steps) is not int or not 1 <= steps <= 32:
                raise ValueError('Số bước phải từ 1 đến 32.')
            question = args.get('question', '')
            if not isinstance(question, str) or not question.strip() or len(question) > 5000:
                raise ValueError('Nhập câu hỏi từ 1 đến 5000 ký tự.')
            if type(args.get('bonus', False)) is not bool:
                raise ValueError('Lựa chọn bonus không hợp lệ.')
            if source == 'replay':
                report = json.loads((ROOT / 'eval_after.json').read_text(encoding='utf-8'))
                case = next(c for c in report['cases'] if c['id'] == 'H1')
                result = case['result']
            else:
                provider = Provider(os.getenv('PROVIDER', 'openai'), os.getenv('MODEL'))
                tools = BonusTools(source) if args.get('bonus') else StatusTools(source)
        except (ValueError, OSError, KeyError, StopIteration) as exc:
            return self.send_json(400, {'error': str(exc) if isinstance(exc, ValueError)
                                       else 'Không đọc được report phát lại H1.'})
        self.send_response(200)
        self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()

        def emit(value):
            self.wfile.write((json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8'))
            self.wfile.flush()

        try:
            emit({'event': 'started', 'mode': source, 'question': case['question'] if source == 'replay' else question,
                  'provider': report['config']['provider'] if source == 'replay' else provider.name,
                  'model': report['config']['model'] if source == 'replay' else provider.model})
            if source == 'replay':
                for event in result['trace']:
                    emit(event)
                    time.sleep(0.25)
            else:
                result = run_agent(question, provider, tools, max_steps=steps, on_event=emit)
            emit({'event': 'result', 'result': result})
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            try:
                emit({'event': 'result', 'result': {'status': 'error', 'answer': '',
                     'error': 'Demo gặp lỗi. Kiểm tra cấu hình hoặc chạy CLI để đối chiếu.',
                     'trace': [], 'usage': []}})
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description='Giao diện demo Status Investigation Agent')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), DemoHandler)
    print(f'Demo: http://127.0.0.1:{server.server_port} (Ctrl+C để dừng)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
