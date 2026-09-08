(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))t(a);new MutationObserver(a=>{for(const i of a)if(i.type==="childList")for(const s of i.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&t(s)}).observe(document,{childList:!0,subtree:!0});function r(a){const i={};return a.integrity&&(i.integrity=a.integrity),a.referrerPolicy&&(i.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?i.credentials="include":a.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function t(a){if(a.ep)return;a.ep=!0;const i=r(a);fetch(a.href,i)}})();const M=[{ticker:"HPG",name:"Tập đoàn Hòa Phát",industry:"Thép",aliases:["hòa phát","h-p-g","hát pơ gờ","h p g","thép hòa phát"],exchange:"HOSE"},{ticker:"SSI",name:"Công ty Cổ phần Chứng khoán SSI",industry:"Chứng khoán",aliases:["ssi","s-s-i","ép-sơ-sơ-y","chứng khoán ssi","chứng khoán s i"],exchange:"HOSE"},{ticker:"VHM",name:"Công ty Cổ phần Vinhomes",industry:"Bất động sản",aliases:["vinhomes","v-h-m","ve hát mờ","v h m","vin home"],exchange:"HOSE"},{ticker:"VIC",name:"Tập đoàn Vingroup",industry:"Bất động sản / Đa ngành",aliases:["vingroup","v-i-c","ve y cờ","v i c","bác vượng"],exchange:"HOSE"},{ticker:"DIG",name:"Tổng Công ty Cổ phần Đầu tư Phát triển Xây dựng (DIC Corp)",industry:"Bất động sản",aliases:["đê y gê","d-i-g","dic corp","d i g","đích corp"],exchange:"HOSE"},{ticker:"CEO",name:"Tập đoàn CEO",industry:"Bất động sản",aliases:["c-e-o","xê e o","c e o","tập đoàn ceo"],exchange:"HNX"},{ticker:"NVL",name:"Công ty Cổ phần Tập đoàn Đầu tư Địa ốc No Va (Novaland)",industry:"Bất động sản",aliases:["novaland","n-v-l","nờ ve lờ","n v l","nova land"],exchange:"HOSE"},{ticker:"MWG",name:"Công ty Cổ phần Đầu tư Thế Giới Di Động",industry:"Bán lẻ",aliases:["thế giới di động","m-w-g","mờ vê gê","m w g","tgdd","bách hóa xanh"],exchange:"HOSE"},{ticker:"FPT",name:"Công ty Cổ phần FPT",industry:"Công nghệ",aliases:["fpt","f-p-t","ép bê tê","f p t","tập đoàn fpt"],exchange:"HOSE"},{ticker:"VCB",name:"Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)",industry:"Ngân hàng",aliases:["vietcombank","vcb","v-c-b","ve xê bê","v c b"],exchange:"HOSE"},{ticker:"TCB",name:"Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank)",industry:"Ngân hàng",aliases:["techcombank","tcb","t-c-b","tê xê bê","t c b"],exchange:"HOSE"},{ticker:"STB",name:"Ngân hàng TMCP Sài Gòn Thương Tín (Sacombank)",industry:"Ngân hàng",aliases:["sacombank","stb","s-t-b","ép tê bê","s t b"],exchange:"HOSE"},{ticker:"PDR",name:"Công ty Cổ phần Phát triển Bất động sản Phát Đạt",industry:"Bất động sản",aliases:["phát đạt","p-d-r","bê dê rờ","p d r"],exchange:"HOSE"},{ticker:"VND",name:"Công ty Cổ phần Chứng khoán VNDIRECT",industry:"Chứng khoán",aliases:["vndirect","vnd","v-n-d","ve nờ dê","v n d"],exchange:"HOSE"},{ticker:"VCI",name:"Công ty Cổ phần Chứng khoán Vietcap",industry:"Chứng khoán",aliases:["vietcap","vci","v-c-i","chứng khoán bản việt","v c i"],exchange:"HOSE"},{ticker:"HSG",name:"Tập đoàn Hoa Sen",industry:"Thép",aliases:["hoa sen","hsg","h-s-g","hát ép gê","thép hoa sen"],exchange:"HOSE"},{ticker:"NKG",name:"Công ty Cổ phần Thép Nam Kim",industry:"Thép",aliases:["nam kim","nkg","n-k-g","nờ ca gê","thép nam kim"],exchange:"HOSE"},{ticker:"DGC",name:"Công ty Cổ phần Tập đoàn Hóa chất Đức Giang",industry:"Hóa chất",aliases:["đức giang","dgc","d-g-c","dê gê xê","hóa chất đức giang"],exchange:"HOSE"},{ticker:"ANV",name:"Công ty Cổ phần Nam Việt",industry:"Thủy sản",aliases:["nam việt","anv","a-n-v","a nờ ve","thủy sản nam việt"],exchange:"HOSE"},{ticker:"VNM",name:"Công ty Cổ phần Sữa Việt Nam (Vinamilk)",industry:"Thực phẩm",aliases:["vinamilk","vnm","v-n-m","ve nờ mờ","sữa vinamilk"],exchange:"HOSE"}];function I(n){if(!n)return[];const e=n.toLowerCase(),r=[],t=new Set;return M.forEach(a=>{if(new RegExp(`\\b${a.ticker.toLowerCase()}\\b`,"gi").test(e)){t.has(a.ticker)||(t.add(a.ticker),r.push({ticker:a.ticker,name:a.name,industry:a.industry,matchedTerm:a.ticker,confidence:.98}));return}for(const s of a.aliases)if(e.includes(s.toLowerCase())){t.has(a.ticker)||(t.add(a.ticker),r.push({ticker:a.ticker,name:a.name,industry:a.industry,matchedTerm:s,confidence:.9}));break}}),r}class N{constructor(e={}){this.frameDuration=e.frameDuration||10,this.overlapDuration=e.overlapDuration||3,this.stepDuration=this.frameDuration-this.overlapDuration,this.bufferFrames=[],this.processedSignals=[]}setParameters(e,r){this.frameDuration=e,this.overlapDuration=r,this.stepDuration=Math.max(1,e-r)}processFrame(e){const r=I(e.rawTranscript),t=this.analyzeFrameContext(e.rawTranscript,r),a={...e,extractedTickers:r,recommendation:t,timestamp:new Date().toLocaleTimeString("vi-VN")};this.bufferFrames.push(a),this.bufferFrames.length>5&&this.bufferFrames.shift();const i=this.synthesizeRollingContext(this.bufferFrames);return{currentFrame:a,rollingContextSummary:i,activeBufferCount:this.bufferFrames.length}}analyzeFrameContext(e,r){const t=e.toLowerCase();let a="THEO DÕI",i=null,s=null;t.includes("mút")||t.includes("mua")||t.includes("gom")||t.includes("mở vị thế")||t.includes("múc")?a="MUA":t.includes("bán")||t.includes("chốt lời")||t.includes("hạ tỷ trọng")||t.includes("ra hàng")?a="BÁN":(t.includes("cắt lỗ")||t.includes("stop loss")||t.includes("quản trị rủi ro"))&&(a="CẮT LỖ");const o=e.match(/(\d+[.,]?\d*)/g);return o&&o.length>0&&((t.includes("kháng cự")||t.includes("mục tiêu")||t.includes("target"))&&(s=o[0]),(t.includes("hỗ trợ")||t.includes("vùng giá")||t.includes("đáy"))&&(i=o[0])),{action:a,tickers:r.map(H=>H.ticker),support:i,resistance:s,summarySnippet:e}}synthesizeRollingContext(e){if(!e||e.length===0)return null;const r=new Map,t=[];e.forEach(i=>{t.push(i.rawTranscript),i.extractedTickers.forEach(s=>{r.has(s.ticker)||r.set(s.ticker,{...s,actionCount:{MUA:0,BÁN:0,"THEO DÕI":0},lastMentionedFrame:i.id,transcripts:[]});const o=r.get(s.ticker);o.actionCount[i.recommendation.action]=(o.actionCount[i.recommendation.action]||0)+1,o.transcripts.push(i.rawTranscript)})});const a=Array.from(r.values()).map(i=>{let s="THEO DÕI";return i.actionCount.MUA>i.actionCount.BÁN?s="MUA (Khuyên Dùng)":i.actionCount.BÁN>i.actionCount.MUA&&(s="BÁN / CHỐT LỜI"),{ticker:i.ticker,name:i.name,industry:i.industry,consensusAction:s,mentionFrequency:i.transcripts.length}});return{windowTimeRange:`${e[0].startTime}s - ${e[e.length-1].endTime}s`,mergedTranscript:t.join(" ... "),activeTickers:a,totalFramesCombined:e.length}}}const l=[{id:1,startTime:0,endTime:10,rawTranscript:"Chào anh em nha, hôm nay VN-Index giữ nhịp rất tốt quanh vùng 1280 điểm. Hôm nay dòng thép đang có dấu hiệu mút mạnh đặc biệt là Hòa Phát.",audioSnippetLabel:"Frame 001 [0s - 10s]"},{id:2,startTime:7,endTime:17,rawTranscript:"...dấu hiệu mút mạnh đặc biệt là Hòa Phát con HPG giá 28.5 này anh em gom dần vùng này được, mục tiêu ngắn hạn cản 31 nhé.",audioSnippetLabel:"Frame 002 [7s - 17s] (Overlap 3s)"},{id:3,startTime:14,endTime:24,rawTranscript:"...gom dần vùng giá này. Tiếp theo về nhóm chứng khoán thì anh chị em chú ý cổ phiếu SSI nhé. Ép-sơ-sơ-y hiện tại đang tạo đáy 2 rất đẹp.",audioSnippetLabel:"Frame 003 [14s - 24s] (Overlap 3s)"},{id:4,startTime:21,endTime:31,rawTranscript:"...đang tạo đáy 2 rất đẹp. SSI quanh 34.5 anh em mở vị thế được, kháng cự quanh 37. Còn dòng bất động sản con Đê Y Gê thì thôi ra hàng đi.",audioSnippetLabel:"Frame 004 [21s - 31s] (Overlap 3s)"},{id:5,startTime:28,endTime:38,rawTranscript:"...bất động sản con Đê Y Gê con DIG yếu quá, anh em nên hạ tỷ trọng bán chốt lời hoặc hạ margin vùng 26 nhé.",audioSnippetLabel:"Frame 005 [28s - 38s] (Overlap 3s)"},{id:6,startTime:35,endTime:45,rawTranscript:"...hạ margin vùng 26. Còn Novaland NVL thì ai đang cầm vùng giá 14 hỗ trợ tốt, tiếp tục nắm giữ chờ sóng tới.",audioSnippetLabel:"Frame 006 [35s - 45s] (Overlap 3s)"}],h=new N({frameDuration:10,overlapDuration:3});let c=0,y=!1,g=null;const b=document.getElementById("btnStartSim"),w=document.getElementById("btnStepNext"),O=document.getElementById("btnResetSim"),d=document.getElementById("statusText"),k=document.getElementById("frameProgressText"),S=document.getElementById("timelineProgressBar"),p=document.getElementById("transcriptContainer"),x=document.getElementById("tickerSignalsContainer"),v=document.getElementById("frameDetailsTableBody"),E=document.getElementById("detectedTickersCount"),T=document.getElementById("sliderFrameLength"),C=document.getElementById("sliderOverlapLength"),$=document.getElementById("frameLengthVal"),F=document.getElementById("overlapLengthVal"),D=document.getElementById("stepValText"),V=document.getElementById("overlapConfigLabel"),m=document.getElementById("codeModal"),P=document.getElementById("toggleCodeModalBtn"),A=document.getElementById("closeCodeModalBtn");function R(){G(),q(),L()}function G(){const n=()=>{const e=parseInt(T.value,10),r=parseInt(C.value,10),t=Math.min(r,e-1),a=e-t;$.textContent=`${e}s`,F.textContent=`${t}s (${Math.round(t/e*100)}%)`,D.textContent=`${a}s / frame`,V.textContent=`${t}s (${Math.round(t/e*100)}%)`,h.setParameters(e,t)};T.addEventListener("input",n),C.addEventListener("input",n)}function q(){b.addEventListener("click",()=>{y?u():z()}),w.addEventListener("click",()=>{u(),f()}),O.addEventListener("click",()=>{j()}),P.addEventListener("click",()=>{m.classList.remove("hidden")}),A.addEventListener("click",()=>{m.classList.add("hidden")}),m.addEventListener("click",n=>{n.target===m&&m.classList.add("hidden")})}function z(){y=!0,d.textContent="Đang Stream Audio Live",d.className="text-emerald-400 font-bold animate-pulse",b.innerHTML=`
    <svg class="w-4 h-4 text-slate-950" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
    </svg>
    Tạm Dừng Stream
  `,c<l.length&&f(),g=setInterval(()=>{if(c>=l.length){u(),d.textContent="Hoàn Thành Livestream",d.className="text-cyan-400 font-bold";return}f()},3500)}function u(){y=!1,g&&clearInterval(g),d.textContent="Đang Tạm Dừng",d.className="text-amber-400 font-semibold",b.innerHTML=`
    <svg class="w-4 h-4 text-slate-950" fill="currentColor" viewBox="0 0 20 20">
      <path d="M4 4l12 6-12 6V4z"/>
    </svg>
    Tiếp Tục Live Stream
  `}function j(){u(),c=0,h.bufferFrames=[],h.processedSignals=[],d.textContent="Sẵn sàng",d.className="text-slate-200 font-normal",k.textContent="Chờ bắt đầu (0 / 6 frames)",S.style.width="0%",E.textContent="0 mã",L()}function L(){p.innerHTML=`
    <div class="text-slate-500 italic text-center py-12">
      Bấm "Chạy Demo Live Stream" hoặc "Next Frame" để bắt đầu nhận audio STT frame-by-frame...
    </div>
  `,x.innerHTML=`
    <div class="text-slate-500 italic text-center py-12 text-xs">
      Chưa phát hiện mã chứng khoán. Hệ thống sẽ lọc mã (HPG, SSI, DIG, NVL, VHM...) khi stream chạy.
    </div>
  `,v.innerHTML=`
    <tr>
      <td colspan="5" class="py-8 text-center text-slate-500 italic">
        Chưa có dữ liệu frame nào được xử lý.
      </td>
    </tr>
  `}function f(){if(c>=l.length)return;const n=l[c],e=h.processFrame(n);c++;const r=Math.round(c/l.length*100);S.style.width=`${r}%`,k.textContent=`Đang xử lý Frame ${c} / ${l.length} (${n.startTime}s - ${n.endTime}s)`,K(e.currentFrame),U(e.rollingContextSummary),_(e.currentFrame)}function K(n){c===1&&(p.innerHTML="");let e=n.rawTranscript;n.extractedTickers.forEach(t=>{const a=new RegExp(`(${t.matchedTerm})`,"gi");e=e.replace(a,`<mark class="bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded font-bold border border-emerald-500/30">$1 [Mã: ${t.ticker}]</mark>`)});const r=`
    <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2 new-frame-pulse">
      <div class="flex items-center justify-between text-[11px] text-slate-400">
        <div class="flex items-center gap-2">
          <span class="font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold">
            ${n.audioSnippetLabel}
          </span>
          <span class="text-slate-500">${n.timestamp}</span>
        </div>
        <span class="text-xs font-semibold ${B(n.recommendation.action)}">
          Tín hiệu: ${n.recommendation.action}
        </span>
      </div>

      <div class="text-slate-200 text-xs leading-relaxed">
        "${e}"
      </div>
    </div>
  `;p.insertAdjacentHTML("afterbegin",r)}function U(n){!n||!n.activeTickers||n.activeTickers.length===0||(E.textContent=`${n.activeTickers.length} mã`,x.innerHTML="",n.activeTickers.forEach(e=>{const r=Y(e.consensusAction),t=`
      <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3 hover:border-slate-700 transition">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-base text-emerald-400 shadow-inner">
              ${e.ticker}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h4 class="text-xs font-bold text-white">${e.name}</h4>
                <span class="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">${e.industry}</span>
              </div>
              <p class="text-[11px] text-slate-400 mt-0.5">Tần suất nhắc tới: ${e.mentionFrequency} frames</p>
            </div>
          </div>
          <span class="px-2.5 py-1 rounded-lg text-xs font-bold ${r}">
            ${e.consensusAction}
          </span>
        </div>

        <div class="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 text-[11px] text-slate-300">
          <div class="text-slate-400 font-medium mb-1">💡 Tóm tắt nhận định Broker từ Overlap Context:</div>
          <p class="italic text-slate-300">Broker đánh giá tích cực với ${e.ticker}, khuyến nghị theo sát điểm mua quanh vùng hỗ trợ và chú ý mốc kháng cự ngắn hạn.</p>
        </div>
      </div>
    `;x.insertAdjacentHTML("beforeend",t)}))}function _(n){c===1&&(v.innerHTML="");const e=n.extractedTickers.map(t=>`<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800/60 mr-1 mb-1">
      ${t.ticker} (${t.matchedTerm})
    </span>`).join("")||'<span class="text-slate-500 italic">Không tìm thấy mã</span>',r=`
    <tr class="hover:bg-slate-800/30 transition">
      <td class="py-3 px-4 font-mono text-emerald-400 font-semibold">
        Frame #${n.id} (${n.startTime}s - ${n.endTime}s)
      </td>
      <td class="py-3 px-4 text-slate-400">
        ${n.audioSnippetLabel}
      </td>
      <td class="py-3 px-4 text-slate-200 max-w-xs truncate">
        ${n.rawTranscript}
      </td>
      <td class="py-3 px-4">
        ${e}
      </td>
      <td class="py-3 px-4 font-bold ${B(n.recommendation.action)}">
        ${n.recommendation.action}
      </td>
    </tr>
  `;v.insertAdjacentHTML("afterbegin",r)}function B(n){return n.includes("MUA")?"text-emerald-400":n.includes("BÁN")?"text-rose-400":n.includes("CẮT")?"text-amber-400":"text-cyan-400"}function Y(n){return n.includes("MUA")?"bg-emerald-500/20 text-emerald-300 border border-emerald-500/40":n.includes("BÁN")?"bg-rose-500/20 text-rose-300 border border-rose-500/40":n.includes("CẮT")?"bg-amber-500/20 text-amber-300 border border-amber-500/40":"bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"}document.addEventListener("DOMContentLoaded",R);
