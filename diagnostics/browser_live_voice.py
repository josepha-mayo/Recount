"""Live production test: generated microphone audio, real config/token/ASR/TTS.
No provider events, word confidence, ledger transitions or HTTP responses are mocked.
The automated speaker acknowledgement is not evidence of sound heard by a person.
"""
import base64, hashlib, json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
BASE='https://recount-voice.netlify.app'
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('RECOUNT_LIVE_OUT','/tmp/recount-live-voice'));OUT.mkdir(parents=True,exist_ok=True)
INPUT=Path(os.environ.get('RECOUNT_LIVE_INPUT','/tmp/recount-voice-input'))
CODE=os.environ.get('RECOUNT_DEMO_PASS','')
if not 8<=len(CODE)<=128:raise RuntimeError('Judge Actions secret is missing')
FIXTURE=r'''(()=>{
 const Native=window.AudioContext;
 const f=window.__liveInput={contexts:[],streams:[],playbacks:[]};
 navigator.mediaDevices.getUserMedia=async()=>{
  const ctx=new Native({sampleRate:16000}),dest=ctx.createMediaStreamDestination();
  const zero=ctx.createConstantSource();zero.offset.value=0;zero.connect(dest);zero.start();
  await ctx.resume();f.contexts.push(ctx);f.streams.push(dest.stream);f.ctx=ctx;f.dest=dest;return dest.stream;
 };
 f.play=async({name,wav})=>{
  const bytes=Uint8Array.from(atob(wav),c=>c.charCodeAt(0));
  const buffer=await f.ctx.decodeAudioData(bytes.buffer),source=f.ctx.createBufferSource();source.buffer=buffer;source.connect(f.dest);
  const row={name,start_ms:performance.now(),seconds:buffer.duration};f.playbacks.push(row);
  await new Promise(resolve=>{source.onended=()=>{row.end_ms=performance.now();resolve();};source.start();});
 };
})();'''
report={'status':'failed','source_commit':'d9841875a27c95dcb50d36c91728fdce9252ebfb','site':BASE,'microphone_input':'generated Kokoro stock voice','physical_microphone_tested':False,'human_validation':False,'speaker_acknowledgement':'automated test control, not a human claim','http_or_asr_mocked':False,'token_http_statuses':[],'steps':[]}
started=time.monotonic();stage='browser_launch';page=None;context=None;video=None

def safe(text):
    return str(text).replace(CODE,'[REDACTED]')[:2000]

