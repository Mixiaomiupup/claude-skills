import http.server
import urllib.parse
import json
import subprocess
import sys

CODE = None

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global CODE
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if parsed.path == '/callback' and 'code' in params:
            CODE = params['code'][0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'<h1>✅ 授权成功！</h1><p>授权码已获取，请返回终端。</p>'.encode('utf-8'))
            print(f'\n=== GOT CODE: {CODE} ===', flush=True)
            
            # Exchange code for user_access_token
            app_id = 'cli_a928d4672cb89bca'
            app_secret = 'jdkh6VjSqUChWzHBCOUggeWQ8tUy1IMZ'
            
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                'https://open.feishu.cn/open-apis/authen/v1/oidc/access_token',
                '-H', 'Content-Type: application/json',
                '-H', f'Authorization: Bearer {get_app_access_token(app_id, app_secret)}',
                '-d', json.dumps({
                    'grant_type': 'authorization_code',
                    'code': CODE
                })
            ], capture_output=True, text=True)
            
            resp = json.loads(result.stdout)
            print(f'\n=== TOKEN RESPONSE ===', flush=True)
            print(json.dumps(resp, indent=2, ensure_ascii=False), flush=True)
            
            if resp.get('code') == 0:
                token_data = resp['data']
                # Save token to file
                with open('/tmp/feishu_uat.json', 'w') as f:
                    json.dump(token_data, f, indent=2)
                print(f"\n✅ user_access_token saved to /tmp/feishu_uat.json", flush=True)
            
            # Shutdown server after getting token
            import threading
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(400)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>Missing code parameter</h1>')
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

def get_app_access_token(app_id, app_secret):
    result = subprocess.run([
        'curl', '-s', '-X', 'POST',
        'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({'app_id': app_id, 'app_secret': app_secret})
    ], capture_output=True, text=True)
    return json.loads(result.stdout)['app_access_token']

if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', 9876), OAuthHandler)
    print('OAuth callback server listening on http://localhost:9876', flush=True)
    print('Waiting for authorization callback...', flush=True)
    server.serve_forever()
    print('Server stopped.', flush=True)
