#!/usr/bin/env python3
from __future__ import annotations
import json, re, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CAT=ROOT/'data'/'imported_media.json'; CACHE=ROOT/'media-cache'; OUT=ROOT/'data'/'transcripts'; OUT.mkdir(parents=True,exist_ok=True)

def safe(s):return re.sub(r'[^A-Za-z0-9_.-]+','_',str(s))[:160]
def media_file(mid):
 stem=safe(mid)
 for p in CACHE.glob(stem+'.*'):
  if p.is_file() and p.suffix.lower() in {'.mp3','.m4a','.aac','.ogg','.wav','.flac','.mp4','.mkv','.webm','.mov','.m4v'}:return p
 return None
def ts(sec):
 ms=max(0,int(sec*1000));h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000;s=ms//1000;ms%=1000;return f'{h:02d}:{m:02d}:{s:02d}.{ms:03d}'
def build(mid,src,lang=None):
 try:from faster_whisper import WhisperModel
 except ImportError:raise RuntimeError('faster-whisper is required: pip install faster-whisper')
 model_name='small' if not lang or lang.startswith(('ar','fr')) else 'base';model=WhisperModel(model_name,device='auto',compute_type='int8')
 segments,info=model.transcribe(str(src),language=(lang or None),word_timestamps=True,vad_filter=True)
 words=[];segs=[];vtt=['WEBVTT','']
 for i,seg in enumerate(segments,1):
  text=(seg.text or '').strip();entry={'start':round(seg.start,3),'end':round(seg.end,3),'text':text,'words':[]}
  for w in seg.words or []:
   z={'start':round(w.start or seg.start,3),'end':round(w.end or seg.end,3),'text':(w.word or '').strip()};entry['words'].append(z);words.append(z)
  segs.append(entry);vtt.extend([str(i),f'{ts(seg.start)} --> {ts(seg.end)}',text,''])
 out={'id':mid,'generatedAt':int(time.time()),'language':getattr(info,'language',lang),'languageProbability':round(float(getattr(info,'language_probability',0) or 0),4),'method':'faster-whisper-word-timestamps','source':str(src.relative_to(ROOT)),'segments':segs,'words':words}
 (OUT/(safe(mid)+'.json')).write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8');(OUT/(safe(mid)+'.vtt')).write_text('\n'.join(vtt),encoding='utf-8');return len(words)
def main():
 data=json.loads(CAT.read_text(encoding='utf-8'));report={'processed':0,'generated':0,'missingLocalMedia':[],'failed':[]}
 for x in data.get('items',[]):
  mid=str(x.get('id') or '');src=media_file(mid)
  if not src:report['missingLocalMedia'].append(mid);continue
  report['processed']+=1
  try:build(mid,src,x.get('language'));report['generated']+=1
  except Exception as e:report['failed'].append({'id':mid,'error':str(e)})
 (OUT/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
