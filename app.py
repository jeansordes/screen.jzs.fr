#!/usr/bin/env python3
import base64, hashlib, hmac, json, os, secrets, sqlite3
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'screen.db'
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change-me')
SECRET = os.environ.get('SESSION_SECRET', 'prototype-only-change-this')

DEFAULTS = {
 'venue_name':'Votre lieu', 'tagline':'Bienvenue — découvrez ce qui se passe aujourd’hui',
 'primary_color':'#E94057', 'rotation_seconds':'9',
 'info_title':'À propos de nous', 'info_body':'Ajoutez ici les informations pratiques : horaires, accueil, Wi-Fi, accès et contact.'
}

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
 DB.parent.mkdir(exist_ok=True)
 with db() as c:
  c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS slides (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, image TEXT DEFAULT "", cta TEXT DEFAULT "", active INTEGER NOT NULL DEFAULT 1, position INTEGER NOT NULL DEFAULT 0)')
  for k,v in DEFAULTS.items(): c.execute('INSERT OR IGNORE INTO settings VALUES (?,?)',(k,v))
  if not c.execute('SELECT 1 FROM slides LIMIT 1').fetchone():
   c.executemany('INSERT INTO slides(title,body,image,cta,position) VALUES (?,?,?,?,?)', [
    ('Bienvenue','Un espace pour apprendre, créer et rencontrer des personnes inspirantes.','', 'Découvrir le lieu',1),
    ('Événement à venir','Ajoutez vos ateliers, conférences, dates et informations utiles ici.','', 'Voir le programme',2),
    ('Besoin d’aide ?','Notre équipe d’accueil est là pour vous orienter.','', 'Contacter l’accueil',3)])

def settings():
 with db() as c: return {r['key']:r['value'] for r in c.execute('SELECT * FROM settings')}
def slides():
 with db() as c: return [dict(r) for r in c.execute('SELECT * FROM slides WHERE active=1 ORDER BY position,id')]
def sign(text): return hmac.new(SECRET.encode(), text.encode(), hashlib.sha256).hexdigest()
def logged_in(handler):
 cookie=SimpleCookie(handler.headers.get('Cookie')); v=cookie.get('screen_admin')
 if not v: return False
 try:
  raw=base64.urlsafe_b64decode(v.value.encode()).decode(); payload,sig=raw.rsplit('.',1)
  return hmac.compare_digest(sig,sign(payload)) and json.loads(payload).get('role')=='admin'
 except Exception: return False

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT/'static'),**kw)
 def send_json(self, obj, status=200):
  data=json.dumps(obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
 def body(self):
  try: return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
  except Exception: return {}
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/api/public': return self.send_json({'settings':settings(),'slides':slides()})
  if path=='/api/admin':
   if not logged_in(self): return self.send_json({'error':'Non authentifié'},401)
   with db() as c: allslides=[dict(x) for x in c.execute('SELECT * FROM slides ORDER BY position,id')]
   return self.send_json({'settings':settings(),'slides':allslides})
  if path=='/admin': self.path='/admin.html'
  elif path=='/': self.path='/index.html'
  return super().do_GET()
 def do_POST(self):
  path=urlparse(self.path).path; data=self.body()
  if path=='/api/login':
   if not hmac.compare_digest(str(data.get('password','')),ADMIN_PASSWORD): return self.send_json({'error':'Mot de passe incorrect'},401)
   payload=json.dumps({'role':'admin'},separators=(',',':')); token=base64.urlsafe_b64encode((payload+'.'+sign(payload)).encode()).decode()
   self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Set-Cookie',f'screen_admin={token}; HttpOnly; Secure; SameSite=Strict; Path=/'); self.end_headers(); return self.wfile.write(b'{"ok":true}')
  if not logged_in(self): return self.send_json({'error':'Non authentifié'},401)
  if path=='/api/logout':
   self.send_response(200); self.send_header('Set-Cookie','screen_admin=; Max-Age=0; Path=/'); self.end_headers(); return
  if path=='/api/settings':
   allowed=set(DEFAULTS)
   with db() as c:
    for k,v in data.items():
     if k in allowed: c.execute('INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,str(v)))
   return self.send_json({'ok':True})
  if path=='/api/slides':
   with db() as c:
    if data.get('delete'):
     c.execute('DELETE FROM slides WHERE id=?',(int(data['delete']),)); return self.send_json({'ok':True})
    fields=(str(data.get('title','')).strip(),str(data.get('body','')).strip(),str(data.get('image','')).strip(),str(data.get('cta','')).strip(),int(bool(data.get('active',True))),int(data.get('position',0)))
    if not fields[0] or not fields[1]: return self.send_json({'error':'Titre et texte requis'},400)
    if data.get('id'): c.execute('UPDATE slides SET title=?,body=?,image=?,cta=?,active=?,position=? WHERE id=?',fields+(int(data['id']),))
    else: c.execute('INSERT INTO slides(title,body,image,cta,active,position) VALUES (?,?,?,?,?,?)',fields)
   return self.send_json({'ok':True})
  return self.send_json({'error':'Introuvable'},404)

if __name__=='__main__':
 init_db(); port=int(os.environ.get('PORT','8099')); print(f'Accueil écran prêt sur http://127.0.0.1:{port}')
 ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
