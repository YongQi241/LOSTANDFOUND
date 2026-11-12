import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { PGlite } from '@electric-sql/pglite';

const here = new URL('./', import.meta.url);
const db = new PGlite();
const results = [];
const q = (sql, args=[]) => db.query(sql,args);
const one = async (sql,args=[]) => (await q(sql,args)).rows[0];
async function tx(fn) {
  await db.exec('BEGIN');
  try { const result=await fn(); await db.exec('COMMIT'); return result; }
  catch(error) { await db.exec('ROLLBACK'); throw error; }
}
async function rejected(fn,codes) {
  let error;
  try { await fn(); } catch(e) { error=e; }
  assert.ok(error,'Expected database rejection');
  assert.ok(codes.includes(error.code),`Expected ${codes}, got ${error.code}: ${error.message}`);
}
async function as(role,fn) {
  assert.ok(['lf_api','lf_auth','lf_catalog','anon','authenticated'].includes(role));
  await db.exec(`SET ROLE ${role}`);
  try { return await fn(); } finally { await db.exec('RESET ROLE'); }
}
async function test(name,fn) {
  try { await fn(); results.push({name,passed:true}); console.log(`PASS ${name}`); }
  catch(error) { results.push({name,passed:false,error:error.message}); throw error; }
}
const ids=Object.fromEntries(['university','campus','category','owner','a','b','other','r1','r2','r3','admin','unverified','banned'].map(x=>[x,randomUUID()]));
const state=async p=>one('SELECT status,previous_status FROM app.posts WHERE post_id=$1',[p]);
async function post(type='FOUND',owner=ids.owner,{image=true,contact=true}={}) {
  const id=randomUUID();
  await tx(async()=>{
    await q(`INSERT INTO app.posts(post_id,owner_id,campus_id,category_id,post_type,title,incident_at,verification_question)
      VALUES($1,$2,$3,$4,$5,$6,CURRENT_TIMESTAMP-interval '1 day',$7)`,
      [id,owner,ids.campus,ids.category,type,`Fixture ${id}`,type==='FOUND'?'Describe the item':null]);
    if(contact) await q('SELECT app.write_post_contact($1,$2,$3,$4)',[owner,id,'PHONE','0901234567']);
    if(image) await q(`INSERT INTO app.post_images(post_id,position,object_key,mime_type,size_bytes)
      VALUES($1,1,$2,'image/jpeg',1000)`,[id,`posts/${id}/1.jpg`]);
  });
  return id;
}
async function claim(p,user=ids.a,{answer='Correct fixture answer',message=null,proof=false}={}) {
  return as('lf_api',async()=> (await one('SELECT app.submit_claim($1,$2,$3,$4,$5,$6,$7) AS id',
    [user,p,answer,message,proof?`claims/${randomUUID()}.png`:null,proof?'image/png':null,proof?1000:null])).id);
}
async function decide(pClaim,action='ACCEPT',actor=ids.owner) {
  return as('lf_api',()=>q('SELECT app.decide_claim($1,$2,$3)',[actor,pClaim,action]));
}
async function report(p,who) { return as('lf_api',()=>q('SELECT app.report_post($1,$2,$3)',[who,p,'SPAM'])); }
async function reportedPost(type='FOUND') {
  const p=await post(type);
  for(const who of [ids.r1,ids.r2,ids.r3]) await report(p,who);
  return p;
}
async function review(p,action='KEEP',reason=null,actor=ids.admin) {
  return as('lf_api',()=>q('SELECT app.review_post($1,$2,$3,$4)',[actor,p,action,reason]));
}

