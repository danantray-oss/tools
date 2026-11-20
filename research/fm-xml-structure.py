import urllib.request,urllib.parse,json,zipfile,io,xml.etree.ElementTree as ET
u='https://ckan.publishing.service.gov.uk/api/3/action/package_show?id=8570ac2d-9bb5-415c-83e8-d860b6e67c4d'
res=json.load(urllib.request.urlopen(u))['result']['resources']
for fileday,id in [('9th','106241-2026'),('16th','108593-2026')]:
  ur=next(r['url'] for r in res if r['name'].endswith(fileday+' November 2026'))
  z=zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(ur).read()))
  root=ET.fromstring(z.read(id+'.xml'))
  def loc(x):return x.tag.split('}')[-1]
  print('NOTICE',id,'TOPLEVEL',[(loc(x),x.attrib) for x in root])
  print('FIRST_MAIN_TREE')
  def walk(node,path="",depth=0):
    tag=loc(node); this=path+'/'+tag
    kids=list(node)
    if depth<5:
      v=(node.text or '').strip()
      if depth<=3 or not kids:
        print(' '*depth*2, this, str(node.attrib)[:100], repr(v[:100]))
    if depth<5:
      for x in kids[:30]: walk(x,this,depth+1)
  walk(root)
  print('INTERESTING_TAGS')
  n=0
  for e in root.iter():
    tag=loc(e)
    if tag.lower() in ('title','name','supplier','suppliers','buyer','award','awards','status','amount','value','contract','contracts'):
      v=(e.text or '').strip()
      print(tag,repr(v[:180]),'attributes',str(e.attrib)[:80], 'childcount',len(e))
      n+=1
      if n>75:break
