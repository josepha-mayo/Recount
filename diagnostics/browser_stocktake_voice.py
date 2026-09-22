"""Public-site multi-item acceptance with generated input; real HTTP, ASR and read-back.
Four counts, an interrupted draft, zero versus unknown, session replay and explicit UI assistance.
"""
import base64, hashlib, json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
BASE='https://recount-voice.netlify.app'
OUT=Path(os.getenv('RECOUNT_STOCKTAKE_OUT','/tmp/recount-stocktake-voice'));OUT.mkdir(parents=True,exist_ok=True)
INPUT=Path(os.getenv('RECOUNT_LIVE_INPUT','/tmp/recount-stocktake-input'))
CODE=os.environ.get('RECOUNT_DEMO_PASS','')
if not 8<=len(CODE)<=128:raise RuntimeError('Judge secret unavailable')
FIXTURE=r'''(()=>{const Native=window.AudioContext,f=window.__stockInput={playbacks:[]};navigator.mediaDevices.getUserMedia=async()=>{const c=new Native({sampleRate:16000}),d=c.createMediaStreamDestination(),z=c.createConstantSource();z.offset.value=0;z.connect(d);z.start();await c.resume();f.ctx=c;f.dest=d;return d.stream;};f.play=async({name,wav})=>{const b=Uint8Array.from(atob(wav),c=>c.charCodeAt(0)),a=await f.ctx.decodeAudioData(b.buffer),s=f.ctx.createBufferSource();s.buffer=a;s.connect(f.dest);f.playbacks.push({name,seconds:a.duration});await new Promise(resolve=>{s.onended=resolve;s.start();});};})();'''
report={'status':'failed','site':BASE,'source_commit':os.getenv('RECOUNT_SOURCE_COMMIT'),'http_or_asr_mocked':False,'generated_input':'Kokoro af_heart stock voice','human_validation':False,'physical_microphone_tested':False,'operator_assistance':'Beans is explicitly confirmed with the on-screen control after restoring the saved session. Other final counts require spoken quantity confirmation.','token_http_statuses':[],'steps':[]}
started=time.monotonic();stage='launch';page=None;ctx=None;video=None;audits=[]
def save(page,selector,name):
    with page.expect_download() as ev:page.locator(selector).click()
    target=OUT/name;ev.value.save_as(target)
    if target.suffix in ['.json','.csv'] and CODE in target.read_text():
        target.unlink();raise RuntimeError('Private judge code appeared in export')
    return target

def start_voice(page):
    if not page.locator('#voiceSetup').evaluate('(e)=>e.open'):page.locator('summary').click()
    page.locator('#consent').check()
    page.locator('#speakerTest').click();expect(page.locator('#speakerHeard')).to_be_visible(timeout=20000);page.locator('#speakerHeard').click()
    page.locator('#accessCode').fill(CODE);page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('AUDIO LISTENING',timeout=25000)

