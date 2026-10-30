import {useEffect,useState} from 'react'
import {Activity,ArrowUpRight,Bot,Braces,Bug,Check,CheckCircle2,ChevronDown,Code2,Copy,Cpu,FileCode2,Folder,GitBranch,LoaderCircle,Play,Plus,ShieldCheck,Sparkles,Terminal,TestTube2,WandSparkles,X,Zap} from 'lucide-react'
import {runAgent,getHealth} from './api'

const starter = `def calculate_discount(price, discount):
    """Return the final price after applying a percentage discount."""
    if price < 0:
        raise ValueError("price cannot be negative")
    if discount < 0 or discount > 100:
        raise ValueError("discount must be between 0 and 100")
    return price * (1 - discount / 100)


def format_price(value):
    return f"₹{value:.2f}"


if __name__ == "__main__":
    print(format_price(calculate_discount(1000, 15)))
`
const workflows = [
  {id:'debug',name:'Fix bugs',icon:Bug,desc:'Find root causes and repair defects'},
  {id:'review',name:'Code review',icon:ShieldCheck,desc:'Quality, security and maintainability'},
  {id:'tests',name:'Generate tests',icon:TestTube2,desc:'Create and run unit tests'},
  {id:'explain',name:'Explain code',icon:Braces,desc:'Understand unfamiliar code'},
  {id:'build',name:'Build feature',icon:WandSparkles,desc:'Implement a feature in the workspace'}
]

