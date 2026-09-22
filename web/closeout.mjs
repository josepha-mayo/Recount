/* Read-only stocktake closeout. No recognition rules or stock values are changed here. */
import {CATALOG, exportCSV} from './core.mjs';

export function buildCloseout(state) {
  if (!state || !Number.isSafeInteger(state.revision) || state.revision < 0 ||
      !state.counts || !Array.isArray(state.review) || !Array.isArray(state.history)) {
    throw Error('A valid Recount session is required');
  }
  if (Object.keys(state.counts).some(sku => !Object.hasOwn(CATALOG, sku))) {
    throw Error('The session contains an unknown catalogue item');
  }
  const drafts = [state.pending, ...state.review.map(x => x.draft)].filter(Boolean);
  if (drafts.some(d => !Object.hasOwn(CATALOG, d.sku))) throw Error('Unknown review item');
  const rows = Object.entries(CATALOG).map(([sku, item]) => {
    const count = state.counts[sku] ?? null;
    if (count && (!Number.isSafeInteger(count.quantity) || count.quantity < 0 || count.quantity > 9999 ||
        count.unit !== item.unit || !Number.isSafeInteger(count.revision) || count.revision < 1 || count.revision > state.revision)) {
      throw Error('Invalid confirmed count');
    }
    const open = drafts.filter(d => d.sku === sku);
    const confirmation = count ? state.history[count.revision - 1] : null;
    const confirmationMethod = !count ? null : confirmation?.kind === 'confirm' ? 'on_screen' :
      confirmation?.source === 'assemblyai' ? 'speech' : confirmation?.source === 'typed' ? 'typed' : 'unclassified';
    return {sku, item: item.label, unit: item.unit,
      status: open.length ? 'needs_review' : count ? 'confirmed' : 'not_counted',
      confirmed_quantity: count?.quantity ?? null,
      confirmation_revision: count?.revision ?? null,
      confirmation_method: confirmationMethod,
      open_drafts: open.length,
      restatement_required: open.some(d => d.blocked || d.identityUncertain)};
  });
  const totals = {scope: rows.length, confirmed: rows.filter(x => x.status === 'confirmed').length,
    needs_review: rows.filter(x => x.status === 'needs_review').length,
    not_counted: rows.filter(x => x.status === 'not_counted').length};
  return {schema: 'recount-closeout-1', revision: state.revision,
    complete: !state.hold && totals.confirmed === totals.scope,
    hold: state.hold ?? null, totals, rows,
    scope: 'Four-item prototype catalogue, not a claim that an entire physical stockroom was counted.',
    privacy: {transcripts_included: false, audio_included: false, credentials_included: false},
    qualification: 'Confirmed means explicitly accepted in this session, not independently verified physical stock. This local report is not tamper-proof.'};
}

export function exportCompleteCSV(state) {
  if (!buildCloseout(state).complete) throw Error('Resolve open drafts and count every scoped item before complete-stocktake export. A partial counts export remains available.');
  return exportCSV(state);
}
