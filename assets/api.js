window.SiteAPI=(()=>{
  let csrf=null,user=null;
  async function request(path,options={}){
    const opts={credentials:'same-origin',...options};
    opts.headers={'Accept':'application/json',...(opts.body?{'Content-Type':'application/json'}:{}),...(opts.headers||{})};
    if(opts.method && !['GET','HEAD'].includes(opts.method.toUpperCase())){
      if(!csrf) await me().catch(()=>null);
      if(csrf) opts.headers['X-CSRF-Token']=csrf;
    }
    const res=await fetch(path,opts); let data={}; try{data=await res.json()}catch(e){}
    if(!res.ok){const err=new Error(data.error||`HTTP ${res.status}`);err.status=res.status;err.data=data;throw err}
    if(data.csrf)csrf=data.csrf;if(Object.prototype.hasOwnProperty.call(data,'user'))user=data.user;return data;
  }
  async function me(){const d=await request('/api/auth/me');return d.user}
  return {request,me,get user(){return user},get csrf(){return csrf}};
})();
