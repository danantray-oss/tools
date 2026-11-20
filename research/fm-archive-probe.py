import urllib.request,json
base='https://ckan.publishing.service.gov.uk/api/3/action/package_show?id='
for id in ['8570ac2d-9bb5-415c-83e8-d860b6e67c4d','d5038a31-8666-4d6f-8d4d-7de87ed650e7']:
  j=json.load(urllib.request.urlopen(base+id,timeout=30))['result']['resources']
  print('BEGIN',id)
  for r in j: print(repr(r.get('name')),repr(r.get('url','').split('/')[-1]))
