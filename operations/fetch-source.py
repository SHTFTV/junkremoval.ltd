"""One fixed official source read. Parent enforces a hard subprocess deadline."""
import sys,urllib.request,urllib.parse,hashlib,gzip,json,io,pathlib,re
from html.parser import HTMLParser
MAX_RAW=3_000_000
MAX_EXTRACTED=12_000_000
SOURCE_FILE=pathlib.Path(__file__).with_name('sources.json')
class VisibleText(HTMLParser):
 def __init__(self):super().__init__();self.skip=0;self.main=0;self.all=[];self.primary=[];self.stack=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);blocked=tag in ['script','style','head','nav','header','footer','template'];primary=tag in ['main','article'] or a.get('role')=='main';self.stack.append((tag,blocked,primary));self.skip+=blocked;self.main+=primary
  if tag in ['img','input','meta','link','br','hr','source','area','wbr','embed','param','track','col']:self.stack.pop();self.skip-=blocked;self.main-=primary
 def handle_endtag(self,tag):
  match=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i][0]==tag),None)
  if match is not None:
   for _,blocked,primary in self.stack[match:]:self.skip-=blocked;self.main-=primary
   del self.stack[match:]
 def handle_data(self,data):
  if not self.skip:
   value=' '.join(data.split())
   if value:self.all.append(value);self.primary.extend([value] if self.main else [])
def visible_text(html):
 parser=VisibleText();parser.feed(html);return ' '.join(parser.primary or parser.all)
def scoped_url(url,origin=None):
 if re.search(r'[\x00-\x20\x7f\\]',url):raise ValueError('Source URL contains controls or backslash')
 u=urllib.parse.urlsplit(url)
 if u.scheme!='https' or not u.hostname or u.username or u.password or u.port not in [None,443] or u.fragment:raise ValueError('Source URL scope invalid')
 if origin and (u.scheme,u.hostname,u.port)!=(origin.scheme,origin.hostname,origin.port):raise ValueError('Source redirect left fixed origin')
 return u
class ScopedRedirect(urllib.request.HTTPRedirectHandler):
 max_redirections=5
 def __init__(self,origin):super().__init__();self.origin=origin
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  scoped_url(newurl,self.origin)
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url):
 allowed={x['url'] for x in json.loads(SOURCE_FILE.read_text())}
 if url not in allowed:raise ValueError('Source URL is not in the fixed approved list')
 origin=scoped_url(url)
 req=urllib.request.Request(url,headers={'User-Agent':'JunkRemoval.ltd source-review monitor/1.0','Accept-Encoding':'gzip','Accept':'text/html,text/plain,application/xhtml+xml'})
 with urllib.request.build_opener(ScopedRedirect(origin)).open(req,timeout=45) as response:
  scoped_url(response.url,origin)
  if response.status!=200:raise ValueError('Source did not return HTTP200')
  content_type=response.headers.get_content_type()
  if content_type not in ['text/html','text/plain','application/xhtml+xml']:raise ValueError('Source is not HTML or text')
  body=response.read(MAX_RAW+1)
  if len(body)>MAX_RAW:raise ValueError('Source exceeds raw transport limit')
  if response.headers.get('Content-Encoding','').lower()=='gzip':
   with gzip.GzipFile(fileobj=io.BytesIO(body)) as stream:body=stream.read(MAX_EXTRACTED+1)
  if len(body)>MAX_EXTRACTED:raise ValueError('Source exceeds extraction limit')
  text=visible_text(body.decode(response.headers.get_content_charset() or 'utf8',errors='replace'))
  if len(text)<80:raise ValueError('Insufficient visible source text; retain for review')
  return {'httpStatus':response.status,'sha256':hashlib.sha256(text.encode()).hexdigest(),'hashAlgorithm':'visible-text-v1','textCharacters':len(text)}
if __name__=='__main__':print(json.dumps(fetch(sys.argv[1])))
