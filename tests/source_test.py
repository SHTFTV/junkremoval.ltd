import unittest,importlib.util,pathlib,urllib.parse,ast,json,types,re,io,tempfile,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_fetch',ROOT/'operations/fetch-source.py');fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)
class ScopeTests(unittest.TestCase):
 def test_visible_primary_text_ignores_scripts_and_navigation(self):
  self.assertEqual(fetch.visible_text('<nav>wrong</nav><main>A <b>useful</b> source<script>bad</script></main><footer>footer</footer>'),'A useful source')
 def test_controls_credentials_and_private_redirects_rejected(self):
  for url in ['http://www.gov.uk/a','https://u:p@www.gov.uk/a','https://www.gov.uk/\n//127.0.0.1/','https://www.gov.uk\\@127.0.0.1/','https://www.gov.uk:444/a']:
   with self.assertRaises(ValueError):fetch.scoped_url(url)
  with self.assertRaises(ValueError):fetch.scoped_url('https://127.0.0.1/a',urllib.parse.urlsplit('https://www.gov.uk/a'))
 def test_unlisted_url_rejected_before_network(self):
  with self.assertRaises(ValueError):fetch.fetch('https://www.gov.uk/unapproved-path')
 def test_same_origin_official_redirect_allowed(self):
  self.assertEqual(fetch.scoped_url('https://www.gov.uk/b',urllib.parse.urlsplit('https://www.gov.uk/a')).hostname,'www.gov.uk')
 def test_provider_proof_requires_exact_event_head_and_workflow(self):
  tree=ast.parse((ROOT/'operations/supervisor.py').read_text());function=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='provider_run')
  body={'status':'completed','conclusion':'success','head_sha':'a'*40,'event':'schedule','path':'.github/workflows/source-monitor.yml'}
  class Response(io.StringIO):
   def __enter__(self):return self
   def __exit__(self,*args):self.close()
  request=types.SimpleNamespace(Request=lambda url,headers:None,urlopen=lambda req,timeout:Response(json.dumps(body)))
  env={'re':re,'json':json,'os':types.SimpleNamespace(getenv=lambda name:None),'urllib':types.SimpleNamespace(request=request)}
  exec(compile(ast.Module(body=[function],type_ignores=[]),'provider-function','exec'),env)
  receipt={'runRef':'https://github.com/SHTFTV/junkremoval.ltd/actions/runs/123','sourceCommit':'a'*40,'event':'schedule'}
  proof=lambda:env['provider_run'](receipt,'.github/workflows/source-monitor.yml','schedule')['passed']
  self.assertTrue(proof())
  for key,value in [('event','push'),('head_sha','b'*40),('status','in_progress'),('conclusion','failure'),('path','.github/workflows/other.yml')]:
   old=body[key];body[key]=value;self.assertFalse(proof());body[key]=old
 def test_preflight_and_receipt_binding_allow_state_only_changes_not_assets(self):
  spec=importlib.util.spec_from_file_location('input_guard',ROOT/'operations/check-inputs.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
  with tempfile.TemporaryDirectory() as directory:
   repo=pathlib.Path(directory)
   def git(*args):return subprocess.check_output(['git',*args],cwd=repo,stderr=subprocess.DEVNULL,text=True).strip()
   git('init','-q');git('config','user.name','Synthetic guard test');git('config','user.email','fixture@example.invalid')
   (repo/'asset.txt').write_text('approved image bytes');(repo/'state.json').write_text('{}');git('add','.');git('commit','-qm','Fixture');head=git('rev-parse','HEAD')
   guard.BASE=repo;guard.paths_for=lambda role:['asset.txt'];self.assertTrue(guard.verify('worker',head))
   (repo/'state.json').write_text('{"new":"receipt"}');self.assertTrue(guard.verify('worker',head))
   tree=ast.parse((ROOT/'operations/supervisor.py').read_text());function=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='receipt_inputs')
   env={'re':re,'subprocess':subprocess,'B':repo/'operations'};exec(compile(ast.Module(body=[function],type_ignores=[]),'receipt-inputs','exec'),env)
   old_cwd=pathlib.Path.cwd()
   try:
    import os;os.chdir(repo)
    self.assertTrue(env['receipt_inputs']({'sourceCommit':head},['asset.txt']))
    (repo/'asset.txt').write_text('different image bytes')
    self.assertFalse(env['receipt_inputs']({'sourceCommit':head},['asset.txt']))
    with self.assertRaises(RuntimeError):guard.verify('worker',head)
   finally:os.chdir(old_cwd)
if __name__=='__main__':unittest.main()
