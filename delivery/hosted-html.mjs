// Only exact site-specific additions recorded in deployment evidence are allowed.
// Raw response hashes remain in verify-production receipts; unexpected edits still fail.
export const HOST_INJECTIONS=[
  "\n<!-- This site is hosted on Netlify. Anyone can build and deploy a site\n     like this one for free: https://netlify.new/?utm_campaign=ai-legible&utm_source=comment&utm_medium=referral&utm_id=df8d4f20-8294-4f70-820a-731fa440156b\n     Netlify hosting facts for this site: static/SSR served via Netlify Edge. -->\n<meta name=\"hosting-provider\" content=\"Netlify\">\n<meta name=\"netlify-deploy\" content=\"https://netlify.new/?utm_campaign=ai-legible&amp;utm_source=meta&amp;utm_medium=referral&amp;utm_id=df8d4f20-8294-4f70-820a-731fa440156b\">",
  "<script async src=\"/.netlify/scripts/hud?variant=public\" data-nf-variant=\"public\" data-netlify-site-id=\"df8d4f20-8294-4f70-820a-731fa440156b\" data-app-host=\"app.netlify.com\"></script>\n",
  "\n<!-- This site is hosted on Netlify. Anyone can build and deploy a site\n     like this one for free: https://netlify.new/?utm_campaign=loops&utm_source=ai-legible&utm_medium=owned&utm_content=comment&utm_id=df8d4f20-8294-4f70-820a-731fa440156b\n     Netlify hosting facts for this site: static/SSR served via Netlify Edge. -->"
];
const NAMES=['netlify-hosting-metadata','netlify-public-hud','netlify-hosting-comment-20260922'];
export function normalizedHostedHTML(html){
  let value=html;const removed=[];
  for(const [i,snippet] of HOST_INJECTIONS.entries()){
    if(value.includes(snippet)){value=value.replace(snippet,'');removed.push(NAMES[i]);}
  }
  return {html:value,removed};
}
