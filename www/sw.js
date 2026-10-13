const C='lexium-sw';
self.addEventListener('install',e=>{self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim());});
self.addEventListener('fetch',e=>{
  const r0=e.request;
  if(r0.method!=='GET'||r0.headers.has('range'))return;
  const u=new URL(r0.url);
  if(u.origin!==location.origin&&!/fonts\.(googleapis|gstatic)\.com$/.test(u.host))return;
  e.respondWith(fetch(r0).then(r=>{if(r.ok){const c=r.clone();caches.open(C).then(x=>x.put(r0,c)).catch(()=>{});}return r;}).catch(()=>caches.match(r0)));
});
