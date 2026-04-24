import { useState, useEffect } from "react";

const C = {
  confirmed: { label:"CONFIRMED", color:"#4ade80", bg:"rgba(74,222,128,0.12)", border:"rgba(74,222,128,0.25)", icon:"✓" },
  no_answer: { label:"NO ANSWER", color:"#fb923c", bg:"rgba(251,146,60,0.12)",  border:"rgba(251,146,60,0.25)",  icon:"~" },
  failed:    { label:"FAILED",    color:"#f87171", bg:"rgba(248,113,113,0.12)", border:"rgba(248,113,113,0.25)", icon:"✕" },
};
const LANG = {"en-IN":"EN","hi-IN":"HI","kn-IN":"KN","mr-IN":"MR"};
const fmt = d => d ? new Date(d).toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit",second:"2-digit"}) : "";
const lang = l => LANG[l]||"EN";

const s = {
  page:   { minHeight:"100vh", background:"#0c0c10", color:"#e2e2e8", fontFamily:"'SF Pro Display',-apple-system,system-ui,sans-serif", padding:"0 0 60px" },
  wrap:   { maxWidth:900, margin:"0 auto", padding:"0 20px" },
  header: { borderBottom:"1px solid rgba(255,255,255,0.07)", padding:"24px 0 20px", marginBottom:32 },
  hrow:   { display:"flex", alignItems:"center", justifyContent:"space-between", flexWrap:"wrap", gap:12 },
  logo:   { display:"flex", alignItems:"center", gap:12 },
  badge:  { width:38, height:38, borderRadius:10, background:"#dc2626", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, boxShadow:"0 0 20px rgba(220,38,38,0.4)" },
  title:  { margin:0, fontSize:18, fontWeight:700, letterSpacing:"-0.02em", color:"#fff" },
  sub:    { margin:0, fontSize:10, color:"rgba(255,255,255,0.3)", letterSpacing:"0.2em", textTransform:"uppercase", marginTop:1 },
  live:   { display:"flex", alignItems:"center", gap:6, padding:"5px 12px", borderRadius:20, background:"rgba(220,38,38,0.1)", border:"1px solid rgba(220,38,38,0.3)" },
  liveT:  { fontSize:10, fontWeight:700, color:"#f87171", letterSpacing:"0.15em", textTransform:"uppercase" },
  stats:  { display:"flex", alignItems:"center", gap:8, marginTop:20, flexWrap:"wrap" },
  pill:   { display:"flex", alignItems:"center", gap:8, padding:"8px 14px", borderRadius:8, background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)" },
  pillV:  { fontSize:18, fontWeight:800 },
  pillL:  { fontSize:10, color:"rgba(255,255,255,0.35)", letterSpacing:"0.1em", textTransform:"uppercase" },
  div:    { width:1, height:28, background:"rgba(255,255,255,0.08)", margin:"0 4px" },
  sec:    { marginBottom:40 },
  secH:   { display:"flex", alignItems:"center", gap:10, marginBottom:14, paddingBottom:10, borderBottom:"1px solid rgba(255,255,255,0.07)" },
  secT:   { margin:0, fontSize:11, fontWeight:700, letterSpacing:"0.2em", textTransform:"uppercase" },
  cnt:    { marginLeft:"auto", fontSize:11, fontWeight:700, padding:"2px 8px", borderRadius:10, background:"rgba(255,255,255,0.06)" },
  empty:  { textAlign:"center", color:"rgba(255,255,255,0.2)", fontStyle:"italic", padding:"20px 0", fontSize:13 },
  card:   { display:"flex", alignItems:"flex-start", gap:14, padding:"14px 16px", borderRadius:12, background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.06)", marginBottom:8, transition:"background 0.15s, border 0.15s", cursor:"default" },
  dot:    (c)=>({ flexShrink:0, width:28, height:28, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:11, fontWeight:700, background:c.bg, border:`1px solid ${c.border}`, color:c.color }),
  body:   { flex:1, minWidth:0 },
  meta:   { display:"flex", alignItems:"center", gap:6, flexWrap:"wrap", marginBottom:4 },
  lTag:   { fontSize:10, fontWeight:700, color:"rgba(255,255,255,0.25)", letterSpacing:"0.15em" },
  phone:  { fontSize:12, color:"rgba(255,255,255,0.55)", fontFamily:"monospace" },
  addr:   { fontSize:10, color:"#38bdf8", background:"rgba(56,189,248,0.1)", border:"1px solid rgba(56,189,248,0.2)", padding:"1px 7px", borderRadius:10 },
  items:  { fontSize:13, color:"rgba(255,255,255,0.82)", margin:0 },
  trans:  { fontSize:11, color:"rgba(255,255,255,0.2)", fontStyle:"italic", margin:"3px 0 0", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" },
  right:  { flexShrink:0, textAlign:"right", display:"flex", flexDirection:"column", alignItems:"flex-end", gap:5 },
  stBadge:(c)=>({ fontSize:10, fontWeight:700, padding:"3px 9px", borderRadius:10, background:c.bg, border:`1px solid ${c.border}`, color:c.color }),
  time:   { fontSize:10, color:"rgba(255,255,255,0.25)", fontFamily:"monospace" },
  oid:    { fontSize:9, color:"rgba(255,255,255,0.15)", fontFamily:"monospace" },
  callRow:{ display:"flex", gap:10, marginBottom:32 },
  inp:    { flex:1, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", fontSize:13, color:"#fff", outline:"none" },
  btn:    (dis)=>({ padding:"10px 18px", borderRadius:10, fontSize:13, fontWeight:700, background:dis?"rgba(220,38,38,0.35)":"#dc2626", color:"#fff", border:"none", cursor:dis?"not-allowed":"pointer", boxShadow:dis?"none":"0 0 16px rgba(220,38,38,0.3)", transition:"all 0.15s" }),
  toast:  { position:"fixed", top:16, right:16, zIndex:99, padding:"10px 18px", borderRadius:12, fontSize:13, fontWeight:600, background:"rgba(5,46,22,0.97)", border:"1px solid rgba(74,222,128,0.35)", color:"#86efac" },
};

function Ping() {
  return (
    <span style={{ position:"relative", display:"inline-flex", width:8, height:8 }}>
      <span style={{ position:"absolute", inset:0, borderRadius:"50%", background:"#f87171", animation:"ping 1.2s ease-in-out infinite", opacity:0.7 }} />
      <span style={{ position:"relative", width:8, height:8, borderRadius:"50%", background:"#f87171", display:"block" }} />
    </span>
  );
}

function Pill({ label, value, color }) {
  return (
    <div style={s.pill}>
      <span style={{ ...s.pillV, color }}>{value}</span>
      <span style={s.pillL}>{label}</span>
    </div>
  );
}

function Card({ o }) {
  const c = C[o.status] || C.confirmed;
  const [hover, setHover] = useState(false);
  return (
    <div style={{ ...s.card, background: hover?"rgba(255,255,255,0.055)":"rgba(255,255,255,0.03)", border:`1px solid ${hover?"rgba(255,255,255,0.11)":"rgba(255,255,255,0.06)"}` }}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}>
      <div style={s.dot(c)}>{c.icon}</div>
      <div style={s.body}>
        <div style={s.meta}>
          <span style={s.lTag}>{lang(o.language)}</span>
          <span style={s.phone}>{(o.customer_phone||"unknown").trim()}</span>
          {o.address?.trim() && <span style={s.addr}>📍 {o.address}</span>}
        </div>
        <p style={{ ...s.items, color: o.items?.length?"rgba(255,255,255,0.82)":"rgba(255,255,255,0.22)", fontStyle:o.items?.length?"normal":"italic" }}>
          {o.items?.length ? o.items.join(", ") : "No items captured"}
        </p>
        {o.raw_transcript && <p style={s.trans}>"{o.raw_transcript}"</p>}
      </div>
      <div style={s.right}>
        <span style={s.stBadge(c)}>{c.label}</span>
        <span style={s.time}>{fmt(o.confirmed_at)}</span>
        <span style={s.oid}>#{(o.id||"").slice(0,8)}</span>
      </div>
    </div>
  );
}

function Section({ title, icon, orders, color, empty }) {
  return (
    <div style={s.sec}>
      <div style={s.secH}>
        <span style={{ fontSize:14 }}>{icon}</span>
        <h2 style={{ ...s.secT, color }}>{title}</h2>
        <span style={{ ...s.cnt, color }}>{orders.length}</span>
      </div>
      {orders.length===0
        ? <p style={s.empty}>{empty}</p>
        : orders.map(o=><Card key={o.id} o={o}/>)}
    </div>
  );
}

export default function App() {
  const [orders, setOrders] = useState([]);
  const [toast, setToast] = useState(null);
  const [phone, setPhone] = useState("");
  const [calling, setCalling] = useState(false);

  useEffect(()=>{
    const go = async()=>{ try{ const r=await fetch("http://localhost:8000/orders"); setOrders(await r.json()); }catch(e){} };
    go();
    const iv=setInterval(go,3000);
    return()=>clearInterval(iv);
  },[]);

  const confirmed = orders.filter(o=>o.status==="confirmed");
  const noAnswer  = orders.filter(o=>o.status==="no_answer");
  const failed    = orders.filter(o=>o.status==="failed");
  const lc = orders.reduce((a,o)=>{ const l=LANG[o.language]||"EN"; a[l]=(a[l]||0)+1; return a; },{});

  const call = async()=>{
    if(!phone||calling) return;
    setCalling(true);
    try{ await fetch(`http://localhost:8000/make-call?to=${encodeURIComponent(phone)}`,{method:"POST"}); setToast("Call initiated"); }
    catch(e){ setToast("Backend unreachable"); }
    setTimeout(()=>{ setCalling(false); setToast(null); },3000);
  };

  return (
    <div style={s.page}>
      <style>{`@keyframes ping{0%,100%{transform:scale(1);opacity:0.7}50%{transform:scale(2.2);opacity:0}} *{box-sizing:border-box;margin:0;padding:0}`}</style>
      {toast && <div style={s.toast}>✓ {toast}</div>}
      <div style={s.wrap}>
        <div style={s.header}>
          <div style={s.hrow}>
            <div style={s.logo}>
              <div style={s.badge}>🤖</div>
              <div>
                <h1 style={s.title}>AUTOMATON AI</h1>
                <p style={s.sub}>Order Intelligence Dashboard</p>
              </div>
            </div>
            <div style={s.live}><Ping/><span style={s.liveT}>Live</span></div>
          </div>
          <div style={s.stats}>
            <Pill label="Total"     value={orders.length}    color="#fff"/>
            <Pill label="Confirmed" value={confirmed.length} color="#4ade80"/>
            <Pill label="No Answer" value={noAnswer.length}  color="#fb923c"/>
            <Pill label="Failed"    value={failed.length}    color="#f87171"/>
            <div style={s.div}/>
            {["EN","HI","KN","MR"].map(l=><Pill key={l} label={l} value={lc[l]||0} color="#67e8f9"/>)}
          </div>
        </div>

        <div style={s.callRow}>
          <input style={s.inp} type="text" placeholder="+91xxxxxxxxxx" value={phone} onChange={e=>setPhone(e.target.value)}
            onFocus={e=>e.target.style.borderColor="rgba(220,38,38,0.5)"} onBlur={e=>e.target.style.borderColor="rgba(255,255,255,0.1)"}/>
          <button style={s.btn(!phone||calling)} onClick={call} disabled={!phone||calling}>
            {calling?"Calling…":"📞 Initiate Call"}
          </button>
        </div>

        <Section title="Confirmed Orders" icon="✅" orders={confirmed} color="#4ade80" empty="No confirmed orders yet"/>
        <Section title="No Answer"        icon="⏳" orders={noAnswer}  color="#fb923c" empty="All calls answered"/>
        <Section title="Failed"           icon="❌" orders={failed}    color="#f87171" empty="No failed orders"/>

        <p style={{ textAlign:"center", fontSize:11, color:"rgba(255,255,255,0.12)", letterSpacing:"0.2em", textTransform:"uppercase" }}>
          Automaton AI · Powered by Twilio + Claude
        </p>
      </div>
    </div>
  );
}
