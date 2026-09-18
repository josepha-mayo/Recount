"""Public-site screenshot walkthrough, NOT a new microphone or ASR evaluation.
The output includes no private audio, judge code, provider key or model weights.
"""
from pathlib import Path
import hashlib, json, re, urllib.request
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from playwright.sync_api import sync_playwright, expect

BASE = 'https://recount-voice-joseph.netlify.app'
APP_SOURCE = 'b82c262cd962415721c5654541ec5c82bc49223b'
ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/tmp/recount-recovery-media')
OUT.mkdir(exist_ok=True)
(OUT/'screens').mkdir(exist_ok=True)
(OUT/'audio').mkdir(exist_ok=True)

SCENES = [
 {'id':'01-task','title':'One correction. One stock record.','text':'Recount is built around a specific mistake: twelve, no, thirteen. It keeps that correction on one draft, then checks the quantity before changing the stock sheet. This walkthrough shows the deployed application using typed inputs, not a new microphone test.'},
 {'id':'02-correction','title':'Invalidate the old number.','text':'First, rice is counted as twelve bags. Saying no clears the old number. Thirteen bags completes the corrected draft. Confirm twelve does not save it. Only the matching confirmation creates one record for thirteen bags.'},
 {'id':'03-review','title':'Keep unfinished work visible.','text':'Now there are eight bags of beans waiting for review. Moving to soap parks the beans draft in Needs review. It is not silently discarded, and it is not treated as confirmed stock.'},
 {'id':'04-export','title':'Export only confirmed stock.','text':'After confirming two bars of soap, the downloaded stock sheet contains rice and soap only. The eight bags of beans are still visible for review, but they stay out of the stock export.'},
 {'id':'05-resume','title':'Resume. Review. Confirm.','text':'The operator can resume the beans draft, inspect the quantity, and explicitly confirm it. That is a separate review action, not a speech-recognition success. The session can then be saved and reopened with its recorded actions intact.'},
 {'id':'06-failure','title':'Two human tests failed.','text':'The first two human recording tests produced no completed stock records. Those failures remain in the evidence. The revised workflow recovers unfinished drafts, but it has not yet passed a fresh interactive human voice test. Refusing everything would not make a useful product.'},
 {'id':'07-engineering','title':'Recovery is tested, not assumed.','text':'The current release also fixes the microphone resuming before a spoken read-back finished. If the read-back fails or times out, speech is cancelled and the session is held for review. Automated browser checks exercise that behavior with simulated speech events, separately from the public-site checks.'},
 {'id':'08-next','title':'Voice where reliable. Review when needed.','text':'Recount is a deliberately small stocktaking prototype: four catalogue items, explicit units, correction-aware drafts, and a confirmed stock export. It does not place orders or alter a shop system. The next validation is a real interactive voice session against this deployed recovery release.'}
]
checks=[]; errors=[]; sockets=[]; hashes={}
# The workflow checks out APP_SOURCE before copying this builder into the checkout.
for item in sorted((ROOT/'web').iterdir()):
    if not item.is_file(): continue
    remote=urllib.request.urlopen(BASE+'/'+('' if item.name=='index.html' else item.name),timeout=20).read()
    assert hashlib.sha256(remote).digest()==hashlib.sha256(item.read_bytes()).digest(), item.name
    hashes[item.name]=hashlib.sha256(remote).hexdigest()

def enter(page, text):
    page.locator('#utterance').fill(text)
    page.locator('#textForm button').click()

