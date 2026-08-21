from __future__ import annotations
import json, os, subprocess, sys, time, unittest, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PORT=18991

def req(path,method='GET',data=None,headers=None):
    body=None if data is None else json.dumps(data).encode()
    h={'Content-Type':'application/json',**(headers or {})}
    with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',data=body,method=method,headers=h),timeout=8) as r:return json.loads(r.read().decode())

class StaticRegression(unittest.TestCase):
    def test_arabic_normalization(self):
        sys.path.insert(0,str(ROOT));from platform_services import normalize_ar
        self.assertEqual(normalize_ar('مُحَمَّدٌ'),normalize_ar('محمد'))
        self.assertEqual(normalize_ar('إبراهيم'),normalize_ar('ابراهيم'))
    def test_reader_modules_present(self):
        html=(ROOT/'reader.html').read_text(encoding='utf-8')
        for x in ('reader-futurist.js','reader-research-completion.js','reader-nextgen.js','reader-player-i18n.js','reader-research-pro.js'):self.assertIn(x,html)
    def test_media_modules_present(self):
        html=(ROOT/'media.html').read_text(encoding='utf-8')
        for x in ('universal-player.js','adaptive-media.js','media-adaptive-hook.js','media-nextgen.js','media-pro.js'):self.assertIn(x,html)
    def test_no_4k_upscale(self):
        s=(ROOT/'scripts'/'build_adaptive_media.py').read_text(encoding='utf-8');self.assertIn("if sh and hh>sh:continue",s)

class RuntimeRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env={**os.environ,'PM_PORT':str(PORT),'PM_HOST':'127.0.0.1','PM_MEDIA_SYNC_ON_START':'0','PM_EPUB_CONVERT_ON_START':'0'}
        cls.p=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                if req('/api/ready').get('ok'):return
            except Exception:time.sleep(.2)
        raise RuntimeError('server did not start')
    @classmethod
    def tearDownClass(cls):
        cls.p.terminate()
        try:cls.p.wait(3)
        except:cls.p.kill()
    def test_ready(self):self.assertTrue(req('/api/ready')['ok'])
    def test_search(self):
        r=req('/api/search?q=محمد');self.assertTrue(r['ok']);self.assertIn('results',r)
    def test_account_sync(self):
        email=f'test-{int(time.time()*1000)}@example.invalid';password='Regression-Only-12345'
        a=req('/api/account/register','POST',{'email':email,'password':password});self.assertTrue(a['ok']);token=a['token']
        h={'Authorization':'Bearer '+token};s=req('/api/sync','POST',{'items':[{'scope':'reader','key':'test','payload':{'page':3}}]},h);self.assertTrue(s['ok'])
        g=req('/api/sync',headers=h);self.assertTrue(g['ok']);self.assertTrue(any(x['key']=='test' for x in g['items']))
    def test_telemetry(self):
        self.assertTrue(req('/api/telemetry','POST',{'event':'regression','startupMs':1})['ok']);self.assertTrue(req('/api/telemetry/summary')['ok'])

if __name__=='__main__':unittest.main(verbosity=2)
