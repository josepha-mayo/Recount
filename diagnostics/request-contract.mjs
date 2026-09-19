/* Diagnostic transport only. Never rewrites speech or changes the count ledger. */
const ORIGIN = 'wss://streaming.assemblyai.com/v3/ws';

export function buildStreamingURL(token, config) {
  if (typeof token !== 'string' || token.length < 10 || token.length > 4096)
    throw new Error('Invalid temporary token');
  if (config.speech_model !== 'universal-3-5-pro') throw new Error('Unexpected speech model');
  if (!Number.isInteger(config.min_turn_silence) || config.min_turn_silence < 50 || config.min_turn_silence > 500)
    throw new Error('Invalid min_turn_silence');
  if (!Number.isInteger(config.max_turn_silence) || config.max_turn_silence < 500 || config.max_turn_silence > 5000)
    throw new Error('Invalid max_turn_silence');
  if (config.max_turn_silence < config.min_turn_silence) throw new Error('Inverted silence bounds');
  const q = new URLSearchParams({sample_rate: '16000', encoding: 'pcm_s16le',
    speech_model: config.speech_model, token,
    min_turn_silence: String(config.min_turn_silence),
    max_turn_silence: String(config.max_turn_silence)});
  for (const key of ['prompt', 'agent_context']) {
    if (config[key] === undefined) continue;
    if (typeof config[key] !== 'string' || config[key].length > 1750)
      throw new Error(`Invalid ${key}`);
    if (config[key]) q.set(key, config[key]);
  }
  const terms = config.keyterms_prompt;
  if (terms !== undefined) {
    if (!Array.isArray(terms) || terms.length > 100 ||
        terms.some(x => typeof x !== 'string' || !x.trim() || x.length > 50))
      throw new Error('Invalid keyterms list');
    // Raw WebSocket queries require ONE JSON string, not repeated parameters.
    if (terms.length) q.set('keyterms_prompt', JSON.stringify(terms));
  }
  return `${ORIGIN}?${q}`;
}

export function makeRedactor(values = []) {
  const secrets = [...new Set(values.filter(v => typeof v === 'string' && v.length >= 4))]
    .flatMap(v => [v, encodeURIComponent(v)]).sort((a,b) => b.length-a.length);
  return value => {
    let s = String(value ?? '');
    for (const secret of secrets) s = s.split(secret).join('[REDACTED]');
    s = s.replace(/\b(?:https?|wss?):\/\/[^\s"'<>]*\?[^\s"'<>]*/gi, '[REDACTED_QUERY_URL]')
      .replace(/((?:token|access_code|authorization|api[_-]?key|csrf)\s*[:=]\s*)[^\s,;}]+/gi, '$1[REDACTED]');
    return s.slice(0, 4000);
  };
}

export function safeEvent(raw, redact = makeRedactor()) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) || typeof raw.type !== 'string')
    throw new Error('Malformed provider message');
  const r = {type: redact(raw.type)};
  for (const k of ['id','turn_order','transcript','end_of_turn','end_of_turn_confidence',
      'turn_is_formatted','audio_duration_seconds','session_duration_seconds','timestamp',
      'confidence','error_code','error','message','total_audio_received_ms',
      'total_duration_ms','realtime_factor','max_speech_probability']) {
    const v = raw[k];
    if (typeof v === 'string') r[k] = redact(v);
    else if (typeof v === 'boolean' || (typeof v === 'number' && Number.isFinite(v))) r[k] = v;
  }
  if (raw.configuration && typeof raw.configuration === 'object') {
    r.configuration = {};
    for (const k of ['model','mode','api_version','sample_rate','encoding','min_turn_silence',
        'max_turn_silence','speaker_labels','redact_pii','filter_profanity','voice_focus','domain']) {
      const v = raw.configuration[k];
      if (typeof v === 'string') r.configuration[k] = redact(v);
      else if (v === null || typeof v === 'boolean' || (typeof v === 'number' && Number.isFinite(v)))
        r.configuration[k] = v;
    }
  }
  if (Array.isArray(raw.words)) r.words = raw.words.map(w => {
    const item = {};
    for (const k of ['text','confidence','start','end','word_is_final']) {
      const v = w?.[k];
      if (typeof v === 'string') item[k] = redact(v);
      else if (typeof v === 'boolean' || (typeof v === 'number' && Number.isFinite(v))) item[k] = v;
    }
    return item;
  });
  return r;
}

