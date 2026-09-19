"""Loopback-only prototype host. Audio goes directly to AssemblyAI only after consent.
No inventory reaches this server. The permanent provider key stays in its environment.
"""
from __future__ import annotations
import argparse, hashlib, json, os, secrets, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'web'
TOKEN=secrets.token_urlsafe(32)
COUNTER=0
LAST=0.0
LOCK=threading.Lock()

def provider_token(key: str) -> dict:
    request=urllib.request.Request('https://streaming.assemblyai.com/v3/token?expires_in_seconds=60&max_session_duration_seconds=120',headers={'Authorization':key,'Accept':'application/json'})
    with urllib.request.urlopen(request,timeout=15) as r:
        raw=r.read(8193)
    if len(raw)>8192:raise ValueError('Oversized token response')
    obj=json.loads(raw)
    if not isinstance(obj.get('token'),str) or not 10<=len(obj['token'])<=4096:raise ValueError('Invalid token response')
    return {'token':obj['token'],'max_session_duration_seconds':120,'speech_model':'universal-3-5-pro'}

def enabled() -> bool:
    return os.getenv('ALLOW_ASSEMBLYAI')=='true' and bool(os.getenv('ASSEMBLYAI_API_KEY'))

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass  # No transcript, token or query logging.
    def send(self,code,data,mime='application/json'):
        body=json.dumps(data).encode() if not isinstance(data,bytes) else data
        self.send_response(code);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self' wss://streaming.assemblyai.com; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(body)
    def origin(self):return f'http://127.0.0.1:{self.server.server_port}'
    def do_GET(self):
        if self.headers.get('Host')!=f'127.0.0.1:{self.server.server_port}':return self.send(403,{'error':'Use the printed loopback URL'})
        if self.path=='/api/config':return self.send(200,{'csrf':TOKEN,'voice_enabled':enabled(),'provider_executed':False})
        paths={'/audio-readback.mjs':('audio-readback.mjs','text/javascript'),'/':('index.html','text/html; charset=utf-8'),'/app.mjs':('app.mjs','text/javascript'),'/speaker-check.mjs':('speaker-check.mjs','text/javascript'),'/voice-audit.mjs':('voice-audit.mjs','text/javascript'),'/core.mjs':('core.mjs','text/javascript'),'/capture-gate.mjs':('capture-gate.mjs','text/javascript'),'/voice-runtime.mjs':('voice-runtime.mjs','text/javascript'),'/audio-worklet.js':('audio-worklet.js','text/javascript'),'/style.css':('style.css','text/css'),'/readback.mjs':('readback.mjs','text/javascript'),'/streaming-request.mjs':('streaming-request.mjs','text/javascript')}
        # Serve only manifest-listed public audio vocabulary, never arbitrary files.
        if self.path.startswith('/voice/v1/'):
            name=self.path.removeprefix('/voice/v1/')
            directory=ROOT/'voice/v1'
            if name=='manifest.json' and (directory/name).is_file():
                return self.send(200,(directory/name).read_bytes(),'application/json')
            if name.endswith('.mp3') and name[:-4].replace('-','').isalnum() and name==name.lower():
                try:
                    manifest=json.loads((directory/'manifest.json').read_text())
                    item=manifest['clips'].get(name[:-4])
                    if item and item['path']==self.path and (directory/name).is_file():
                        return self.send(200,(directory/name).read_bytes(),'audio/mpeg')
                except (OSError,ValueError,KeyError):pass
            return self.send(404,{'error':'Not found'})
        if self.path not in paths:return self.send(404,{'error':'Not found'})
        path,mime=paths[self.path];return self.send(200,(ROOT/path).read_bytes(),mime)
    def do_POST(self):
        global COUNTER,LAST
        if self.path!='/api/token':return self.send(404,{'error':'Not found'})
        if self.headers.get('Host')!=f'127.0.0.1:{self.server.server_port}' or self.headers.get('Origin')!=self.origin() or not secrets.compare_digest(self.headers.get('X-Recount-Token',''),TOKEN):return self.send(403,{'error':'Invalid local origin/token'})
        if self.headers.get('Content-Type')!='application/json':return self.send(415,{'error':'JSON required'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=256:raise ValueError()
            body=json.loads(self.rfile.read(length))
            if body!={'consent':True}:raise ValueError()
        except (ValueError,json.JSONDecodeError):return self.send(400,{'error':'Explicit audio-transfer consent required'})
        if not enabled():return self.send(503,{'error':'Live transcription is not configured. Text mode remains available.'})
        with LOCK:
            if COUNTER>=3 or time.monotonic()-LAST<20:return self.send(429,{'error':'Prototype session limit reached; no further provider request made'})
            COUNTER+=1;LAST=time.monotonic()
        try:return self.send(200,provider_token(os.environ['ASSEMBLYAI_API_KEY']))
        except Exception:return self.send(502,{'error':'Provider token request failed. Check the local configuration; no secret is returned.'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);a=p.parse_args()
    if not 1024<=a.port<=65535:p.error('Use a port from 1024 to 65535')
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'Recount: http://127.0.0.1:{a.port}',flush=True)
    print('Voice configured: '+str(enabled())+'. No provider request has been made.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
