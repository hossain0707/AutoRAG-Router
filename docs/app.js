/* AutoRAG Router live static preview.
 * A real, inspectable browser-side implementation of the published Python baseline.
 * No LLM, third-party search or server endpoint is invoked. All documents remain in memory.
 * License: see ../LICENSE (personal noncommercial use only).
 */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const RELATIONS = ['relationship','related','connected','connect','dependency','dependencies','depends','network','graph','between','linked'];
  const COMPLEX = ['compare','analyze','investigate','research','synthesize','across','multi-step','multiple','evaluate','why'];
  const VISUAL = ['diagram','image','screenshot','figure','chart','photo','pdf','table in the'];
  const STRUCTURED = ['sum','total','average','count','revenue','sales','records','rows','group by','how many'];
  const NO_RETRIEVAL = ['hello','hi','thanks','thank you','write a poem','tell a joke'];
  const STRATEGIES = ['no_rag','hybrid','graph','agentic','multimodal','structured'];
  const TITLE = { no_rag:'No-RAG',hybrid:'Hybrid RAG',graph:'Graph RAG',agentic:'Agentic RAG',multimodal:'Multimodal RAG',structured:'Structured RAG' };
  const SEED = [
    {id:'architecture-atlas',title:'Atlas ingestion service',source:'internal://architecture/atlas',kind:'text',entities:['Atlas','Beacon'],text:'Atlas collects and normalizes incoming operational events. Atlas sends the normalized records to Beacon for indexing; Beacon is downstream of Atlas. Compass queries the indexed records through Beacon.'},
    {id:'architecture-beacon',title:'Beacon search index',source:'internal://architecture/beacon',kind:'text',entities:['Atlas','Beacon','Compass'],text:'Beacon receives normalized records from Atlas and maintains the search index. Compass depends on Beacon to retrieve search results. Beacon has a dependency on upstream Atlas ingestion.'},
    {id:'employee-policy',title:'Employee leave handbook',source:'internal://policies/leave',kind:'text',entities:['HR'],text:'Employees receive twenty paid annual leave days per year. Leave requests require manager approval through the HR portal. Remote work requests are reviewed individually.'},
    {id:'security-policy',title:'Security incident response policy',source:'internal://policies/security',kind:'text',entities:['SOC'],text:'For suspected phishing, notify the security operations team immediately. Security incidents are triaged within one hour. Never share passwords and report suspicious links through the incident portal.'},
    {id:'quarterly-revenue',title:'2026 revenue table',source:'internal://finance/2026-Q2',kind:'table',entities:[],text:'The finance table reports Q1 2026 revenue of 200000 USD and Q2 2026 revenue of 250000 USD. The Q2 revenue total is 250000 USD.',metadata:{year:2026,quarter:'Q2'}},
    {id:'system-topology',title:'Architecture diagram caption',source:'internal://diagrams/services',kind:'image_caption',entities:['Atlas','Beacon','Compass'],text:'Architecture diagram caption: arrows show Atlas ingestion to Beacon indexing and Beacon search to Compass orchestration. A verification stage checks retrieved evidence before a result is returned.'},
    {id:'compliance-procedure',title:'Access and compliance procedure',source:'internal://policies/access',kind:'pdf_text',entities:['SOC','HR'],text:'Extracted text from a company procedure PDF: privileged access reviews occur quarterly; audit exceptions are recorded. The security team investigates escalated incidents; HR approves employee access during onboarding.'},
  ];
  const SCENARIOS = {
    graph:'How are Atlas and Beacon connected in our service architecture?',
    structured:'What was the Q2 2026 revenue total?',
    multimodal:'Explain the architecture diagram showing Atlas, Beacon and Compass.',
    agentic:'Compare annual leave and security incident response procedures.',
    hybrid:'What should an employee do after a suspected phishing link?',
    no_rag:'Hello',
  };
  let docs = SEED.map(d=>({...d}));
  let running = false;
  let last = null;
  const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const containsAny = (s, terms) => terms.some(t => new RegExp('\\b'+escapeRe(t)+'\\b').test(s));
  const tokenize = (s) => (s.toLowerCase().match(/[\p{L}\p{N}_]+/gu) || []);
  const ngrams = (s) => {const normalized=tokenize(s).join(' '), out=new Map();for(let i=0;i<normalized.length-2;i++){const tri=normalized.slice(i,i+3);out.set(tri,(out.get(tri)||0)+1);}return out;};
  const similarity = (a,b) => {const x=ngrams(a),y=ngrams(b);if(!x.size||!y.size)return 0;let dot=0,xx=0,yy=0;for(const [k,v] of x){dot+=v*(y.get(k)||0);xx+=v*v;}for(const v of y.values())yy+=v*v;return dot/Math.sqrt(xx*yy);};
  function policy(query){
    const q=query.toLowerCase().trim();let primary,confidence,reason;
    if(NO_RETRIEVAL.includes(q)||(containsAny(q,NO_RETRIEVAL.slice(0,2))&&q.length<18)){
      [primary,confidence,reason]=['no_rag',.98,'Conversation does not require document lookup'];
    }else if(containsAny(q,VISUAL)){
      [primary,confidence,reason]=['multimodal',.85,'Visual or document-derived information requested'];
    }else if(containsAny(q,STRUCTURED)){
      [primary,confidence,reason]=['structured',.80,'Quantitative or structured-record intent'];
    }else if(containsAny(q,RELATIONS)){
      [primary,confidence,reason]=['graph',.82,'Entity relationship intent'];
    }else if(containsAny(q,COMPLEX)||q.split(/\s+/).length>=32){
      [primary,confidence,reason]=['agentic',.79,'Complex or multi-part information need'];
    }else{
      [primary,confidence,reason]=['hybrid',.76,'General factual retrieval benefits from lexical and fuzzy similarity'];
    }
    const stages=[primary];if(!['no_rag','hybrid'].includes(primary))stages.push('hybrid_fallback');if(primary!=='no_rag')stages.push('evidence_check');
    return {primary,confidence,reason,stages};
  }
  function bm25(query,items){
    if(!items.length)return new Map();
    const terms=[...new Set(tokenize(query))],docWords=items.map(d=>tokenize(d.text+' '+d.title)),avg=docWords.reduce((a,b)=>a+b.length,0)/items.length;
    const df=new Map();for(const words of docWords)for(const term of new Set(words))df.set(term,(df.get(term)||0)+1);
    const results=new Map();
    for(let i=0;i<items.length;i++){
      const words=docWords[i],tf=new Map();for(const t of words)tf.set(t,(tf.get(t)||0)+1);
      let score=0;for(const t of terms){const f=tf.get(t)||0;if(!f)continue;const idf=Math.log(1+(items.length-(df.get(t)||0)+.5)/((df.get(t)||0)+.5));score+=idf*f*2.2/(f+1.2*(.25+.75*words.length/Math.max(avg,1)));}
      results.set(items[i].id,score);
    }return results;
  }
  function hybrid(query,items,topK=5){
    if(!items.length)return [];
    const lexical=bm25(query,items),fuzzy=new Map(items.map(d=>[d.id,similarity(query,d.title+' '+d.text)]));const rr=new Map();
    for(const scores of [lexical,fuzzy]){
      const ordered=[...scores.entries()].filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
      ordered.forEach(([id],rank)=>rr.set(id,(rr.get(id)||0)+1/(61+rank)));
    }
    return items.filter(d=>(rr.get(d.id)||0)>0).sort((a,b)=>(rr.get(b.id)||0)-(rr.get(a.id)||0)||a.id.localeCompare(b.id)).slice(0,topK).map(d=>({doc:d,score:Math.round((rr.get(d.id)/(2/61))*1e4)/1e4,method:'hybrid_bm25_char3_rrf'}));
  }
  function graph(query,items,topK=5){
    const terms=new Set(tokenize(query));const lower=query.toLowerCase();const seeds=new Set();
    for(const d of items)for(const e of d.entities||[])if(terms.has(e.toLowerCase())||lower.includes(e.toLowerCase()))seeds.add(e.toLowerCase());
    if(!seeds.size)return [];
    return items.map(doc=>({doc,score:(doc.entities||[]).filter(e=>seeds.has(e.toLowerCase())).length/seeds.size,method:'entity_graph'}))
      .filter(h=>h.score>0).sort((a,b)=>b.score-a.score||a.doc.id.localeCompare(b.doc.id)).slice(0,topK);
  }
  function agentic(query,items,topK=5){
    const parts=query.split(/\b(?:and|versus|vs\.?|compared to)\b|[;?]/i).map(s=>s.trim()).filter(s=>s.length>=3).slice(0,4);
    const aggregate=new Map();for(const part of (parts.length?parts:[query]))for(const h of hybrid(part,items,Math.min(20,items.length)))aggregate.set(h.doc.id,Math.max(h.score,aggregate.get(h.doc.id)||0));
    return items.filter(d=>aggregate.has(d.id)).sort((a,b)=>aggregate.get(b.id)-aggregate.get(a.id)||a.id.localeCompare(b.id)).slice(0,topK).map(doc=>({doc,score:aggregate.get(doc.id),method:'decomposed_hybrid'}));
  }
  function snippet(doc,query){const terms=new Set(tokenize(query));const sentences=doc.text.split(/(?<=[.!?])\s+|\n+/);let winner=doc.text,overlap=-1;for(const sentence of sentences){const score=[...new Set(tokenize(sentence))].filter(t=>terms.has(t)).length;if(score>overlap){overlap=score;winner=sentence;}}return winner.slice(0,420);}
  function runQuery(query){
    const begin=performance.now(),decision=policy(query),trace=['policy:'+decision.primary];
    if(decision.primary==='no_rag')return {decision,hits:[],grounded:false,trace,latency:performance.now()-begin,answer:'No retrieval required for this conversational request.'};
    if(!docs.length)return {decision,hits:[],grounded:false,trace:[...trace,'empty_index'],latency:performance.now()-begin,answer:'No documents indexed. Add a document first.'};
    let ranked;
    switch(decision.primary){
      case 'graph':ranked=graph(query,docs);break;
      case 'agentic':ranked=agentic(query,docs);break;
      case 'structured':ranked=hybrid(query,docs).map(h=>({...h,method:'structured_filter+'+h.method}));break;
      case 'multimodal':ranked=hybrid(query,docs.filter(d=>['image_caption','pdf_text','table'].includes(d.kind)));trace.push('pre_extracted_multimodal_text_only');break;
      default:ranked=hybrid(query,docs);
    }
    trace.push('retrieved:'+ranked.length);
    if(!ranked.length&&decision.stages.includes('hybrid_fallback')){ranked=hybrid(query,docs);trace.push('hybrid_fallback_triggered');}
    const hits=ranked.map(h=>({...h,snippet:snippet(h.doc,query)}));const grounded=!!(hits.length&&hits[0].score>=.05);
    trace.push('evidence_check:'+(grounded?'pass':'insufficient'));
    const answer=grounded?'Evidence retrieved from '+hits.length+' matching source(s). These snippets are relevant retrieval candidates; review the sources before drawing conclusions.':'Insufficient matching evidence. No factual answer generated.';
    return {decision,hits,grounded,trace,latency:performance.now()-begin,answer};
  }
  function node(tag,className,value){const el=document.createElement(tag);if(className)el.className=className;if(value!==undefined)el.textContent=String(value);return el;}
  function renderDocs(){
    $('indexedCount').textContent=docs.length;$('docCountLabel').textContent=docs.length+' local sample / user records';
    const root=$('documents');root.replaceChildren();for(const d of docs){const wrap=node('article','doc');wrap.append(node('div','doc-tag',d.kind.replace('_',' ')),node('div','doc-title',d.title),node('div','doc-source',d.source));root.append(wrap);}
  }
  function renderResult(res){
    last=res;const {decision,hits,trace,grounded}=res;
    document.querySelectorAll('.strategy-chip').forEach(el=>el.classList.toggle('active',el.dataset.strategy===decision.primary));
    $('selectedStrategy').textContent=TITLE[decision.primary];$('decisionReason').textContent=decision.reason;
    $('confidenceValue').textContent=Math.round(decision.confidence*100)+'%';$('confidenceRing').style.setProperty('--pct',(decision.confidence*100)+'%');
    $('decisionStatus').textContent='ROUTE SELECTED';$('flowStatus').textContent='COMPLETED';$('matchedCount').textContent=hits.length;
    $('latency').textContent=res.latency.toFixed(2)+' ms';$('grounded').textContent=decision.primary==='no_rag'?'N/A':(grounded?'PRESENT':'LOW');
    $('evidenceBadge').textContent=decision.primary==='no_rag'?'SKIPPED':grounded?'EVIDENCE FOUND':'NO SUPPORT';
    $('verificationMessage').textContent=decision.primary==='no_rag'?'Retrieval correctly skipped':grounded?'Matching sources identified':'Insufficient evidence';
    for(const id of ['inputNode','routerNode','evidenceNode'])$(id).classList.add('active');
    $('trace').replaceChildren(...trace.map(item=>node('li','',item)));
    $('resultSummary').textContent=res.answer;
    const container=$('hits');container.replaceChildren();
    if(!hits.length){const blank=node('div','empty-hits');blank.append(node('span','',decision.primary==='no_rag'?'○':'▤'),node('p','',decision.primary==='no_rag'?'No retrieval necessary':'No matching documents'),node('small','',decision.primary==='no_rag'?'The router intentionally skipped document search.':'Try another query or add an appropriate document.'));container.append(blank);return;}
    for(const h of hits){const wrap=node('article','hit');const header=node('div','hit-top');header.append(node('div','hit-title',h.doc.title),node('div','hit-score',Math.round(h.score*100)+'% score'));wrap.append(header,node('div','hit-source',h.doc.source),node('p','hit-snippet',h.snippet),node('span','hit-method',h.method));container.append(wrap);}
  }
  async function execute(){
    if(running)return;const query=$('query').value.trim();$('queryError').hidden=true;
    if(query.length<2){$('queryError').textContent='Enter at least two characters.';$('queryError').hidden=false;return;}
    running=true;$('run').disabled=true;$('flowStatus').textContent='ROUTING';$('decisionStatus').textContent='ANALYZING';document.querySelector('.flow-card').classList.add('running');
    for(const id of ['inputNode','routerNode','evidenceNode'])$(id).classList.remove('active');
    document.querySelectorAll('.strategy-chip').forEach(el=>el.classList.remove('active'));
    $('inputNode').classList.add('active');
    try{
      // Calculation is deterministic and synchronous; animated pacing is presentation only.
      const res=runQuery(query);
      await new Promise(resolve=>setTimeout(resolve,200));$('routerNode').classList.add('active');
      document.querySelector(`.strategy-chip[data-strategy="${res.decision.primary}"]`).classList.add('active');
      await new Promise(resolve=>setTimeout(resolve,350));renderResult(res);
    }finally{running=false;$('run').disabled=false;document.querySelector('.flow-card').classList.remove('running');}
  }
  $('run').addEventListener('click',execute);
  $('query').addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();execute();}});
  document.querySelectorAll('.example').forEach(button=>button.addEventListener('click',()=>{
    document.querySelectorAll('.example').forEach(el=>el.classList.remove('selected'));button.classList.add('selected');$('query').value=SCENARIOS[button.dataset.scenario];
  }));
  $('reset').addEventListener('click',()=>{docs=SEED.map(d=>({...d}));renderDocs();$('documentError').hidden=true;});
  $('addDocument').addEventListener('click',()=>{
    const title=$('docTitle').value.trim(),text=$('docText').value.trim();
    if(!title||!text){$('documentError').textContent='Both title and document text are required.';$('documentError').hidden=false;return;}
    if(docs.length>=50){$('documentError').textContent='The static preview limits indexing to 50 records.';$('documentError').hidden=false;return;}
    docs.push({id:'user-'+(docs.filter(d=>d.id.startsWith('user-')).length+1)+'-'+Date.now(),title,text,source:'browser://added-document',kind:'text',entities:[]});
    $('docTitle').value='';$('docText').value='';$('documentError').hidden=true;renderDocs();
  });
  renderDocs();
  window.AutoRAGDemo={policy,runQuery,getDocuments:()=>docs.map(d=>({...d})),scenarios:{...SCENARIOS}};
})();
