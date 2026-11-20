import urllib.request, urllib.error, json, urllib.parse
ids=['8570ac2d-9bb5-415c-83e8-d860b6e67c4d','d5038a31-8666-4d6f-8d4d-7de87ed650e7']
for host in ['https://ckan.publishing.service.gov.uk/api/3/action/package_show','https://data.gov.uk/api/3/action/package_show','https://www.data.gov.uk/api/3/action/package_show']:
  for ident in ids:
    u=host+'?'+urllib.parse.urlencode({'id':ident})
    try:
      req=urllib.request.Request(u,headers={'User-Agent':'Public data research 1.0','Accept':'application/json'})
      with urllib.request.urlopen(req,timeout=28) as f:
        j=json.loads(f.read())
      res=j.get('result',{}).get('resources',[])
      print('OK',host,ident,len(res))
      for x in res[:4]: print('RESOURCE',x.get('name'),x.get('url'),x.get('format'))
    except urllib.error.HTTPError as e:print('HTTP',e.code,u,e.read(100).decode('utf8','replace'))
    except Exception as e: print('ERROR',u,repr(e))
