import {speechErrorCode,speechErrorMessage} from './readback.mjs';
export const SPEAKER_TEST_TEXT='This is Recount. If you can hear this voice, tap I heard it.';
export class SpeakerCheck {
  constructor(player,{onChange=()=>{},onTrace=()=>{}}={}){Object.assign(this,{player,onChange,onTrace});this.generation=0;this.state='untested';this.code=null;}
  ready(){return this.state==='heard';}
  busy(){return this.state==='testing';}
  trace(event,extra={}){try{this.onTrace({event,...extra});}catch{}}
  changed(){this.onChange();}
  reset(){this.generation++;this.player.cancel();this.state='untested';this.code=null;this.changed();}
  async test(){
    const id=++this.generation;this.state='testing';this.code=null;
    const capabilities=this.player.capabilities();this.trace('speaker_test_started',capabilities);this.changed();
    try{
      // Start during the originating click, not after permission/network work.
      const result=await this.player.speak(SPEAKER_TEST_TEXT);
      if(id!==this.generation)return;
      if(result?.status!=='completed')throw Object.assign(new Error('Speaker unavailable'),{code:result?.code||'speech-unavailable'});
      this.state='awaiting_confirmation';this.trace('speaker_test_finished',{status:'completed'});
    }catch(error){if(id!==this.generation)return;this.code=speechErrorCode(error?.code);this.state='failed';this.trace('speaker_test_failed',{code:this.code});}
    this.changed();
  }
  heard(){if(this.state!=='awaiting_confirmation')return false;this.state='heard';this.trace('speaker_test_confirmed');this.changed();return true;}
  unheard(){if(!['awaiting_confirmation','heard'].includes(this.state))return false;this.state='unheard';this.trace('speaker_test_unheard');this.changed();return true;}
  message(){
    if(this.state==='testing')return 'Playing a short speaker test. The microphone is OFF.';
    if(this.state==='awaiting_confirmation')return 'The browser reported playback finished. Did you actually hear the voice?';
    if(this.state==='heard')return 'Speaker test confirmed by you. Voice mode is ready when access and consent are set.';
    if(this.state==='unheard')return 'You reported no sound. Voice mode stays off. Check the media volume/output device; the browser may report completion even without audible output.';
    if(this.state==='failed')return speechErrorMessage(this.code)+' Microphone and transcription have not started for this test.';
    return 'First tap Test speaker. It uses no microphone or AssemblyAI credit.';
  }
}
