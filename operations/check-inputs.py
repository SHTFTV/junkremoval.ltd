"""Reject stale runtime inputs before work and again after rebasing state-only commits."""
import pathlib,subprocess,os,re,sys
BASE=pathlib.Path(__file__).resolve().parent.parent
COMMON=['operations/check-inputs.py','operations/persist-state.sh','site-sot.json']
def paths_for(role):
 if role=='worker':return COMMON+['operations/source-monitor.py','operations/fetch-source.py','operations/sources.json','operations/role-sots/worker.json','.github/workflows/source-monitor.yml']
 if role=='visual':
  public=subprocess.check_output(['git','ls-files','--','*.html','assets/*','publication-status.json'],cwd=BASE,text=True).splitlines()
  return COMMON+['operations/visual-check.cjs','operations/package.json','operations/render-review.json','operations/role-sots/visual-checker.json','.github/workflows/visual-supervisor.yml']+public
 if role=='supervisor':return COMMON+['operations/supervisor.py','operations/role-sots/supervisor.json','.github/workflows/supervisor.yml']
 raise ValueError('INPUT_SCOPE_INVALID')
def verify(role,head=None):
 head=head or os.getenv('GITHUB_SHA')
 if not head:return False
 if not re.fullmatch(r'[0-9a-f]{40}',head):raise ValueError('PROVIDER_HEAD_INVALID')
 for name in sorted(set(paths_for(role))):
  expected=subprocess.check_output(['git','show',head+':'+name],cwd=BASE,stderr=subprocess.DEVNULL)
  if expected!=(BASE/name).read_bytes():raise RuntimeError('RUNTIME_INPUT_CHANGED:'+name)
 return True
if __name__=='__main__':
 native=verify(sys.argv[1]);print('Runtime inputs match provider head' if native else 'Local check only; no provider head or unattended proof')
