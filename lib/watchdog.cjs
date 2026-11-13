const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const ROOT=process.cwd();
function read(name){try{return JSON.parse(fs.readFileSync(path.join(ROOT,'operations',name)));}catch{return null;}}
function evaluate({worker,supervisor,now=Date.now(),ttl=6*3600000}){
 const stale=d=>!d?.observedAt||!Number.isFinite(Date.parse(d.observedAt))||now-Date.parse(d.observedAt)>ttl||Date.parse(d.observedAt)>now;
 const failures=[];
 if(stale(worker))failures.push('worker heartbeat missing/stale');
 if(stale(supervisor))failures.push('supervisor heartbeat missing/stale');
 if(worker?.site!=='junkremoval.ltd'||worker?.status!=='monitoring-complete'||!Array.isArray(worker?.sources)||!worker.sources.length||worker.sources.some(x=>x.status!=='passed'))failures.push('worker source monitoring incomplete/held');
 if(worker?.event!=='schedule'||worker?.unattended!==true)failures.push('worker native scheduled run unverified');
 if(supervisor?.site!=='junkremoval.ltd'||supervisor?.status!=='passed')failures.push('supervisor status '+(supervisor?.status??'missing'));
 if(supervisor?.event!=='schedule')failures.push('supervisor native scheduled run unverified');
 if(!worker?.runRef||supervisor?.checkedWorkerRunRef!==worker.runRef)failures.push('supervisor has not checked current worker run');
 return {status:failures.length?'held':'passed',failures,workerSilent:stale(worker),supervisorSilent:stale(supervisor)};
}
function observe(){
 const raw=fs.readFileSync(path.join(ROOT,'operations/role-sots/independent-watchdog.json')),sot=JSON.parse(raw),worker=read('source-monitor-status.json'),supervisor=read('supervisor-status.json'),result=evaluate({worker,supervisor}),checkedAt=new Date().toISOString(),basis=supervisor?.runRef??'missing-supervisor',id='junkremoval-watchdog-'+crypto.createHash('sha256').update(basis+'|'+(worker?.runRef??'missing-worker')+'|'+result.failures.join('|')).digest('hex').slice(0,20);
 return {site:'junkremoval.ltd',role:'independent-watchdog',scope:'source-monitor-and-supervisor-observation-only',executionProvider:'vercel',actorId:'junkremoval-vercel-watchdog',observedAt:checkedAt,loadedRevision:sot.version,loadedHash:crypto.createHash('sha256').update(raw).digest('hex'),pageQualityVersion:1,deploymentSourceCommit:process.env.VERCEL_GIT_COMMIT_SHA??null,checkedWorkerRunRef:worker?.runRef??null,checkedSupervisorRunRef:supervisor?.runRef??null,...result,incident:{id,status:result.status==='passed'?'recovered':'failed',title:'JunkRemoval.ltd independent watchdog: '+(result.failures.join('; ')||'fresh role heartbeats'),runUrl:supervisor?.runRef??'https://junkremoval-ltd.vercel.app/api/watchdog',at:checkedAt},probe:{id:'junkremoval-watchdog-controlled-silence-v1',status:'failed',title:'Controlled logic test: JunkRemoval worker and supervisor silence',synthetic:true,canary:true,at:checkedAt,result:evaluate({worker:null,supervisor:null})},nativeExecutionVerified:false,ownerDeliveryVerified:false,automaticArticlePublication:false,fourRolesApproved:false};
}
module.exports={observe,evaluate,read};
