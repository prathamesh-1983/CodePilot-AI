async function post(url,payload){
 const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
 const data=await r.json()
 if(!r.ok) throw new Error(data.detail||'Request failed')
 return data
}
export async function runAgent(payload){return post('/api/agent/run',payload)}
export async function analyzeCode(payload){return (await post('/api/analyze',payload)).result}
export async function getHealth(){const r=await fetch('/api/health');if(!r.ok)throw new Error('Backend unavailable');return r.json()}
