/* Observed development profile, not an accuracy or optimal-latency claim. */
export const PROFILE_ID='short-counts-160-400-v1';
export const KEYTERMS=Object.freeze(['rice','beans','cooking oil','soap','bags','bottles','bars','cartons','confirm','confirmed','discard count','actually','sorry']);
export function streamingURL({token,sampleRate,speechModel}){
  if(typeof token!=='string'||token.length<10||token.length>4096)throw Error('Invalid temporary token');
  if(!Number.isInteger(sampleRate)||sampleRate<8000||sampleRate>48000)throw Error('Invalid audio sample rate');
  if(speechModel!=='universal-3-5-pro')throw Error('Unexpected speech model');
  const q=new URLSearchParams({sample_rate:String(sampleRate),encoding:'pcm_s16le',speech_model:speechModel,
    min_turn_silence:'160',max_turn_silence:'400',
    prompt:'Inventory stocktaking conversation. The speaker uses short commands with rice, beans, cooking oil, soap; units bags, bottles, bars, cartons; corrections such as no, actually, sorry; confirmations such as confirm plus a whole-number quantity; and discard count.',
    agent_context:'Recount asks for one stock item, quantity and unit. The speaker may correct a count or confirm by repeating the quantity.',
    keyterms_prompt:JSON.stringify(KEYTERMS),token});
  return 'wss://streaming.assemblyai.com/v3/ws?'+q;
}
