"""Observe actual source/visual receipts, source identity, runtime SOT and public pages."""
import pathlib,json,os,datetime,urllib.request,hashlib,subprocess,re,sys
B=pathlib.Path(__file__).parent;now=datetime.datetime.now(datetime.timezone.utc)
subprocess.check_call([sys.executable,str(B/'check-inputs.py'),'supervisor'])
raw=(B/'role-sots/supervisor.json').read_bytes();sot=json.loads(raw)
def read(name):
 try:return json.loads((B/name).read_text())
 except Exception:return None
def fresh(d,hours=6):
 try:return 0<=(now-datetime.datetime.fromisoformat(d['observedAt'].replace('Z','+00:00'))).total_seconds()<=hours*3600
 except Exception:return False
checks=[]
def check(id,passed,detail):checks.append({'id':id,'passed':bool(passed),'detail':detail})
worker=read('source-monitor-status.json');visual=read('visual-status.json')
def provider_run(receipt,expected_path,expected_event=None):
 ref=(receipt or {}).get('runRef') or '';match=re.fullmatch(r'https://github.com/SHTFTV/junkremoval\.ltd/actions/runs/([0-9]+)',ref)
 if not match:return {'passed':False,'reason':'INVALID_PROVIDER_RUN_REF'}
 try:
  headers={'Accept':'application/vnd.github+json','User-Agent':'JunkRemoval-supervisor'}
  token=os.getenv('GITHUB_TOKEN')
  if token:headers['Authorization']='Bearer '+token
  request=urllib.request.Request('https://api.github.com/repos/SHTFTV/junkremoval.ltd/actions/runs/'+match.group(1),headers=headers)
  with urllib.request.urlopen(request,timeout=20) as response:run=json.load(response)
  expected_head=receipt.get('sourceCommit',receipt.get('observerSourceCommit'))
  good=run.get('status')=='completed' and run.get('conclusion')=='success' and run.get('head_sha')==expected_head and run.get('event')==receipt.get('event') and run.get('path')==expected_path and (not expected_event or run.get('event')==expected_event)
  return {'passed':good,'runRef':ref,'providerStatus':run.get('status'),'conclusion':run.get('conclusion'),'head':run.get('head_sha'),'event':run.get('event'),'workflow':run.get('path')}
 except Exception:return {'passed':False,'runRef':ref,'reason':'PROVIDER_RUN_LOOKUP_FAILED'}
worker_provider=provider_run(worker,'.github/workflows/source-monitor.yml','schedule')
visual_provider=provider_run(visual,'.github/workflows/visual-supervisor.yml','schedule')
check('worker-provider',worker_provider['passed'],worker_provider)
check('visual-provider',visual_provider['passed'],visual_provider)
def receipt_inputs(receipt,paths):
 commit=(receipt or {}).get('sourceCommit') or (receipt or {}).get('observerSourceCommit')
 if not isinstance(commit,str) or not re.fullmatch(r'[0-9a-f]{40}',commit):return False
 try:return all(subprocess.check_output(['git','show',commit+':'+name],stderr=subprocess.DEVNULL)==(B.parent/name).read_bytes() for name in paths)
 except Exception:return False
parent_raw=(B.parent/'site-sot.json').read_bytes();parent_sot=json.loads(parent_raw)
check('worker-parent-sot',bool(worker) and worker.get('loadedSotRevision')==parent_sot['version'] and worker.get('loadedSotSha256')==hashlib.sha256(parent_raw).hexdigest(),{'expectedVersion':parent_sot['version']})
worker_inputs=['operations/source-monitor.py','operations/fetch-source.py','operations/sources.json','operations/role-sots/worker.json','site-sot.json']
visual_inputs=['operations/visual-check.cjs','operations/role-sots/visual-checker.json','operations/render-review.json','site-sot.json','index.html','guides/index.html','guides/choosing-junk-removal-truck-trailer-hooklift/index.html','planner/index.html','publication-status.json']+[str(x.relative_to(B.parent)) for x in (B.parent/'assets').rglob('*') if x.is_file()]
check('worker-current-inputs',receipt_inputs(worker,worker_inputs),{'comparedInputCount':len(worker_inputs)})
check('visual-current-inputs',receipt_inputs(visual,visual_inputs),{'comparedInputCount':len(visual_inputs)})

for name,receipt,policy_file in [('worker',worker,'worker.json'),('visual',visual,'visual-checker.json')]:
 role_raw=(B/'role-sots'/policy_file).read_bytes();role=json.loads(role_raw)
 check(name+'-policy',bool(receipt) and receipt.get('site')=='junkremoval.ltd' and receipt.get('loadedRoleSotRevision',receipt.get('loadedRevision'))==role['version'] and receipt.get('loadedRoleSotSha256',receipt.get('loadedHash'))==hashlib.sha256(role_raw).hexdigest(),{'rolePolicy':policy_file,'runRef':(receipt or {}).get('runRef')})
