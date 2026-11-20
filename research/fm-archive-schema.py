import urllib.request,urllib.parse,json,zipfile,io,csv,xml.etree.ElementTree as ET
url='https://ckan.publishing.service.gov.uk/api/3/action/package_show?id='
for source,ident in [('FTS','8570ac2d-9bb5-415c-83e8-d860b6e67c4d'),('CF','d5038a31-8666-4d6f-8d4d-7de87ed650e7')]:
  data=json.load(urllib.request.urlopen(url+ident,timeout=30))['result']['resources']
  print(source,'RESOURCES',len(data))
  dates=[r for r in data if ('11th November' in r.get('name','') if source=='FTS' else '2026-11-11' in r.get('name',''))]
  if not dates: print('NO_DATE_MATCH');continue
  rr=dates[0]; print('DOWNLOADING',rr['url'])
  with urllib.request.urlopen(rr['url'],timeout=60) as resp:b=resp.read()
  print('BYTES',len(b))
  if source=='FTS':
    z=zipfile.ZipFile(io.BytesIO(b))
    files=z.namelist()
    print('ZIP_FILES',len(files),'FIRST',files[:8])
    for f in files:
      if f.endswith('.xml'):
        raw=z.read(f)
        root=ET.fromstring(raw)
        print('EXAMPLE_FILE',f,'XML_BYTES',len(raw),'ROOT',root.tag,'ATTRS',root.attrib)
        print('CHILD_TAGS',[(el.tag,el.attrib) for el in list(root)[:14]])
        print('FIRST_1500',raw[:1500].decode('utf8','replace'))
        break
  else:
    txt=b.decode('utf-8-sig','replace')
    print('CSV_HEADERS',txt.splitlines()[0][:3000])
    print('CSV_FIRSTROW',txt.splitlines()[1][:2000] if len(txt.splitlines())>1 else '')