let engine;
try {
  // Test-only stand-ins: no Supabase Auth/SMTP/Storage service is being tested.
  await db.exec('CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY); CREATE ROLE anon NOLOGIN; CREATE ROLE authenticated NOLOGIN;');
  await db.exec(await readFile(new URL('schema.sql',here),'utf8'));
  await db.exec(await readFile(new URL('rules.sql',here),'utf8'));
  engine=(await one('SELECT version() AS version')).version;
  await tx(async()=>{
    await q(`INSERT INTO app.universities(university_id,code,name) VALUES($1,'FIXTURE','Fixture University')`,[ids.university]);
    await q(`INSERT INTO app.university_domains VALUES('student.example.edu.vn',$1)`,[ids.university]);
    await q(`INSERT INTO app.campuses(campus_id,university_id,name,address) VALUES($1,$2,'Main','Fixture Address')`,[ids.campus,ids.university]);
    await q(`INSERT INTO app.categories(category_id,name) VALUES($1,'Fixture category')`,[ids.category]);
    for(const name of ['owner','a','b','other','r1','r2','r3','admin','unverified','banned']) {
      const id=ids[name];
      await q('INSERT INTO auth.users VALUES($1)',[id]);
      await q(`INSERT INTO app.users(user_id,full_name,role,is_verified,status,ban_reason)
        VALUES($1,$2,$3,$4,$5,$6)`,[id,`Fixture ${name}`,name==='admin'?'ADMIN':'STUDENT',name!=='unverified',name==='banned'?'BANNED':'ACTIVE',name==='banned'?'FIXTURE_BAN':null]);
      await q(`INSERT INTO private.user_contacts VALUES($1,$2,'student.example.edu.vn',NULL)`,[id,`${name}@student.example.edu.vn`]);
    }
  });
  await test('17 tables / 126 columns / 27 foreign keys materialise',async()=>{
    const r=await one(`SELECT count(*)::int AS n FROM information_schema.tables WHERE table_schema IN ('app','private') AND table_type='BASE TABLE'`);
    assert.equal(r.n,17);
    const model=JSON.parse(await readFile(new URL('model.json',here),'utf8'));
    for(const t of model.tables) {
      const [schema,name]=t.name.split('.');
      assert.equal((await one('SELECT count(*)::int AS n FROM information_schema.columns WHERE table_schema=$1 AND table_name=$2',[schema,name])).n,t.columns.length);
    }
    assert.equal((await one(`SELECT count(*)::int AS n FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY' AND table_schema IN ('app','private')`)).n,27);
  });
  await test('NOT NULL and foreign keys reject invalid session',async()=>{
    await rejected(()=>q(`INSERT INTO app.sessions(session_id,user_id,expires_at) VALUES($1,NULL,CURRENT_TIMESTAMP+interval '1 hour')`,[randomUUID()]),['23502']);
    await rejected(()=>q(`INSERT INTO app.sessions(session_id,user_id,expires_at) VALUES($1,$2,CURRENT_TIMESTAMP+interval '1 hour')`,[randomUUID(),randomUUID()]),['23503']);
  });
  await test('Case-insensitive category uniqueness',()=>rejected(()=>q(`INSERT INTO app.categories(name) VALUES('FIXTURE CATEGORY')`),['23505']));
  await test('BR-01: unverified and banned users cannot create posts',async()=>{
    await rejected(()=>post('FOUND',ids.unverified),['23514']);
    await rejected(()=>post('FOUND',ids.banned),['23514']);
  });
  await test('Deferred one-contact and minimum-one-image constraints',async()=>{
    await rejected(()=>post('FOUND',ids.owner,{image:false}),['23514']);
    await rejected(()=>post('FOUND',ids.owner,{contact:false}),['23514']);
  });
  await test('Image slot, MIME, size checks and maximum five images',async()=>{
    const p=await post();
    for(let i=2;i<=5;i++) await q(`INSERT INTO app.post_images(post_id,position,object_key,mime_type,size_bytes) VALUES($1,$2,$3,'image/png',1000)`,[p,i,`${p}/${i}.png`]);
    await rejected(()=>q(`INSERT INTO app.post_images(post_id,position,object_key,mime_type,size_bytes) VALUES($1,6,$2,'image/png',1000)`,[p,`${p}/6.png`]),['23514']);
    await rejected(()=>q(`UPDATE app.post_images SET mime_type='image/webp' WHERE post_id=$1`,[p]),['23514']);
    await rejected(()=>q(`UPDATE app.post_images SET size_bytes=5242881 WHERE post_id=$1`,[p]),['23514']);
  });
  await test('FOUND requires question and answer; answer alone is sufficient',async()=>{
    const p=await post();
    await rejected(()=>claim(p,ids.a,{answer:null,proof:true}),['23514']);
    await claim(p,ids.a);
  });
  await test('LOST accepts message OR image, rejects neither',async()=>{
    const p=await post('LOST');
    await rejected(()=>claim(p,ids.a,{answer:null}),['23514']);
    await claim(p,ids.a,{answer:null,message:'Found near the library'});
    await claim(p,ids.b,{answer:null,proof:true});
  });
  await test('Reject self / unverified / banned Claimants',async()=>{
    const p=await post();
    for(const who of [ids.owner,ids.unverified,ids.banned]) await rejected(()=>claim(p,who),['23514']);
  });
  await test('One PENDING per Post/User, resend after REJECTED allowed',async()=>{
    const p=await post(); const c=await claim(p);
    await rejected(()=>claim(p),['23505']);
    await decide(c,'REJECT');
    const c2=await claim(p); assert.notEqual(c,c2);
    assert.equal((await state(p)).status,'ACTIVE');
  });
  await test('Only owner decides; null decision is rejected',async()=>{
    const p=await post(); const c=await claim(p);
    await rejected(()=>decide(c,'ACCEPT',ids.other),['42501']);
    await rejected(()=>decide(c,null),['P0001']);
  });
  await test('BR-02: Guest/student/PENDING/Admin cannot read foreign contact',async()=>{
    const p=await post(); const c=await claim(p);
    for(const who of [null,ids.a,ids.other,ids.admin]) {
      await rejected(()=>as('lf_api',()=>q('SELECT * FROM app.read_post_contact($1,$2)',[who,p])),['42501']);
    }
    await rejected(()=>as('lf_api',()=>q('SELECT * FROM app.read_claimant_contact($1,$2)',[ids.owner,c])),['42501']);
    assert.equal((await as('lf_api',()=>one('SELECT * FROM app.read_post_contact($1,$2)',[ids.owner,p]))).contact_value,'0901234567');
  });
  await test('ACCEPT atomically resolves Post, rejects others and opens both contacts',async()=>{
    const p=await post(); const c=await claim(p); const c2=await claim(p,ids.b);
    await decide(c);
    assert.equal((await state(p)).status,'RESOLVED');
    assert.deepEqual((await q('SELECT status FROM app.claims WHERE post_id=$1 ORDER BY status',[p])).rows.map(x=>x.status),['ACCEPTED','REJECTED']);
    assert.equal((await as('lf_api',()=>one('SELECT * FROM app.read_post_contact($1,$2)',[ids.a,p]))).contact_value,'0901234567');
    assert.equal((await as('lf_api',()=>one('SELECT * FROM app.read_claimant_contact($1,$2)',[ids.owner,c]))).contact_value,'a@student.example.edu.vn');
    await rejected(()=>as('lf_api',()=>q('SELECT * FROM app.read_post_contact($1,$2)',[ids.b,p])),['42501']);
    assert.equal((await one(`SELECT count(*)::int AS n FROM app.notifications WHERE post_id=$1 AND event_type='CLAIM_DECIDED'`,[p])).n,2);
    await rejected(()=>decide(c2),['P0001']);
    await rejected(()=>claim(p,ids.other),['23514']);
  });
  await test('Partial UNIQUE prevents two ACCEPTED even before Post update',async()=>{
    const p=await post(); const a=await claim(p); const b=await claim(p,ids.b);
    await rejected(()=>tx(async()=>{
      await q(`UPDATE app.claims SET status='ACCEPTED',decided_at=clock_timestamp() WHERE claim_id=$1`,[a]);
      await q(`UPDATE app.claims SET status='ACCEPTED',decided_at=clock_timestamp() WHERE claim_id=$1`,[b]);
    }),['23505']);
    assert.equal((await one(`SELECT count(*)::int AS n FROM app.claims WHERE post_id=$1 AND status='ACCEPTED'`,[p])).n,0);
  });
  await test('Deferred invariant rejects accepting without resolving/rejecting others',async()=>{
    const p=await post(); const c=await claim(p);
    await rejected(()=>tx(()=>q(`UPDATE app.claims SET status='ACCEPTED',decided_at=clock_timestamp() WHERE claim_id=$1`,[c])),['23514']);
    assert.equal((await state(p)).status,'ACTIVE');
  });
  await test('Injected error rolls back Claim, Post and notification',async()=>{
    const p=await post(); const c=await claim(p);
    await rejected(()=>tx(async()=>{
      await q('SELECT app.decide_claim($1,$2,$3)',[ids.owner,c,'ACCEPT']);
      await q('SELECT 1/0');
    }),['22012']);
    assert.equal((await state(p)).status,'ACTIVE');
    assert.equal((await one('SELECT status FROM app.claims WHERE claim_id=$1',[c])).status,'PENDING');
    assert.equal((await one(`SELECT count(*)::int AS n FROM app.notifications WHERE post_id=$1 AND event_type='CLAIM_DECIDED'`,[p])).n,0);
  });
  await test('Manual resolution does not grant contact access',async()=>{
    const p=await post();
    await q(`UPDATE app.posts SET status='RESOLVED' WHERE post_id=$1`,[p]);
    await rejected(()=>as('lf_api',()=>q('SELECT * FROM app.read_post_contact($1,$2)',[ids.a,p])),['42501']);
  });
  await test('Question locked when pending Claim exists',async()=>{
    const p=await post(); await claim(p);
    await rejected(()=>q(`UPDATE app.posts SET verification_question='Changed' WHERE post_id=$1`,[p]),['23514']);
  });
  await test('BR-03: third DISTINCT reporter hides Post; duplicate cannot inflate count',async()=>{
    const p=await post(); await report(p,ids.r1); await report(p,ids.r2);
    await rejected(()=>report(p,ids.r1),['23505']); assert.equal((await state(p)).status,'ACTIVE');
    await report(p,ids.r3); assert.deepEqual(await state(p),{status:'REPORTED',previous_status:'ACTIVE'});
    assert.equal((await one('SELECT count(*)::int AS n FROM app.public_posts WHERE post_id=$1',[p])).n,0);
  });
  await test('KEEP restores previous state; handled reports do not re-hide',async()=>{
    const p=await reportedPost(); await review(p);
    assert.deepEqual(await state(p),{status:'ACTIVE',previous_status:null});
    assert.equal((await one(`SELECT count(*)::int AS n FROM app.reports WHERE post_id=$1 AND status='PENDING'`,[p])).n,0);
    await rejected(()=>report(p,ids.r1),['23505']);
    await report(p,ids.a); assert.equal((await state(p)).status,'ACTIVE');
    await report(p,ids.b); await report(p,ids.other); assert.equal((await state(p)).status,'REPORTED');
  });
  await test('KEEP preserves RESOLVED and accepted contact rights',async()=>{
    const p=await post(); const c=await claim(p); await decide(c);
    for(const who of [ids.r1,ids.r2,ids.r3]) await report(p,who);
    assert.equal((await state(p)).previous_status,'RESOLVED'); await review(p);
    assert.equal((await state(p)).status,'RESOLVED');
    await as('lf_api',()=>q('SELECT * FROM app.read_post_contact($1,$2)',[ids.a,p]));
  });
  await test('REMOVE requires Admin and reason; cancels pending and preserves audit',async()=>{
    const p=await post(); const c=await claim(p);
    for(const who of [ids.r1,ids.r2,ids.r3]) await report(p,who);
    await rejected(()=>review(p,'REMOVE','Violation',ids.other),['42501']);
    await rejected(()=>review(p,'REMOVE'),['23514']);
    await review(p,'REMOVE','Violation'); assert.equal((await state(p)).status,'CLOSED');
    assert.equal((await one('SELECT status FROM app.claims WHERE claim_id=$1',[c])).status,'CANCELLED');
    assert.equal((await one('SELECT count(*)::int AS n FROM app.moderation_actions WHERE post_id=$1',[p])).n,1);
  });
  await test('Public projection has no protected columns',async()=>{
    const names=(await q(`SELECT column_name FROM information_schema.columns WHERE table_schema='app' AND table_name='public_posts'`)).rows.map(x=>x.column_name);
    for(const forbidden of ['contact_value','phone_number','university_email','security_answer','proof_object_key','private_identifier','storage_location']) assert.ok(!names.includes(forbidden));
  });
  await test('anon/authenticated cannot bypass API via schema or RPC',async()=>{
    for(const role of ['anon','authenticated']) {
      await rejected(()=>as(role,()=>q('SELECT * FROM app.public_posts')),['42501']);
      await rejected(()=>as(role,()=>q('SELECT * FROM app.read_post_contact($1,$2)',[ids.a,randomUUID()])),['42501']);
    }
  });
  await test('Backend API cannot SELECT private contacts; auth column grant excludes phone',async()=>{
    await rejected(()=>as('lf_api',()=>q('SELECT contact_value FROM private.post_details')),['42501']);
    await rejected(()=>as('lf_api',()=>q('SELECT university_email FROM private.user_contacts')),['42501']);
    assert.ok((await as('lf_auth',()=>q('SELECT university_email FROM private.user_contacts'))).rows.length>0);
    await rejected(()=>as('lf_auth',()=>q('SELECT phone_number FROM private.user_contacts')),['42501']);
  });
  await test('Soft deletion/history: API has no DELETE and audit cannot be edited',async()=>{
    await rejected(()=>as('lf_api',()=>q('DELETE FROM app.claims')),['42501']);
    await rejected(()=>as('lf_api',()=>q(`UPDATE app.moderation_actions SET reason='tamper'`)),['42501']);
    await rejected(()=>q(`UPDATE app.moderation_actions SET reason='tamper'`),['23514']);
  });
  await test('Pending school-domain uniqueness; catalog role does not read user contacts',async()=>{
    const input=`INSERT INTO private.school_requests(university_name,email_domain,contact_name,contact_email)
      VALUES('New fixture','new.example.edu.vn','Representative','rep@example.test')`;
    await as('lf_catalog',()=>db.exec(input));
    await rejected(()=>as('lf_catalog',()=>db.exec(input)),['23505']);
    await rejected(()=>as('lf_catalog',()=>q('SELECT university_email FROM private.user_contacts')),['42501']);
  });
  await test('All explicit indexes exist; all app tables have RLS',async()=>{
    const model=JSON.parse(await readFile(new URL('model.json',here),'utf8'));
    const actual=new Set((await q(`SELECT indexname FROM pg_indexes WHERE schemaname IN ('app','private')`)).rows.map(x=>x.indexname));
    for(const idx of model.indexes) assert.ok(actual.has(idx[0]),idx[0]);
    assert.equal((await one(`SELECT count(*)::int AS n FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('app','private') AND c.relkind='r' AND c.relrowsecurity`)).n,17);
  });
  await test('RESOLVED cannot be owner-deleted or edited',async()=>{
    const p=await post(); await q(`UPDATE app.posts SET status='RESOLVED' WHERE post_id=$1`,[p]);
    await rejected(()=>q(`UPDATE app.posts SET status='CLOSED',close_reason='OWNER_DELETED',closed_at=clock_timestamp() WHERE post_id=$1`,[p]),['23514']);
    await rejected(()=>q(`UPDATE app.posts SET title='Changed after resolution' WHERE post_id=$1`,[p]),['23514']);
  });
  await test('Owner ban hides existing posts and closes foreign contact access without changing Post state',async()=>{
    const p=await post('FOUND',ids.r1); const c=await claim(p); await decide(c,'ACCEPT',ids.r1);
    await q(`UPDATE app.users SET status='BANNED',ban_reason='FIXTURE_BAN' WHERE user_id=$1`,[ids.r1]);
    assert.equal((await state(p)).status,'RESOLVED');
    assert.equal((await one('SELECT count(*)::int AS n FROM app.public_posts WHERE post_id=$1',[p])).n,0);
    await rejected(()=>as('lf_api',()=>q('SELECT * FROM app.read_post_contact($1,$2)',[ids.a,p])),['42501']);
  });
  await test('Owner-feed query can use its intended index (planner capability, not benchmark)',async()=>{
    await db.exec('SET enable_seqscan=off');
    try {
      const plan=(await q(`EXPLAIN SELECT post_id FROM app.posts WHERE owner_id=$1 ORDER BY created_at DESC,post_id DESC LIMIT 20`,[ids.owner])).rows.map(x=>x['QUERY PLAN']).join('\n');
      assert.ok(plan.includes('post_owner_idx'),plan);
    } finally { await db.exec('RESET enable_seqscan'); }
  });
  await test('Deliberate context replicas reject mismatched Claim/Post, event code and report audit',async()=>{
    const p=await post(); const other=await post(); const c=await claim(p);
    await rejected(()=>q(`INSERT INTO app.notifications(recipient_id,post_id,claim_id,event_type,message_code)
      VALUES($1,$2,$3,'CLAIM_RECEIVED','CLAIM_RECEIVED')`,[ids.owner,other,c]),['23514']);
    await rejected(()=>q(`INSERT INTO app.notifications(recipient_id,post_id,claim_id,event_type,message_code)
      VALUES($1,$2,$3,'CLAIM_RECEIVED','CLAIM_ACCEPTED')`,[ids.owner,p,c]),['23514']);
    await report(p,ids.r2);
    const audit=(await one(`INSERT INTO app.moderation_actions(admin_id,post_id,action)
      VALUES($1,$2,'KEEP_POST') RETURNING action_id`,[ids.admin,other])).action_id;
    await rejected(()=>q(`UPDATE app.reports SET status='DISMISSED',action_id=$1 WHERE post_id=$2`,[audit,p]),['23514']);
    const matching=(await one(`INSERT INTO app.moderation_actions(admin_id,post_id,action)
      VALUES($1,$2,'KEEP_POST') RETURNING action_id`,[ids.admin,p])).action_id;
    await rejected(()=>q(`UPDATE app.reports SET status='APPROVED',action_id=$1 WHERE post_id=$2`,[matching,p]),['23514']);
    await q(`UPDATE app.reports SET status='DISMISSED',action_id=$1 WHERE post_id=$2`,[matching,p]);
  });
} finally {
  const report={date:'2026-11-12',engine,runner:'PGlite 0.5.16, isolated in-memory PostgreSQL',
    passed:results.filter(x=>x.passed).length,failed:results.filter(x=>!x.passed).length,results,
    limits:['auth.users is a test stub; Supabase Auth/SMTP/Storage are not exercised',
      'No HTTP API, live Supabase deployment, parallel-session race test or NFR load benchmark was run',
      'Actor UUID parameters are trusted backend inputs, not independent authentication']};
  await writeFile(new URL('verification-results.json',here),JSON.stringify(report,null,2)+'\n');
  await db.close();
  console.log(`\n${report.passed} passed, ${report.failed} failed; evidence: ${fileURLToPath(new URL('verification-results.json',here))}`);
}
