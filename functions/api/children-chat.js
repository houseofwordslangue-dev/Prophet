const JSON_HEADERS={"content-type":"application/json; charset=utf-8","cache-control":"no-store"};
const SYSTEM=`أنت «رفيقة القراءة»، مساعد محادثة آمن ومحبب للأطفال داخل منصة سيرة النبي محمد ﷺ.

قواعد إلزامية:
1) خاطب الطفل بلغة عربية واضحة، قصيرة، لطيفة، مناسبة تقريباً للأعمار 7–16، ولا تستخدم التخويف أو الإيحاءات المقلقة.
2) نطاقك الأساسي: السيرة، الأسرة النبوية، الصحابة، التابعون، الأخلاق، القراءة، المفردات، القصص والمواد الظاهرة في الموقع.
3) إذا زُوّدت بسياق من الصفحة فاعتمد عليه أولاً. لا تنسب حديثاً أو قولاً أو حدثاً إلى مصدر إلا إذا كان موجوداً بوضوح في السياق. إذا لم تتأكد فقل إن المادة المتاحة لا تكفي للتحقق.
4) لا تُنشئ أحكاماً دينية شخصية ولا فتاوى. في المسائل الفقهية أو العقدية الدقيقة اطلب الرجوع إلى ولي الأمر/المعلم/متخصص مؤهل.
5) لا تطلب من الطفل اسمه الكامل أو عنوانه أو رقم هاتفه أو مدرسته أو صورته أو أي بيانات شخصية، ولا تشجعه على التواصل مع غرباء أو مغادرة الموقع.
6) لا تقدّم محتوى جنسي، إيذاء ذاتي، تعليمات خطرة أو غير قانونية، كراهية، تنمر، أو وصفاً دموياً للعنف. عند سؤال حساس، أجب بإيجاز وبطريقة وقائية مناسبة للعمر وشجّع الطفل على طلب مساعدة شخص بالغ موثوق عند الحاجة.
7) لا تقل إنك رأيت أو قرأت شيئاً لم يُرسل لك. لا تختلق مراجع أو اقتباسات.
8) لا تحفظ ردود المحادثة كمقالات ولا تقترح نشرها كمحتوى تحريري. هذه محادثة مساعدة فقط.
9) إن كان السؤال خارج النطاق، أجب باختصار ثم وجّه بلطف إلى موضوعات القراءة والتعلّم في الموقع.
10) اجعل الإجابة عادة بين 2 و6 جمل، ويمكن استخدام نقاط قصيرة عند الحاجة.`;
function json(body,status=200){return new Response(JSON.stringify(body),{status,headers:JSON_HEADERS})}
function textFromResponse(data){
  if(typeof data?.output_text==='string')return data.output_text.trim();
  const out=[];for(const item of data?.output||[]){for(const c of item?.content||[]){if(c?.type==='output_text'&&c.text)out.push(c.text)}}
  return out.join('\n').trim();
}
async function openai(path,key,body){
  const r=await fetch(`https://api.openai.com/v1/${path}`,{method:'POST',headers:{'content-type':'application/json','authorization':`Bearer ${key}`},body:JSON.stringify(body)});
  const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data?.error?.message||`OpenAI ${r.status}`);return data;
}
function cleanString(v,max){return String(v||'').replace(/\u0000/g,'').trim().slice(0,max)}
export async function onRequestPost({request,env}){
  if(!env?.OPENAI_API_KEY)return json({error:'CHAT_NOT_CONFIGURED'},503);
  let body;try{body=await request.json()}catch{return json({error:'INVALID_JSON'},400)}
  const message=cleanString(body?.message,1800);if(!message)return json({error:'EMPTY_MESSAGE'},400);
  const language=cleanString(body?.language||'ar',12);
  const page=cleanString(body?.page,240);
  const title=cleanString(body?.context?.title,240);
  const excerpt=cleanString(body?.context?.excerpt,5000);
  const history=Array.isArray(body?.history)?body.history.slice(-8).map(x=>({role:x?.role==='assistant'?'assistant':'user',text:cleanString(x?.text,1200)})).filter(x=>x.text):[];
  try{
    const mod=await openai('moderations',env.OPENAI_API_KEY,{model:'omni-moderation-latest',input:message});
    if(mod?.results?.[0]?.flagged)return json({answer:'هذا السؤال يحتاج إلى طريقة أكثر أماناً للحديث عنه. إذا كان الأمر يزعجك أو يتعلق بأذى لك أو لشخص آخر، تحدث الآن مع أحد والديك أو شخص بالغ تثق به. ويمكنك أن تسألني سؤالاً آخر عن القصة أو القراءة.'});
    const transcript=history.map(x=>`${x.role==='assistant'?'المساعد':'الطفل'}: ${x.text}`).join('\n');
    const context=[title&&`عنوان الصفحة: ${title}`,page&&`المسار: ${page}`,excerpt&&`مقتطف موثوق من الصفحة:\n${excerpt}`,transcript&&`آخر المحادثة:\n${transcript}`].filter(Boolean).join('\n\n');
    const response=await openai('responses',env.OPENAI_API_KEY,{model:env.OPENAI_CHAT_MODEL||'gpt-5.6-luna',store:false,instructions:SYSTEM,input:`${context?context+'\n\n':''}سؤال الطفل: ${message}`,max_output_tokens:500});
    let answer=textFromResponse(response);if(!answer)throw new Error('EMPTY_OPENAI_RESPONSE');
    const outMod=await openai('moderations',env.OPENAI_API_KEY,{model:'omni-moderation-latest',input:answer});
    if(outMod?.results?.[0]?.flagged)answer='أستطيع مساعدتك بطريقة أبسط وأكثر أماناً. اسألني عن معنى في القصة، أو شخصية، أو درس نتعلمه من المادة التي تقرؤها.';
    return json({answer,model:env.OPENAI_CHAT_MODEL||'gpt-5.6-luna'});
  }catch(err){console.error('children-chat',err?.message||err);return json({error:'CHAT_UPSTREAM_ERROR'},502)}
}
export async function onRequest({request,env}){if(request.method==='POST')return onRequestPost({request,env});return json({error:'METHOD_NOT_ALLOWED'},405)}
