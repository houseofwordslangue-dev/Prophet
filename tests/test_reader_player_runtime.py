from __future__ import annotations
import json, os, subprocess, sys, time, unittest, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PORT=18991

def req(path,method='GET',data=None,headers=None):
    body=None if data is None else json.dumps(data).encode()
    h={'Content-Type':'application/json',**(headers or {})}
    # HTTP request targets must be ASCII. Preserve URL separators while
    # percent-encoding Arabic and other non-ASCII query/path characters.
    safe_path=urllib.parse.quote(path,safe='/?=&%:+')
    with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{PORT}{safe_path}',data=body,method=method,headers=h),timeout=8) as r:return json.loads(r.read().decode())

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
    def test_platform_runtime_present(self):
        menu=(ROOT/'assets'/'site-menu.js').read_text(encoding='utf-8');self.assertIn('platform-runtime.js',menu);self.assertIn('cache-telemetry.js',menu)
    def test_no_4k_upscale_and_dash(self):
        s=(ROOT/'scripts'/'build_adaptive_media.py').read_text(encoding='utf-8');self.assertIn("if not sh or p[2]<=sh",s);self.assertIn("'-f','dash'",s);self.assertIn("'2160p'",s)
    def test_real_asset_pipelines_exist(self):
        for p in ('build_mirror_manifest.py','replicate_assets.py','build_ocr_coordinates.py','build_timed_transcripts.py','prepare_reader_player_assets.py'):self.assertTrue((ROOT/'scripts'/p).exists(),p)
        o=(ROOT/'scripts'/'build_ocr_coordinates.py').read_text(encoding='utf-8');self.assertIn('pytesseract',o);self.assertIn("'coordinateUnit':'percent'",o)
        t=(ROOT/'scripts'/'build_timed_transcripts.py').read_text(encoding='utf-8');self.assertIn('word_timestamps=True',t);self.assertIn("'.vtt'",t)
    def test_mirror_pipeline_never_invents_urls(self):
        s=(ROOT/'scripts'/'replicate_assets.py').read_text(encoding='utf-8');self.assertIn('URLs are recorded only after successful upload',s);self.assertIn('PM_MIRROR_',s)
    def test_service_worker_mirror_and_cache_metrics(self):
        s=(ROOT/'service-worker.js').read_text(encoding='utf-8');self.assertIn('mirrorFallback',s);self.assertIn('CACHE_METRIC',s);self.assertIn('cache_hit',s)

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
        r=req('/api/search?q=محمد');self.assertTrue(r['ok']);self.assertIn('results',r);self.assertIn('elapsedMs',r)
    def test_account_sync(self):
        email=f'test-{int(time.time()*1000)}@example.invalid';password='Regression-Only-12345'
        a=req('/api/account/register','POST',{'email':email,'password':password});self.assertTrue(a['ok']);token=a['token']
        h={'Authorization':'Bearer '+token};s=req('/api/sync','POST',{'items':[{'scope':'reader','key':'test','payload':{'page':3}}]},h);self.assertTrue(s['ok'])
        g=req('/api/sync',headers=h);self.assertTrue(g['ok']);self.assertTrue(any(x['key']=='test' for x in g['items']))
    def test_telemetry(self):
        self.assertTrue(req('/api/telemetry','POST',{'event':'regression','startupMs':1})['ok']);j=req('/api/telemetry/summary');self.assertTrue(j['ok']);self.assertIn('byEvent',j)

if __name__=='__main__':unittest.main(verbosity=2)