def capture(page, scene, full=False):
    page.wait_for_timeout(250)
    name=scene+'.png'
    if full: page.screenshot(path=str(OUT/'screens'/name),full_page=True)
    else: page.locator('.workspace').screenshot(path=str(OUT/'screens'/name))
    return name

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1100},accept_downloads=True)
    page=ctx.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('websocket',lambda ws:sockets.append(ws.url.split('?')[0]))
    response=page.goto(BASE+'/',wait_until='networkidle');assert response.status==200
    expect(page.locator('#confirm')).to_be_disabled()
    capture(page,'01-task',True);checks.append('empty draft cannot save')
    enter(page,'rice twelve bags');enter(page,'no')
    expect(page.locator('#draft')).to_contain_text('?');expect(page.locator('#confirm')).to_be_disabled()
    capture(page,'02a-cleared');checks.append('standalone correction invalidates twelve')
    enter(page,'thirteen bags');enter(page,'confirm twelve')
    expect(page.locator('#rows tr')).to_have_count(0);capture(page,'02b-mismatch')
    checks.append('wrong quantity echo does not save')
    enter(page,'confirm thirteen');expect(page.locator('#rows tr')).to_have_count(1)
    expect(page.locator('#rows')).to_contain_text('13');capture(page,'02-correction')
    checks.append('matching echo saves one Rice 13 bags record')
    enter(page,'beans eight bags');enter(page,'soap')
    expect(page.locator('#reviewRows')).to_contain_text('Beans: 8 bags')
    expect(page.locator('#rows tr')).to_have_count(1);capture(page,'03-review')
    checks.append('switching item parks Beans without saving it')
    enter(page,'two bars');enter(page,'confirm two')
    expect(page.locator('#rows tr')).to_have_count(2)
    with page.expect_download() as event:page.locator('#csv').click()
    event.value.save_as(OUT/'pending-excluded.csv')
    assert (OUT/'pending-excluded.csv').read_text()=='item,quantity,unit\nRice,13,bags\nSoap,2,bars\n'
    capture(page,'04-export');checks.append('downloaded CSV excludes the unconfirmed Beans draft')
    page.locator('#reviewRows button').click()
    expect(page.locator('#draft')).to_contain_text('8 bags');expect(page.locator('#rows tr')).to_have_count(2)
    page.locator('#confirm').click();expect(page.locator('#rows tr')).to_have_count(3)
    capture(page,'05-resume');checks.append('explicit operator confirmation adds Beans after review')
    with page.expect_download() as event:page.locator('#session').click()
    event.value.save_as(OUT/'typed-session.json')
    assert json.loads((OUT/'typed-session.json').read_text())['schema']=='recount-session-2'
    page.reload(wait_until='networkidle');expect(page.locator('#rows tr')).to_have_count(0)
    page.locator('#load').set_input_files(OUT/'typed-session.json');expect(page.locator('#rows tr')).to_have_count(3)
    checks.append('saved versioned actions restore the three confirmed records')
    page.locator('summary').click();expect(page.locator('#accessWrap')).to_be_visible()
    expect(page.locator('#listen')).to_be_disabled();checks.append('microphone remains behind explicit consent')
    capture(page,'07-engineering')
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    assert not errors and not sockets
    ctx.close();browser.close()

# Stock neural narrator. Never publish weights or voice-bank files.
models=Path('/tmp/recount-kokoro');models.mkdir(exist_ok=True)
want={
 'kokoro-v1.0.onnx':'7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5',
 'voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for name,checksum in want.items():
    urllib.request.urlretrieve('https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'+name,models/name)
    assert hashlib.sha256((models/name).read_bytes()).hexdigest()==checksum,name
model=Kokoro(str(models/'kokoro-v1.0.onnx'),str(models/'voices-v1.0.bin'))
for scene in SCENES:
    words=len(re.findall(r"[\w]+(?:['-][\w]+)*",scene['text']))
    speed=.78
    for attempt in range(3):
        samples,sr=model.create(scene['text'],voice='bf_emma',speed=speed,lang='en-gb')
        samples=np.asarray(samples,dtype=np.float32)
        assert np.isfinite(samples).all() and len(samples)>sr
        wpm=words*60/(len(samples)/sr)
        if 114<=wpm<=126:break
        speed=float(np.clip(speed*120/wpm,.55,1.0))
    assert 104<=wpm<=136,(scene['id'],wpm)
    samples*=min(1.0,.88/max(float(np.abs(samples).max()),1e-9))
    file=OUT/'audio'/(scene['id']+'.wav');sf.write(file,samples,sr,subtype='PCM_16')
    scene.update({'speech_seconds':len(samples)/sr,'sample_rate':sr,'words':words,'wpm':wpm,'speed':speed,'audio_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})

receipt={'schema':'recount-recovery-walkthrough-assets-1','status':'passed','app_source':APP_SOURCE,
 'site':BASE,'netlify_deploy_id':'6aad870e4dae12c26dae08e9','checks':checks,'check_count':len(checks),
 'public_assets_sha256':hashes,'provider_audio_calls':0,'provider_websockets':len(sockets),
 'human_recordings_uploaded':0,'voice':'bf_emma','voice_type':'stock neural narration, not a human recording or clone',
 'model_checksums':want,'scenes':SCENES,
 'scope':'Fresh production screenshots and authored typed-input controls/downloads. The narrated presentation is not a real-time video recording or a new voice evaluation.'}
(OUT/'ASSET_RECEIPT.json').write_text(json.dumps(receipt,indent=2))
(OUT/'narration.txt').write_text('\n\n'.join(x['text'] for x in SCENES))
print(json.dumps({'status':'passed','screenshots':len(list((OUT/'screens').glob('*.png'))),'checks':len(checks),'speech_seconds':sum(x['speech_seconds'] for x in SCENES),'provider_audio_calls':0}))