def download_report(page,name):
    if not page.locator('#voiceReport').is_enabled():return None
    with page.expect_download() as event:page.locator('#voiceReport').click()
    target=OUT/name;event.value.save_as(target)
    text=target.read_text()
    if CODE in text:
        target.unlink();raise RuntimeError('Report included judge code')
    return json.loads(text)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--autoplay-policy=no-user-gesture-required'])
    try:
        context=browser.new_context(viewport={'width':1360,'height':1050},accept_downloads=True,record_video_dir=str(OUT/'video'),record_video_size={'width':1360,'height':1050})
        context.add_init_script(FIXTURE);page=context.new_page();video=page.video
        page.on('response',lambda r:report['token_http_statuses'].append(r.status) if r.url==BASE+'/api/token' else None)
        page.on('pageerror',lambda e:report.setdefault('javascript_errors',[]).append(type(e).__name__))
        stage='page_load';page.goto(BASE,wait_until='networkidle',timeout=30000)
        page.evaluate('''()=>{const b=document.createElement('div');b.textContent='AUTOMATED LIVE TEST | GENERATED SPEECH INPUT | REAL ASSEMBLYAI | NOT HUMAN VALIDATION';b.style.cssText='position:fixed;top:0;left:0;right:0;z-index:9999;padding:8px;background:#111;color:#fff;font:13px sans-serif;text-align:center;';document.body.appendChild(b);}''')
        page.locator('summary').click();page.locator('#consent').check()
        stage='speaker_test';page.locator('#speakerTest').click();expect(page.locator('#speakerHeard')).to_be_visible(timeout=20000);page.locator('#speakerHeard').click()
        stage='invalid_code_control';page.locator('#accessCode').fill('synthetic-invalid-control');page.locator('#listen').click()
        expect(page.locator('#error')).to_have_text('Invalid judge access code.',timeout=25000)
        expect(page.locator('#mode')).to_have_text('REVIEW REQUIRED')
        report['steps'].append({'stage':stage,'status':'passed','elapsed_s':round(time.monotonic()-started,3)})
        page.screenshot(path=str(OUT/'rejected-code.png'),full_page=True)
        download_report(page,'rejected-code-report.json')
        stage='accepted_code_retry';page.locator('#accessCode').fill(CODE);page.locator('#listen').click()
        expect(page.locator('#mode')).to_have_text('AUDIO LISTENING',timeout=25000)
        page.wait_for_timeout(400)
        report['steps'].append({'stage':stage,'status':'passed','elapsed_s':round(time.monotonic()-started,3)})
        for filename,expected in [('count.wav','12'),('correction.wav','13'),('wrong-confirm.wav','13'),('confirm.wav','13')]:
            stage=filename.removesuffix('.wav')
            expect(page.locator('#mode')).to_have_text('AUDIO LISTENING',timeout=25000)
            wav=(INPUT/filename).read_bytes()
            page.evaluate('(args)=>window.__liveInput.play(args)',{'name':stage,'wav':base64.b64encode(wav).decode()})
            if stage=='confirm':
                expect(page.locator('#rows tr')).to_have_count(1,timeout=20000)
                expect(page.locator('#rows')).to_contain_text('13')
            elif stage=='wrong-confirm':
                expect(page.locator('#reply')).to_contain_text('confirmation said',timeout=20000)
                expect(page.locator('#rows tr')).to_have_count(0)
            else:
                expect(page.locator('#draft')).to_contain_text(expected+' bags',timeout=20000)
                expect(page.locator('#rows tr')).to_have_count(0)
            expect(page.locator('#mode')).to_have_text('AUDIO LISTENING',timeout=25000)
            report['steps'].append({'stage':stage,'status':'passed','reply':safe(page.locator('#reply').inner_text()),'elapsed_s':round(time.monotonic()-started,3)})
            page.screenshot(path=str(OUT/(stage+'.png')),full_page=True)
        stage='finish_and_export';page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('TEXT / REVIEW MODE',timeout=10000)
        audit=download_report(page,'live-interaction-report.json')
        assert audit and audit['ledger']['counts']['rice']['quantity']==13 and len(audit['ledger']['counts'])==1
        assert audit['summary']['provider_begins']==1 and audit['summary']['final_events']>=4
        for name,digest in audit['asset_sha256'].items():assert hashlib.sha256((ROOT/'web'/name).read_bytes()).hexdigest()==digest,name
        with page.expect_download() as event:page.locator('#csv').click()
        event.value.save_as(OUT/'live-stock.csv')
        assert (OUT/'live-stock.csv').read_text()=='item,quantity,unit\nRice,13,bags\n'
        assert 403 in report['token_http_statuses'] and 200 in report['token_http_statuses']
        assert not report.get('javascript_errors')
        report['status']='passed';report['audit_summary']=audit['summary'];report['steps'].append({'stage':stage,'status':'passed'})
    except Exception as e:
        report['failure_stage']=stage;report['failure_type']=type(e).__name__
        if page:
            try:
                report['observed_ui']={key:safe(page.locator('#'+key).inner_text()) for key in ['mode','error','reply','draft','partial']}
                page.screenshot(path=str(OUT/'failure.png'),full_page=True)
                page.locator('#consent').uncheck();page.wait_for_timeout(400)
                download_report(page,'failure-interaction-report.json')
            except Exception:pass
    finally:
        if page:
            try:report['input_playbacks']=page.evaluate('window.__liveInput.playbacks')
            except Exception:pass
        if context:context.close()
        if video:
            try:video.save_as(str(OUT/'live-browser.webm'))
            except Exception:pass
        browser.close()
        report['elapsed_s']=round(time.monotonic()-started,3)
        (OUT/'RECEIPT.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
if report['status']!='passed':raise SystemExit(1)
