import { createHash, timingSafeEqual } from 'node:crypto';
import { JUDGE_CODE_SHA256 } from './judge-verifier.mts';

export function codeDigest(code: string): string {
  return createHash('sha256').update('Recount judge code v1\0').update(code).digest('hex');
}
function validDigest(value: string): boolean { return /^[a-f0-9]{64}$/.test(value); }
function validCode(value: unknown): value is string {
  return typeof value === 'string' && value.length >= 8 && value.length <= 128;
}
export function judgeConfigured(legacyCode: string, verifier = JUDGE_CODE_SHA256): boolean {
  return validDigest(verifier) || validCode(legacyCode);
}
export function judgeMatches(candidate: unknown, legacyCode: string, verifier = JUDGE_CODE_SHA256): boolean {
  if (!validCode(candidate) || !judgeConfigured(legacyCode, verifier)) return false;
  const expected = validDigest(verifier) ? verifier : codeDigest(legacyCode);
  return timingSafeEqual(Buffer.from(codeDigest(candidate), 'hex'), Buffer.from(expected, 'hex'));
}