export default function App(){
  const [code,setCode]=useState(starter),[taskType,setTaskType]=useState('debug')
  const [task,setTask]=useState('Inspect this Python file, identify edge cases, improve it if needed, create pytest tests, and run the tests. Iterate on failures.')
  const [busy,setBusy]=useState(false),[result,setResult]=useState(null),[error,setError]=useState('')
  const [health,setHealth]=useState(null),[tab,setTab]=useState('output'),[selected,setSelected]=useState('main.py')
  const [copied,setCopied]=useState(false)
  useEffect(()=>{getHealth().then(setHealth).catch(()=>setHealth({status:'offline'}))},[])
  const chosen=workflows.find(w=>w.id===taskType)
  async function execute(){
    setBusy(true);setError('');setResult(null);setTab('activity')
    try{const data=await runAgent({task_type:taskType,task,files:[{path:'main.py',content:code}]});setResult(data);setSelected(data.files?.[0]?.path||'main.py');setTab('output')}
    catch(e){setError(e.message);setTab('activity')}finally{setBusy(false)}
  }
  async function copy(value){try{await navigator.clipboard.writeText(value);setCopied(true);setTimeout(()=>setCopied(false),1300)}catch{setError('Clipboard access denied.')}}
  function download(file){const u=URL.createObjectURL(new Blob([file.content],{type:'text/plain'}));const a=document.createElement('a');a.href=u;a.download=file.path.split('/').pop();a.click();URL.revokeObjectURL(u)}
  const selectedFile=result?.files?.find(f=>f.path===selected)
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon"><Bot size={21}/></div><div><b>codepilot<span>.ai</span></b><small>AGENTIC ENGINEERING</small></div></div>
      <div className="side-label">WORKSPACE <button className="icon" title="New workspace"><Plus size={15}/></button></div>
      <div className="workspace"><Folder size={15}/> <span>my-project</span><ChevronDown size={14}/></div>
      <div className="side-label section-label">ENGINEERING TOOLS</div>
      {workflows.map(w=>{const I=w.icon;return <button key={w.id} className={'nav '+(taskType===w.id?'nav-active':'')} onClick={()=>setTaskType(w.id)}><I size={16}/>{w.name}</button>})}
      <div className="side-label section-label">PROJECT</div>
      <div className="tree"><div><Folder size={14}/> src</div><div className="tree-file"><FileCode2 size={14}/> main.py</div>{result?.files?.filter(f=>f.path!=='main.py').map(f=><button key={f.path} onClick={()=>{setSelected(f.path);setTab('files')}}><FileCode2 size={14}/>{f.path}</button>)}</div>
      <div className="side-bottom"><div className="promo"><div className="promo-icon"><Zap size={15}/></div><b>Powered by Nemotron</b><p>Open models. Agentic workflows.</p><a href="https://tokenfactory.nebius.com/" target="_blank" rel="noreferrer">Explore Token Factory ↗</a></div><div className="user"><div className="avatar">CP</div><div><b>Developer</b><small>Local workspace</small></div></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb">Workspace <span>/</span> <b>my-project</b><label><GitBranch size={12}/> main</label></div><div className="top-right"><span className={'status '+(health?.status==='ok'?'connected':'')}><i/>{health?.status==='ok'?'API connected':'API offline'}</span><div className="avatar">CP</div></div></header>
      <section className="hero"><div><div className="eyebrow"><i/> AUTONOMOUS SOFTWARE ENGINEER</div><h1>Build better software.<br/><em>Ship with confidence.</em></h1><p>Delegate the repetitive work. Stay in control of every change.</p></div><div className="orb"><div className="orbit orbit-a"/><div className="orbit orbit-b"/><div className="orb-core"><Bot size={33}/></div><i className="orb-dot d1"/><i className="orb-dot d2"/><i className="orb-dot d3"/></div></section>
      <section className="stats">
        <div className="stat"><div className="stat-icon purple"><Cpu size={17}/></div><div><small>AI ENGINE</small><b>NVIDIA Nemotron</b><span>Nebius Token Factory</span></div><CheckCircle2 className="ok" size={15}/></div>
        <div className="stat"><div className="stat-icon blue"><GitBranch size={17}/></div><div><small>WORKFLOW</small><b>Agentic loop</b><span>Plan · Act · Verify</span></div><label className="live">LIVE</label></div>
        <div className="stat"><div className="stat-icon green"><ShieldCheck size={17}/></div><div><small>DEVELOPER CONTROL</small><b>Review every change</b><span>Human-in-the-loop</span></div><CheckCircle2 className="ok" size={15}/></div>
      </section>
      <div className="section-title"><div><h2>Engineering workspace</h2><p>Give your agent a task and let it work through the code.</p></div><div className="model-pill"><i/>{health?.model_configured?'Nebius key detected':'Configure API key'}</div></div>
      <section className="work-grid">
        <div className="panel editor">
          <div className="panel-head"><div><Code2 size={15}/> Code workspace <label><FileCode2 size={12}/> main.py</label></div><div><button className="mini" onClick={()=>copy(code)}><Copy size={12}/>{copied?'Copied':'Copy'}</button><button className="mini" onClick={()=>setCode('')}><X size={12}/> Clear</button></div></div>
          <div className="editor-bar"><div className="traffic"><i/><i/><i/></div> PYTHON 3.11 <span>UTF-8 · LF</span></div>
          <div className="code-wrap"><div className="lines">{code.split('\n').map((_,i)=><span key={i}>{i+1}</span>)}</div><textarea aria-label="Python code editor" spellCheck="false" value={code} onChange={e=>setCode(e.target.value)}/></div>
          <div className="editor-foot"><span><i/> {code.length} characters</span><span>Sent to temporary agent workspace</span></div>
        </div>
        <div className="panel command">
          <div className="panel-head"><div><Sparkles size={15}/> Agent command</div><label className="ready"><i/> READY</label></div>
          <div className="command-body"><label>SELECT WORKFLOW</label><div className="workflow-grid">{workflows.map(w=>{const I=w.icon;return <button key={w.id} className={taskType===w.id?'chosen':''} onClick={()=>setTaskType(w.id)}><I size={15}/>{w.name}{taskType===w.id&&<Check size={12}/>}</button>})}</div>
            <label htmlFor="task">WHAT SHOULD THE AGENT DO?</label><textarea id="task" className="task" value={task} onChange={e=>setTask(e.target.value)} placeholder="Describe the engineering task..."/>
            <div className="hint"><Sparkles size={12}/>{chosen?.desc}</div>
            <button className="run" disabled={busy||!code.trim()||!task.trim()} onClick={execute}>{busy?<><LoaderCircle className="spin" size={16}/> Agent working...</>:<><Play size={15} fill="currentColor"/> Run agent <ArrowUpRight size={15}/></>}</button>
            <div className="safe-note"><ShieldCheck size={12}/> Changes happen in a temporary workspace. Review before use.</div>
          </div>
        </div>
      </section>
      <section className="panel results">
        <div className="result-tabs"><div><button className={tab==='output'?'tab-on':''} onClick={()=>setTab('output')}><Terminal size={14}/> Output</button><button className={tab==='activity'?'tab-on':''} onClick={()=>setTab('activity')}><Activity size={14}/> Agent activity {result?.events?.length>0&&<i>{result.events.length}</i>}</button><button className={tab==='files'?'tab-on':''} onClick={()=>setTab('files')}><FileCode2 size={14}/> Files {result?.files?.length>0&&<i>{result.files.length}</i>}</button></div>{result?.model&&<small>{result.model}</small>}</div>
        <div className="result-body">
          {error&&<div className="error"><X size={15}/><div><b>Agent request failed</b><p>{error}</p><small>Check backend status, API key, model access and network.</small></div></div>}
          {tab==='output'&&(result?<div className="output"><div className="success"><CheckCircle2 size={15}/> Workflow completed <span>{result.changed_files?.length||0} files changed</span></div><pre>{result.summary}</pre>{result.tool_results?.length>0&&<div className="tool-results"><b>Tool calls</b>{result.tool_results.map((t,i)=><div key={i}><code>{t.tool}</code><span>{t.result.slice(0,220)}</span></div>)}</div>}</div>:<div className="empty"><div><Terminal size={22}/></div><b>Your agent output will appear here</b><p>Choose a workflow, describe the task, then run your agent.</p><section><span><i>01</i> Plan</span><span><i>02</i> Execute tools</span><span><i>03</i> Verify</span></section></div>)}
          {tab==='activity'&&<div className="activity">{result?.events?.length?result.events.map((e,i)=><div className="event" key={i}><div className={'event-icon '+e.kind}><Activity size={13}/></div><div><b>{e.message}</b><p>{e.detail}</p></div><time>{String(i+1).padStart(2,'0')}</time></div>):<div className="empty-inline"><Activity size={19}/> Agent execution steps will appear here.</div>}</div>}
          {tab==='files'&&<div className="files">{result?.files?.length?result.files.map(f=><div className="file-row" key={f.path}><button onClick={()=>setSelected(f.path)} className={selected===f.path?'selected':''}><FileCode2 size={14}/>{f.path}</button><button className="mini" onClick={()=>download(f)}>Download</button></div>):<div className="empty-inline">Run the agent to see workspace files and generated tests.</div>}{selectedFile&&<div className="preview"><div><b>{selectedFile.path}</b><button className="mini" onClick={()=>copy(selectedFile.content)}><Copy size={12}/> Copy</button></div><pre>{selectedFile.content}</pre></div>}</div>}
        </div>
        <div className="result-foot"><span><i/> Local workspace session</span><span>Always review AI-generated code before merging</span></div>
      </section>
      <footer>CODEPILOT AI · BUILT FOR NEBIUS × NVIDIA GLOBAL AI HACKATHON <span>Powered by <b>NVIDIA Nemotron</b> on <b>Nebius Token Factory</b></span></footer>
    </main>
  </div>
}
