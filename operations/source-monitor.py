"""JunkRemoval official-source change monitor. Retains review tasks; no automatic article publication."""
import pathlib,json,os,sys,subprocess,hashlib,gzip,urllib.request,datetime,time,concurrent.futures
BASE=pathlib.Path(__file__).resolve().parent
NOW=datetime.datetime.now(datetime.timezone.utc)
def save(p,d):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2)+'\n');temp.replace(p)
subprocess.check_call([sys.executable,str(BASE/'check-inputs.py'),'worker'])
raw=(BASE.parent/'site-sot.json').read_bytes();sot=json.loads(raw)
state_path=BASE/'source-state.json'
state=json.loads(state_path.read_text()) if state_path.exists() else {'schemaVersion':1,'known':{},'tasks':[],'lease':None}
runid=os.getenv('GITHUB_RUN_ID','local-'+str(time.time_ns()))
lease=state.get('lease')
if lease and lease.get('runId')!=runid and datetime.datetime.fromisoformat(lease['expiresAt'])>NOW:
 owner=lease.get('runId','');token=os.getenv('GITHUB_TOKEN');repo=os.getenv('GITHUB_REPOSITORY')
 recovered=False
 if owner.isdigit() and token and repo:
  req=urllib.request.Request('https://api.github.com/repos/'+repo+'/actions/runs/'+owner,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=15) as response:owner_run=json.load(response)
  if owner_run.get('status')=='completed':
   state.setdefault('leaseRecoveries',[]).append({'oldRunId':owner,'oldRunRef':owner_run.get('html_url'),'providerStatus':'completed','conclusion':owner_run.get('conclusion'),'recoveredAt':NOW.isoformat(),'newRunId':runid});recovered=True
 if not recovered:raise RuntimeError('An unexpired monitor lease already owns this queue; provider did not prove its owner completed')
state['lease']={'runId':runid,'expiresAt':(NOW+datetime.timedelta(minutes=20)).isoformat()};save(state_path,state)
if '--acquire' in sys.argv:
 print('Acquired queue lease for '+runid);sys.exit(0)
sources=json.loads((BASE/'sources.json').read_text())
state.setdefault('retries',{})
eligible=[]
deferred=[]
for source in sources:
 retry=state['retries'].get(source['url'],{})
 transport_recheck=retry.get('transportVersion')!=4 and any(term in retry.get('error','').lower() for term in ['timed out','insufficient visible source text'])
 if retry.get('nextEligibleAt') and datetime.datetime.fromisoformat(retry['nextEligibleAt'])>NOW and not transport_recheck:
  deferred.append({'url':source['url'],'title':source['title'],'status':'deferred','nextEligibleAt':retry['nextEligibleAt'],'retainedError':retry.get('error')})
 else:eligible.append(source)
def fetch_source(source):
 result={'url':source['url'],'title':source['title'],'status':'failed','attempts':0}
 for attempt in range(3):
  result['attempts']=attempt+1
  try:
   child_env=dict(os.environ);child_env.pop('GITHUB_TOKEN',None)
   child=subprocess.run([sys.executable,str(BASE/'fetch-source.py'),source['url']],capture_output=True,text=True,timeout=50,check=True,env=child_env)
   data=json.loads(child.stdout);result.update(status='passed',httpStatus=data['httpStatus'],sha256=data['sha256'],hashAlgorithm=data.get('hashAlgorithm','unknown'),textCharacters=data.get('textCharacters'),retrievalMode=data.get('retrievalMode'))
   break
  except Exception as error:
   result['error']=(error.stderr.strip()[-250:] if isinstance(error,subprocess.CalledProcessError) and error.stderr else str(error)[:250])
   if attempt<2:time.sleep(2**attempt)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch_source,eligible))
results+=deferred
for item in results:
 key=item['url'];prev=state['known'].get(key)
 if item['status']=='failed':
  old=state['retries'].get(key,{})
  count=old.get('consecutiveFailures',0)+1
  delay=12*3600 if '403' in item.get('error','') else min(12*3600,1800*(2**min(count-1,5)))
  state['retries'][key]={'consecutiveFailures':count,'lastAttemptAt':NOW.isoformat(),'nextEligibleAt':(NOW+datetime.timedelta(seconds=delay)).isoformat(),'error':item.get('error'),'status':'blocked-provider' if '403' in item.get('error','') else 'retry-pending','transportVersion':4}
 elif item['status']=='passed':
  state['retries'].pop(key,None)
  if prev and prev.get('hashAlgorithm')==item.get('hashAlgorithm')=='visible-text-v1' and prev.get('sha256')!=item['sha256']:
   taskid=hashlib.sha256((key+item['sha256']).encode()).hexdigest()
   if not any(t['id']==taskid for t in state['tasks']):state['tasks'].append({'id':taskid,'url':key,'detectedAt':NOW.isoformat(),'status':'needs-editorial-review','sourceSha256':item['sha256'],'hashAlgorithm':'visible-text-v1','reason':'Primary visible authority text changed. Inspect the actual substantive change before any article update.'})
  state['known'][key]={'sha256':item['sha256'],'hashAlgorithm':item.get('hashAlgorithm'),'textCharacters':item.get('textCharacters'),'observedAt':NOW.isoformat()}
for task in state['tasks']:
 if task.get('hashAlgorithm')!='visible-text-v1':
  task['detectionBasis']='legacy-raw-html-hash';task['reviewNote']='Raw HTML can change without an editorial change. This task is retained for review, not certified as substantive news.'
state['lease']=None;state['lastRunAt']=NOW.isoformat();save(state_path,state)
role_raw=(BASE/'role-sots/worker.json').read_bytes();role_sot=json.loads(role_raw)
event=os.getenv('GITHUB_EVENT_NAME','local');repo=os.getenv('GITHUB_REPOSITORY','SHTFTV/junkremoval-ltd')
status={'site':'junkremoval.ltd','scope':'official-source-monitoring-only','status':'monitoring-complete' if all(x['status']=='passed' for x in results) else 'held','observedAt':NOW.isoformat(),'event':event,'unattended':event=='schedule','runId':runid,'runRef':'https://github.com/'+repo+'/actions/runs/'+runid if event!='local' else None,'sourceCommit':os.getenv('GITHUB_SHA'),'loadedSotRevision':sot['version'],'loadedSotSha256':hashlib.sha256(raw).hexdigest(),'queueRef':'operations/source-state.json','deduplication':'sha256(url+source-content-hash)','lease':'20-minute persisted lease plus workflow concurrency','boundedRetry':'3 attempts per source, hard50-second process deadline per attempt;3attempts; source-specific retained eligibility; bounded HTTP transport permits one early timeout/text-extraction recheck,never resets403 hold','isolation':'per-source results; one source failure does not suppress healthy source results','sources':results,'reviewTasks':len(state['tasks']),'retainedRetries':len(state['retries']),'nextEligibleAt':min((r['nextEligibleAt'] for r in state['retries'].values()),default=None),'loadedRoleSotRevision':role_sot['version'],'loadedRoleSotSha256':hashlib.sha256(role_raw).hexdigest(),'automaticArticlePublication':False,'fourRolesApproved':False}
save(BASE/'source-monitor-status.json',status)
print(json.dumps({'runId':runid,'event':event,'passed':sum(x['status']=='passed' for x in results),'failed':sum(x['status']!='passed' for x in results),'scope':status['scope']}))
