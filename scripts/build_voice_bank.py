"""Build-time stock neural voice. No user audio/text, keys or inference service.
Only generated MP3s and a content manifest enter the website, never model weights.
"""
from pathlib import Path
import hashlib,json,subprocess,tempfile,urllib.request,wave
import numpy as np
from kokoro_onnx import Kokoro
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'web/voice/v1';OUT.mkdir(parents=True,exist_ok=True)
PHRASES={
 'speaker-test':'This is Recount. If you can hear this voice, tap I heard it.',
 'rice':'Rice.', 'beans':'Beans.', 'oil':'Cooking oil.', 'soap':'Soap.',
 'bags':'Bags.', 'bottles':'Bottles.', 'bars':'Bars.',
 'and':'And.', 'say-confirm':'Say confirm', 'or-correct':'or correct the count.',
 'saved':'Saved.', 'next-item':'What is the next item?',
 'check-item-unit':'Check the item and unit carefully.',
 'how-many-bags':'How many bags of', 'how-many-bottles':'How many bottles of', 'how-many-bars':'How many bars of',
 'which-unit':'Which unit?', 'say-bags':'Say bags.', 'say-bottles':'Say bottles.', 'say-bars':'Say bars.',
 'correcting':'Correcting', 'new-number-unit':'Say the new number and unit. Nothing is ready to save.',
 'confirmation-said':'The confirmation said', 'readback-is':'but the read-back is', 'nothing-saved':'Nothing was saved.',
 'confirm-unclear':'Confirmation unclear. Nothing saved. Repeat the confirmation number, or review it on screen.',
 'no-complete-count':'Nothing complete is ready to save. Repeat the full item, number and unit first.',
 'count-unclear':'That count was unclear. Please repeat the full item, number and unit.',
 'audio-hold':'Audio needs review. Restate the full item, number and unit, or discard the uncertain draft.',
 'discarded':'Draft discarded. Confirmed counts and other reviews are unchanged.',
 'discard-unclear':'Cancellation was unclear. Say discard again, or stop audio and use Discard draft.',
 'wrong-unit':'That unit is not supported for this item. I will not guess pack conversions. Read the required unit on screen.',
 'one-item':'Count one catalogue item at a time, using a whole number and its unit.',
 'uncertain-full-count':'The earlier count is uncertain. Repeat the complete item, number and unit, or discard it.',
 'which-item':'Which item? This prototype knows rice, beans, cooking oil and soap.',
 'start-count':'Name one item, its count, and its unit. For example, rice twelve bags.',
 'review-restored':'Review restored.',
 'reviews-parked':'Earlier drafts are in Needs review, not confirmed stock.',
 'newer-count':'A newer count was confirmed after this review was parked. Restate the complete count before saving it.',
 'confirm-number-only':'Confirm by repeating only the number. For example, confirm thirteen.',
 'incomplete-correction':'The correction was unfinished. Repeat the complete item, number and unit.',
 'unambiguous-number':'I need one unambiguous whole-number count. Repeat the complete item and count.',
 'different-item':'Confirm or discard the current item before starting a different item.',
 'unit-changed':'The unit changed. Say the corrected unit explicitly or discard this draft.',
 'item-unclear':'The item name was uncertain. Repeat it. The current draft is unchanged.',
 'correction-unclear':'The correction marker was uncertain. Repeat the full count.',
 'screen-review':'Please check the on-screen response before continuing.'
}
SMALL='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS={20:'twenty',30:'thirty',40:'forty',50:'fifty',60:'sixty',70:'seventy',80:'eighty',90:'ninety'}
def number_text(n):
 if n<20:return SMALL[n]
 if n<100:return TENS[n//10*10]+(' '+SMALL[n%10] if n%10 else '')
 if n<1000:return SMALL[n//100]+' hundred'
 return SMALL[n//1000]+' thousand'
for n in list(range(100))+list(range(100,1000,100))+list(range(1000,10000,1000)):
 PHRASES['number-'+str(n)]=number_text(n)+'.'
models=Path(tempfile.gettempdir())/'recount-build-voice-model';models.mkdir(exist_ok=True)
expected={'kokoro-v1.0.onnx':'7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for name,sha in expected.items():
 path=models/name
 if not path.exists():urllib.request.urlretrieve('https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'+name,path)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha,name
model=Kokoro(str(models/'kokoro-v1.0.onnx'),str(models/'voices-v1.0.bin'))
clips={}
for idx,(key,text) in enumerate(PHRASES.items()):
 audio,sr=model.create(text,voice='bf_emma',speed=.94,lang='en-gb')
 audio=np.asarray(audio,dtype=np.float32)
 assert sr==24000 and np.isfinite(audio).all() and len(audio)>sr*.08
 # Trim only near-silent edge padding, retain 70 ms around all detected signal.
 active=np.flatnonzero(np.abs(audio)>.003)
 assert len(active)>100,key
 margin=int(sr*.07);audio=audio[max(0,active[0]-margin):min(len(audio),active[-1]+margin+1)]
 audio*=min(1.0,.90/max(float(np.abs(audio).max()),1e-9))
 assert .1<len(audio)/sr<24,(key,len(audio)/sr)
 wav=models/'clip.wav'
 with wave.open(str(wav),'wb') as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((audio*32767).astype('<i2').tobytes())
 target=OUT/(key+'.mp3')
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-codec:a','libmp3lame','-b:a','64k','-ar','24000','-ac','1',str(target)],check=True)
 data=target.read_bytes();clips[key]={'text':text,'path':'/voice/v1/'+key+'.mp3','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'seconds':round(len(audio)/sr,4)}
 if idx%20==0:print('Generated',idx+1,'of',len(PHRASES),flush=True)
manifest={'schema':'recount-bundled-voice-1','voice':'Kokoro bf_emma','origin':'Build-time stock neural synthesis, not a clone or user recording','sample_rate':24000,'clips':clips,'model_sha256':expected,'total_bytes':sum(c['bytes'] for c in clips.values())}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'NOTICE.txt').write_text('Stock neural audio generated at build time using Kokoro-82M (Apache-2.0) through kokoro-onnx (MIT). Voice preset bf_emma. No private recordings or voice cloning. No model weights or voice-bank files are distributed with the site. Source: https://huggingface.co/hexgrad/Kokoro-82M and https://github.com/thewh1teagle/kokoro-onnx\n')
print(json.dumps({'clips':len(clips),'audio_bytes':manifest['total_bytes'],'scope':'Generated response vocabulary, not speech-recognition evaluation'}))
