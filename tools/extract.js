// www/index.html içindeki veriden seslendirilecek metinleri çıkarır -> tools/texts.json
const fs=require('fs');
const h=fs.readFileSync('www/index.html','utf8');
const a=h.search(/var W\s*=\s*\[\]/), b=h.indexOf('(function(){',a);
const code=h.slice(a,b)+';return {W:W,FINAL:FINAL,VERBS:VERBS};';
const D=new Function(code)();
const set=new Map();
const add=(l,t)=>{t=(t||'').trim(); if(t&&/[A-Za-zÇĞİÖŞÜçğıöşü0-9]/.test(t)) set.set(l+'|'+t,[l,t]);};
D.W.forEach(w=>{
  w.d.forEach(day=>day.forEach(s=>{const p=s.split(' | ');add('en',p[0]);add('tr',p[1]);}));
  w.dlg.forEach(l=>add('en',l[1]));
  w.g.ex.forEach(e=>{add('en',e[0]);add('tr',e[1]);});
});
D.VERBS.forEach(v=>add('en',v[0]+', '+v[1].replace(' / ',', ')+', '+v[2].replace(' / ',', ')));
add('en','Hello! This is how the app will sound.');add('tr','Merhaba! Uygulama böyle konuşacak.');
fs.writeFileSync('tools/texts.json',JSON.stringify([...set.values()]));
console.log('metin sayisi',set.size);
