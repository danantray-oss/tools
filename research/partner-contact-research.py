import urllib.request,urllib.parse,re,html
urls=[
"https://mesmerise.marketing/contact",
"https://mesmerise.marketing/partners",
"https://www.getfindable.co/partners",
"https://insightos.co.uk/partnerships/",
"https://itsupport101.com/contact.php",
"https://itsupport101.com/partners/",
"https://adoptech.co.uk/msp-partner-programme/",
"https://www.ivoxx.co.uk/partners.html",
"https://itboffins.com/partners"
]
for u in urls:
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
  with urllib.request.urlopen(req,timeout=22) as f:s=f.read(300000).decode('utf-8','replace')
  emails=sorted(set(html.unescape(x) for x in re.findall(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}',s)))
  mailto=sorted(set(html.unescape(x) for x in re.findall(r'mailto:([^"\'<>?\s]+)',s)))
  print('SITE',u,'HTTP','OK','EMAILS',emails[:20],'MAILTO',mailto[:20])
 except Exception as e:print('SITE',u,'ERROR',repr(e))
