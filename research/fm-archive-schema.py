import urllib.request,json,zipfile,io,csv,xml.etree.ElementTree as ET,collections
u='https://ckan.publishing.service.gov.uk/api/3/action/package_show?id='
for source,id in [('FTS','8570ac2d-9bb5-415c-83e8-d860b6e67c4d'),('CF','d5038a31-8666-4d6f-8d4d-7de87ed650e7')]:
  meta=json.load(urllib.request.urlopen(u+id,timeout=20))['result']['resources']
  r=next(x for x in meta if ('11th November' in x.get('name','') if source=='FTS' else '2026-11-11' in x.get('name','')))
  b=urllib.request.urlopen(r['url'],timeout=55).read()
  if source=='FTS':
    z=zipfile.ZipFile(io.BytesIO(b));counts=collections.Counter()
    for f in z.namelist():
      if not f.endswith('.xml'):continue
      root=ET.fromstring(z.read(f));counts[root.tag]+=1
      if root.tag!='TED_EXPORT' and len([a for a in counts if a!='TED_EXPORT'])<=4 and counts[root.tag]<=2:
        print('MODERN',f,'ROOT',root.tag,'FIRST_7000',z.read(f)[:7000].decode('utf-8','replace'))
    print('ROOT_COUNTS',counts)
  else:
    cr=csv.DictReader(io.StringIO(b.decode('utf-8-sig','replace')))
    names=[x for x in cr.fieldnames if any(k in x for k in ('releases/0/awards','releases/0/contracts','releases/0/tender/value','releases/0/parties','releases/0/tag'))]
    print('FIELDS',len(cr.fieldnames),'FILTER',names[:100])
    row=next(cr)
    print('EXAMPLE_AWARD',{k:row.get(k) for k in names[:100] if row.get(k)})
