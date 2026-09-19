from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
EXPECTED={
'web/app.mjs':'96e279a634183046ed37027ec2612a8364075689af727cf2f8b4352a30bcb3e6',
'web/index.html':'affeb4a07c6259e97f93f292ac8cfb8701d698c86c241947dd1c6e18c14ad89f',
'web/style.css':'9ba8f1208c1e8506c9eb028757bc8d5006e26a159ee16d3eaf18b3676379db7f',
'web/readback.mjs':'e3ee030ca6d6e8c8f9c632aeea37d6e687ed5115d9e320c1ff5e42907768658e',
'web/voice-audit.mjs':'f2873998aff2936fa28facd479c6ed9b5e06e916b3e215b7369d83149ad75021',
'server.py':'00d9d58d23ee8bcbed570ef654021d77868b76fdc8ccc7ec4dafc1d55808090f',
'tests/browser_speaker_check.py':'b3b34106487c03513643e957529a027378623130473ab630f2951e46c02505a5',
'tests/browser_readback_barrier.py':'b9de8cda24358cc3287f6bab18ac517186bfa9959846a3615d48324842d046c4',
'tests/browser_voice_recovery.py':'7c9b7bf281c4a2b0185b4df6a0d7c41dc5ac1349185c49c37ebf2af815c896bd'}
for path,sha in EXPECTED.items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==sha,'Unexpected source '+path
changed={}
def replace(s,a,b):
 assert a in s,a[:100]
 return s.replace(a,b)
def edit(path,fn):changed[path]=fn((R/path).read_text())
def app(s):
 s=replace(s,"import {ReadbackPlayer} from './readback.mjs';","import {ReadbackPlayer} from './readback.mjs';\nimport {AudioReadbackPlayer} from './audio-readback.mjs';")
 s=replace(s,'const readback=new ReadbackPlayer();',"""const nativeReadback=new ReadbackPlayer(),audioReadback=new AudioReadbackPlayer();
const selectedPlayer=()=>$('voiceEngine').value==='native'?nativeReadback:audioReadback;
const readback={cancel(){nativeReadback.cancel();audioReadback.cancel();},
  speak(text){return selectedPlayer().speak(text);},
  capabilities(){return {...selectedPlayer().capabilities(),backend:$('voiceEngine').value==='native'?'native-speech':'bundled-neural-audio'};}};""")
 s=replace(s,"$('speak').disabled=locked;","$('speak').disabled=locked;$('voiceEngine').disabled=locked;")
 s=replace(s,"'speaker-check.mjs']","'speaker-check.mjs','audio-readback.mjs']")
 return replace(s,"$('speak').onchange=()=>{speaker.reset();render();};","$('speak').onchange=()=>{speaker.reset();render();};\n$('voiceEngine').onchange=()=>{speaker.reset();render();};")
edit('web/app.mjs',app)
edit('web/index.html',lambda s:replace(s,'<button id="speakerTest"','<label class="voice-output">Reply audio <select id="voiceEngine"><option value="audio" selected>Bundled neural voice</option><option value="native">Device speech (compatibility)</option></select><small>Bundled voice plays audio files. It does not use your device speech engine or another paid API.</small></label><button id="speakerTest"'))
edit('web/style.css',lambda s:s+'\n.voice-output{margin-bottom:14px}.voice-output select{display:block;width:100%;background:#101916;color:#eef3e7;border:1px solid #35483c;border-radius:7px;padding:10px;margin:5px 0;font:14px system-ui}\n')
def errors(s):
 s=replace(s,"'invalid-argument','not-allowed','speech-start-timeout'","'audio-unavailable','audio-load-failed','audio-integrity','audio-decode-failed','audio-blocked','audio-timeout','audio-plan-failed','audio-playback-failed','invalid-argument','not-allowed','speech-start-timeout'")
 return replace(s,'const messages={',"""const messages={
    'audio-unavailable':'Audio playback is unavailable in this browser.',
    'audio-load-failed':'The bundled voice could not load. Check the connection and tap Test speaker again.',
    'audio-integrity':'A downloaded voice file failed verification. Nothing was played.',
    'audio-decode-failed':'The browser could not decode the bundled audio.',
    'audio-blocked':'Audio playback is blocked or paused. Tap Test speaker directly.',
    'audio-timeout':'Audio playback did not finish in time.',
    'audio-plan-failed':'The reply cannot safely be represented as bundled audio. Review the screen.',
    'audio-playback-failed':'Audio playback failed. The microphone remains held.',""")
edit('web/readback.mjs',errors)
def audit(s):
 s=replace(s,"if(typeof row.supported==='boolean')","if(['bundled-neural-audio','native-speech'].includes(row.backend))out.playback_backend=row.backend;\n    if(typeof row.supported==='boolean')")
 s=replace(s,"'speaker-check.mjs']","'speaker-check.mjs','audio-readback.mjs']")
 return replace(s,"client_revision:'speaker-preflight-20260919'","client_revision:'bundled-neural-audio-20260919'")
edit('web/voice-audit.mjs',audit)
def server(s):
 s=replace(s,"paths={'/':","paths={'/audio-readback.mjs':('audio-readback.mjs','text/javascript'),'/':")
 needle="        if self.path not in paths:return self.send(404,{'error':'Not found'})"
 inject="""        # Serve only manifest-listed public audio vocabulary, never arbitrary files.
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
"""
 return replace(s,needle,inject+needle)
edit('server.py',server)
# Retain every existing native-speech assertion, now explicitly in compatibility mode.
# The new primary-backend suite exercises decoded MP3 audio with native synthesis disabled.
for path,var in [('tests/browser_speaker_check.py','p'),('tests/browser_readback_barrier.py','page'),('tests/browser_voice_recovery.py','page')]:
 edit(path,lambda s,var=var:replace(s,f"{var}.goto(BASE+'/',wait_until='networkidle');",f"{var}.goto(BASE+'/',wait_until='networkidle');{var}.locator('#voiceEngine').select_option('native');"))
for path,text in changed.items():(R/path).write_text(text)
print('Applied',len(changed),'byte-checked changes; ledger and runtime remain untouched')
