/* One bounded local utterance. Failed read-backs reject before capture resumes. */
export function conciseReadback(text){
  const s=String(text);
  const m=s.match(/^(Rice|Beans|Cooking oil|Soap): (\d+) (bags|bottles|bars)\. To save hands-free, say “confirm (\d+)”/);
  if(m && m[2]===m[4])return `${m[1]}: ${m[2]} ${m[3]}. Say confirm ${m[2]}, or correct the count.`+(s.includes('low-confidence')?' Check the item and unit carefully.':'');
  if(s.startsWith('The confirmation number or command was not clear enough'))return 'Confirmation unclear. Nothing saved. Repeat the confirmation number, or review it on screen.';
  if(s.startsWith('Audio or transcript integrity needs review.'))return 'Audio needs review. Restate the full item, number and unit, or discard the uncertain draft.';
  if(s.startsWith('The task-critical part of that transcript is uncertain.'))return 'That count was unclear. Please repeat the full item, number and unit.';
  return s;
}
export class ReadbackPlayer {
  constructor({synth=globalThis.speechSynthesis,Utterance=globalThis.SpeechSynthesisUtterance,
    setTimer=globalThis.setTimeout.bind(globalThis),clearTimer=globalThis.clearTimeout.bind(globalThis),timeoutMs=12000}={}){
    Object.assign(this,{synth,Utterance,setTimer,clearTimer,timeoutMs});this.current=null;
  }
  cancel(){
    const v=this.current;
    if(v&&!v.done){v.done=true;this.current=null;this.clearTimer(v.timer);try{this.synth?.cancel();}finally{v.resolve({status:'cancelled'});}}
    else this.synth?.cancel();
  }
  speak(text){
    this.cancel();
    if(!this.synth||!this.Utterance)return Promise.resolve({status:'unavailable'});
    return new Promise((resolve,reject)=>{
      const v={done:false,resolve,reject,timer:null};this.current=v;
      const finish=(ok,reason)=>{
        if(v.done)return;v.done=true;this.clearTimer(v.timer);if(this.current===v)this.current=null;
        if(!ok){try{this.synth.cancel();}catch{}reject(Error(reason));}
        else resolve({status:'completed'});
      };
      try{
        const u=new this.Utterance(conciseReadback(text));u.rate=.88;
        u.onend=()=>finish(true);u.onerror=()=>finish(false,'Read-back audio failed');
        v.timer=this.setTimer(()=>finish(false,'Read-back timed out and was cancelled'),this.timeoutMs);
        this.synth.speak(u);
      }catch{finish(false,'Read-back audio could not start');}
    });
  }
}