check('worker-native',fresh(worker) and worker.get('unattended') is True and worker.get('event')=='schedule' and str(worker.get('runRef','')).startswith('https://github.com/SHTFTV/junkremoval.ltd/actions/runs/'),{'run':(worker or {}).get('runRef'),'fresh':fresh(worker),'event':(worker or {}).get('event')})
failed=[x for x in (worker or {}).get('sources',[]) if x['status'] in ['failed','deferred']];check('sources',bool((worker or {}).get('sources')) and not failed,{'failedSources':failed,'healthySources':sum(x['status']=='passed' for x in (worker or {}).get('sources',[]))})
check('visual',fresh(visual) and visual.get('status')=='passed' and visual.get('renderReviewVerified') is True,{'run':(visual or {}).get('runRef'),'status':(visual or {}).get('status','missing'),'renderReviewVerified':(visual or {}).get('renderReviewVerified',False)})
for origin,name in [(sot['preview'],'preview'),(sot['canonical'],'canonical')]:
 try:
  r=urllib.request.urlopen(origin+'/',timeout=30);body=r.read(2_000_000).decode();check(name+'-homepage',r.status==200 and 'A clearer space.' in body,{'status':r.status,'finalUrl':r.url,'expectedText':'A clearer space.' in body})
 except Exception as e:check(name+'-homepage',False,str(e)[:200])
try:
 api=json.load(urllib.request.urlopen(sot['preview']+'/api/operations/',timeout=30));parent=(B.parent/'site-sot.json').read_bytes();check('api-sot',api.get('site')=='junkremoval.ltd' and api.get('loadedSotRevision')==json.loads(parent)['version'] and api.get('loadedSotSha256')==hashlib.sha256(parent).hexdigest(),{'site':api.get('site'),'loadedSotRevision':api.get('loadedSotRevision'),'loadedSotSha256':api.get('loadedSotSha256')})
 deployed=api.get('deploymentSourceCommit');ancestor=False
 if deployed:ancestor=subprocess.run(['git','merge-base','--is-ancestor',deployed,'HEAD'],capture_output=True).returncode==0
 public_inputs=subprocess.check_output(['git','ls-files','--','*.html','assets/*','site-sot.json','publication-status.json'],text=True).splitlines()
 check('deployed-public-source',bool(public_inputs) and receipt_inputs({'sourceCommit':deployed},public_inputs),{'deploymentSourceCommit':deployed,'comparedInputCount':len(public_inputs)})
 check('deployment-source',bool(deployed) and ancestor and api.get('sourceMonitorRun')==(worker or {}).get('runRef'),{'actualDeploymentSourceCommit':deployed,'checkoutCommit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'actualGitAncestry':ancestor,'deployedWorkerRunRef':api.get('sourceMonitorRun'),'expectedWorkerRunRef':(worker or {}).get('runRef')})
except Exception as e:check('api-sot',False,str(e)[:200])
publication_checks=[]
manifest=json.loads((B.parent/'publication-status.json').read_text())
for article in manifest.get('posts',[]):
 route='/guides/'+article['slug']+'/'
 try:
  response=urllib.request.urlopen(sot['preview']+route,timeout=25);live=response.read(2_000_000);committed=(B.parent/route.strip('/')/'index.html').read_bytes();publication_checks.append({'url':sot['preview']+route,'status':response.status,'exactCommittedHtml':live==committed})
 except Exception as error:publication_checks.append({'url':sot['preview']+route,'error':str(error)[:180]})
check('actual-editorial-pages',bool(publication_checks) and all(x.get('status')==200 and x.get('exactCommittedHtml') for x in publication_checks),publication_checks)
state=read('source-state.json');check('retained-queue',isinstance(state.get('tasks') if state else None,list) and isinstance(state.get('retries') if state else None,dict),{'queue':'operations/source-state.json','pending':len((state or {}).get('tasks',[])),'retries':len((state or {}).get('retries',{}))})
result={'site':'junkremoval.ltd','role':'supervisor','observedAt':now.isoformat(),'event':os.getenv('GITHUB_EVENT_NAME','local'),'runRef':'https://github.com/'+os.getenv('GITHUB_REPOSITORY','SHTFTV/junkremoval.ltd')+'/actions/runs/'+os.getenv('GITHUB_RUN_ID','local'),'observerSourceCommit':os.getenv('GITHUB_SHA'),'actorId':'junkremoval-supervisor','executionProvider':'github','loadedRevision':sot['version'],'loadedHash':hashlib.sha256(raw).hexdigest(),'pageQualityVersion':1,'checkedWorkerRunRef':(worker or {}).get('runRef'),'checkedVisualRunRef':(visual or {}).get('runRef'),'actualSourceApiDeploymentPublicationChecks':True,'status':'passed' if all(c['passed'] for c in checks) else 'held','checks':checks,'automaticArticlePublication':False,'fourRolesApproved':False}
(B/'supervisor-status.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'role':'supervisor','status':result['status'],'failed':[c['id'] for c in checks if not c['passed']]}))