def play(page,name,kind,expected):
    global stage
    stage=name;expect(page.locator('#mode')).to_have_text('AUDIO LISTENING',timeout=25000)
    page.evaluate('(x)=>__stockInput.play(x)',{'name':name,'wav':base64.b64encode((INPUT/(name+'.wav')).read_bytes()).decode()})
    if kind=='draft':expect(page.locator('#draft')).to_contain_text(expected,timeout=20000)
    elif kind=='rows':expect(page.locator('#rows tr')).to_have_count(expected,timeout=20000)
    elif kind=='reject':expect(page.locator('#reply')).to_contain_text('confirmation said',timeout=20000);expect(page.locator('#rows tr')).to_have_count(0)
    expect(page.locator('#mode')).to_have_text('AUDIO LISTENING',timeout=25000)
    report['steps'].append({'stage':name,'status':'passed','elapsed_seconds':round(time.monotonic()-started,3)})

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--autoplay-policy=no-user-gesture-required'])
    try:
        ctx=browser.new_context(viewport={'width':1440,'height':1080},accept_downloads=True,record_video_dir=str(OUT/'video'),record_video_size={'width':1440,'height':1080})
        ctx.add_init_script(FIXTURE);page=ctx.new_page();video=page.video
        page.on('response',lambda r:report['token_http_statuses'].append(r.status) if r.url==BASE+'/api/token' else None)
        page.on('pageerror',lambda e:report.setdefault('javascript_errors',[]).append(type(e).__name__))
        page.goto(BASE,wait_until='networkidle',timeout=30000)
        stage='first_session';start_voice(page)
        play(page,'beans','draft','27 bags')
        play(page,'oil-focus','draft','Cooking oil')
        expect(page.locator('#reviewRows')).to_contain_text('Beans: 27 bags')
        play(page,'oil-count','draft','16 bottles')
        play(page,'oil-wrong-confirm','reject',None)
        play(page,'oil-confirm','rows',1)
        play(page,'soap-zero','draft','0 bars')
        play(page,'soap-confirm','rows',2)
        page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('TEXT / REVIEW MODE',timeout=10000)
        audits.append(json.loads(save(page,'#voiceReport','first-voice-report.json').read_text()))
        partial=json.loads(save(page,'#handoff','partial-handoff.json').read_text())
        assert partial['totals']=={'scope':4,'confirmed':2,'needs_review':1,'not_counted':1}
        assert next(r for r in partial['rows'] if r['sku']=='soap')['confirmed_quantity']==0
        assert next(r for r in partial['rows'] if r['sku']=='rice')['confirmed_quantity'] is None
        expect(page.locator('#completeCSV')).to_be_disabled()
        page.screenshot(path=str(OUT/'partial-stocktake.png'),full_page=True)
        session=save(page,'#session','interrupted-session.json')
        stage='reopen_and_review';page.reload(wait_until='networkidle');page.locator('#load').set_input_files(session)
        expect(page.locator('#reviewRows')).to_contain_text('Beans: 27 bags');expect(page.locator('#closeoutBadge')).to_have_text('2 / 4 resolved')
        page.locator('#reviewRows button').first.click();expect(page.locator('#rows tr')).to_have_count(2)
        page.locator('#confirm').click();expect(page.locator('#rows tr')).to_have_count(3)
        report['steps'].append({'stage':stage,'status':'passed','assistance':'Explicit on-screen confirmation of Beans 27 bags; not voice-only.'})
        stage='second_session';start_voice(page)
        play(page,'rice-count','draft','41 bags');play(page,'rice-confirm','rows',4)
        page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('TEXT / REVIEW MODE',timeout=10000)
        audits.append(json.loads(save(page,'#voiceReport','second-voice-report.json').read_text()))
        stage='complete_export';expect(page.locator('#completeCSV')).to_be_enabled()
        complete=json.loads(save(page,'#handoff','complete-handoff.json').read_text())
        assert complete['complete'] and complete['totals']=={'scope':4,'confirmed':4,'needs_review':0,'not_counted':0}
        by={r['sku']:r for r in complete['rows']}
        assert {k:v['confirmed_quantity'] for k,v in by.items()}=={'beans':27,'oil':16,'soap':0,'rice':41}
        assert by['beans']['confirmation_method']=='on_screen'
        assert all(by[k]['confirmation_method']=='speech' for k in ['oil','soap','rice'])
        csv=save(page,'#completeCSV','complete-stocktake.csv').read_text().splitlines()
        assert csv[0]=='item,quantity,unit' and set(csv[1:])=={'Beans,27,bags','Cooking oil,16,bottles','Soap,0,bars','Rice,41,bags'}
        for a in audits:
            for name,digest in a['asset_sha256'].items():assert hashlib.sha256((ROOT/'web'/name).read_bytes()).hexdigest()==digest,name
        assert not report.get('javascript_errors')
        assert report['token_http_statuses']==[200,200],report['token_http_statuses']
        report.update(status='passed',confirmed_items=4,spoken_confirmed_items=3,on_screen_confirmed_items=1,provider_sessions=sum(a['summary']['provider_begins'] for a in audits),final_transcripts=sum(a['summary']['final_events'] for a in audits),completed_readbacks=sum(a['summary']['completed_readbacks'] for a in audits),speech_output_errors=sum(a['summary']['speech_output_errors'] for a in audits),complete_handoff=complete)
        page.screenshot(path=str(OUT/'complete-stocktake.png'),full_page=True)
    except Exception as e:
        report.update(failure_stage=stage,failure_type=type(e).__name__)
        if page:
            try:
                report['observed_ui']={k:page.locator('#'+k).inner_text().replace(CODE,'[REDACTED]')[:500] for k in ['mode','error','reply','draft']}
                page.screenshot(path=str(OUT/'failure.png'),full_page=True)
                page.locator('#consent').uncheck();page.wait_for_timeout(200)
                if page.locator('#voiceReport').is_enabled():save(page,'#voiceReport','failure-voice-report.json')
            except Exception:pass
    finally:
        if ctx:ctx.close()
        if video:
            try:video.save_as(str(OUT/'stocktake-browser.webm'))
            except Exception:pass
        browser.close();report['elapsed_seconds']=round(time.monotonic()-started,3)
        (OUT/'RECEIPT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if report['status']!='passed':raise SystemExit(1)
