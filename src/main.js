import { AudioWindowProcessor, SAMPLE_BROKER_LIVESTREAM_FRAMES } from './audio_processor.js';
import { VN_STOCK_DICTIONARY } from './stock_dictionary.js';

// Instantiate Audio Window Processor
const processor = new AudioWindowProcessor({ frameDuration: 10, overlapDuration: 3 });

let currentFrameIndex = 0;
let isSimulationRunning = false;
let simInterval = null;

// DOM Elements
const btnStartSim = document.getElementById('btnStartSim');
const btnStepNext = document.getElementById('btnStepNext');
const btnResetSim = document.getElementById('btnResetSim');
const statusText = document.getElementById('statusText');
const frameProgressText = document.getElementById('frameProgressText');
const timelineProgressBar = document.getElementById('timelineProgressBar');
const transcriptContainer = document.getElementById('transcriptContainer');
const tickerSignalsContainer = document.getElementById('tickerSignalsContainer');
const frameDetailsTableBody = document.getElementById('frameDetailsTableBody');
const detectedTickersCount = document.getElementById('detectedTickersCount');

const sliderFrameLength = document.getElementById('sliderFrameLength');
const sliderOverlapLength = document.getElementById('sliderOverlapLength');
const frameLengthVal = document.getElementById('frameLengthVal');
const overlapLengthVal = document.getElementById('overlapLengthVal');
const stepValText = document.getElementById('stepValText');
const overlapConfigLabel = document.getElementById('overlapConfigLabel');

const codeModal = document.getElementById('codeModal');
const toggleCodeModalBtn = document.getElementById('toggleCodeModalBtn');
const closeCodeModalBtn = document.getElementById('closeCodeModalBtn');

// Initial Setup & Event Listeners
function initApp() {
  setupSliderControls();
  setupEventListeners();
  updateUIEmptyStates();
}

function setupSliderControls() {
  const updateConfig = () => {
    const frameDur = parseInt(sliderFrameLength.value, 10);
    const overlapDur = parseInt(sliderOverlapLength.value, 10);
    
    // Ensure overlap is less than frame duration
    const validOverlap = Math.min(overlapDur, frameDur - 1);
    const stepDur = frameDur - validOverlap;
    
    frameLengthVal.textContent = `${frameDur}s`;
    overlapLengthVal.textContent = `${validOverlap}s (${Math.round((validOverlap/frameDur)*100)}%)`;
    stepValText.textContent = `${stepDur}s / frame`;
    overlapConfigLabel.textContent = `${validOverlap}s (${Math.round((validOverlap/frameDur)*100)}%)`;

    processor.setParameters(frameDur, validOverlap);
  };

  sliderFrameLength.addEventListener('input', updateConfig);
  sliderOverlapLength.addEventListener('input', updateConfig);
}

function setupEventListeners() {
  btnStartSim.addEventListener('click', () => {
    if (isSimulationRunning) {
      pauseSimulation();
    } else {
      startSimulation();
    }
  });

  btnStepNext.addEventListener('click', () => {
    pauseSimulation();
    stepNextFrame();
  });

  btnResetSim.addEventListener('click', () => {
    resetSimulation();
  });

  toggleCodeModalBtn.addEventListener('click', () => {
    codeModal.classList.remove('hidden');
  });

  closeCodeModalBtn.addEventListener('click', () => {
    codeModal.classList.add('hidden');
  });

  codeModal.addEventListener('click', (e) => {
    if (e.target === codeModal) {
      codeModal.classList.add('hidden');
    }
  });
}

function startSimulation() {
  isSimulationRunning = true;
  statusText.textContent = "Đang Stream Audio Live";
  statusText.className = "text-emerald-400 font-bold animate-pulse";

  btnStartSim.innerHTML = `
    <svg class="w-4 h-4 text-slate-950" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
    </svg>
    Tạm Dừng Stream
  `;

  // Step immediately once, then loop every 3 seconds
  if (currentFrameIndex < SAMPLE_BROKER_LIVESTREAM_FRAMES.length) {
    stepNextFrame();
  }

  simInterval = setInterval(() => {
    if (currentFrameIndex >= SAMPLE_BROKER_LIVESTREAM_FRAMES.length) {
      pauseSimulation();
      statusText.textContent = "Hoàn Thành Livestream";
      statusText.className = "text-cyan-400 font-bold";
      return;
    }
    stepNextFrame();
  }, 3500);
}

function pauseSimulation() {
  isSimulationRunning = false;
  if (simInterval) clearInterval(simInterval);
  statusText.textContent = "Đang Tạm Dừng";
  statusText.className = "text-amber-400 font-semibold";

  btnStartSim.innerHTML = `
    <svg class="w-4 h-4 text-slate-950" fill="currentColor" viewBox="0 0 20 20">
      <path d="M4 4l12 6-12 6V4z"/>
    </svg>
    Tiếp Tục Live Stream
  `;
}

function resetSimulation() {
  pauseSimulation();
  currentFrameIndex = 0;
  processor.bufferFrames = [];
  processor.processedSignals = [];

  statusText.textContent = "Sẵn sàng";
  statusText.className = "text-slate-200 font-normal";
  frameProgressText.textContent = "Chờ bắt đầu (0 / 6 frames)";
  timelineProgressBar.style.width = "0%";
  detectedTickersCount.textContent = "0 mã";

  updateUIEmptyStates();
}

function updateUIEmptyStates() {
  transcriptContainer.innerHTML = `
    <div class="text-slate-500 italic text-center py-12">
      Bấm "Chạy Demo Live Stream" hoặc "Next Frame" để bắt đầu nhận audio STT frame-by-frame...
    </div>
  `;

  tickerSignalsContainer.innerHTML = `
    <div class="text-slate-500 italic text-center py-12 text-xs">
      Chưa phát hiện mã chứng khoán. Hệ thống sẽ lọc mã (HPG, SSI, DIG, NVL, VHM...) khi stream chạy.
    </div>
  `;

  frameDetailsTableBody.innerHTML = `
    <tr>
      <td colspan="5" class="py-8 text-center text-slate-500 italic">
        Chưa có dữ liệu frame nào được xử lý.
      </td>
    </tr>
  `;
}

function stepNextFrame() {
  if (currentFrameIndex >= SAMPLE_BROKER_LIVESTREAM_FRAMES.length) return;

  const rawFrame = SAMPLE_BROKER_LIVESTREAM_FRAMES[currentFrameIndex];
  const result = processor.processFrame(rawFrame);

  currentFrameIndex++;

  // Update timeline visualizer
  const progressPercent = Math.round((currentFrameIndex / SAMPLE_BROKER_LIVESTREAM_FRAMES.length) * 100);
  timelineProgressBar.style.width = `${progressPercent}%`;
  frameProgressText.textContent = `Đang xử lý Frame ${currentFrameIndex} / ${SAMPLE_BROKER_LIVESTREAM_FRAMES.length} (${rawFrame.startTime}s - ${rawFrame.endTime}s)`;

  // Render to UI components
  renderTranscriptFeed(result.currentFrame);
  renderTickerSignalCards(result.rollingContextSummary);
  renderFrameDetailsRow(result.currentFrame);
}

function renderTranscriptFeed(frame) {
  // If first frame, clear empty placeholder
  if (currentFrameIndex === 1) {
    transcriptContainer.innerHTML = '';
  }

  // Highlight stock symbols in transcript text
  let highlightedText = frame.rawTranscript;
  frame.extractedTickers.forEach(t => {
    const termRegex = new RegExp(`(${t.matchedTerm})`, 'gi');
    highlightedText = highlightedText.replace(termRegex, `<mark class="bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded font-bold border border-emerald-500/30">$1 [Mã: ${t.ticker}]</mark>`);
  });

  const cardHtml = `
    <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2 new-frame-pulse">
      <div class="flex items-center justify-between text-[11px] text-slate-400">
        <div class="flex items-center gap-2">
          <span class="font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold">
            ${frame.audioSnippetLabel}
          </span>
          <span class="text-slate-500">${frame.timestamp}</span>
        </div>
        <span class="text-xs font-semibold ${getActionBadgeColor(frame.recommendation.action)}">
          Tín hiệu: ${frame.recommendation.action}
        </span>
      </div>

      <div class="text-slate-200 text-xs leading-relaxed">
        "${highlightedText}"
      </div>
    </div>
  `;

  transcriptContainer.insertAdjacentHTML('afterbegin', cardHtml);
}

function renderTickerSignalCards(rollingContext) {
  if (!rollingContext || !rollingContext.activeTickers || rollingContext.activeTickers.length === 0) return;

  detectedTickersCount.textContent = `${rollingContext.activeTickers.length} mã`;
  tickerSignalsContainer.innerHTML = '';

  rollingContext.activeTickers.forEach(stock => {
    const actionBadge = getActionBadgeStyle(stock.consensusAction);
    
    const card = `
      <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3 hover:border-slate-700 transition">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-base text-emerald-400 shadow-inner">
              ${stock.ticker}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h4 class="text-xs font-bold text-white">${stock.name}</h4>
                <span class="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">${stock.industry}</span>
              </div>
              <p class="text-[11px] text-slate-400 mt-0.5">Tần suất nhắc tới: ${stock.mentionFrequency} frames</p>
            </div>
          </div>
          <span class="px-2.5 py-1 rounded-lg text-xs font-bold ${actionBadge}">
            ${stock.consensusAction}
          </span>
        </div>

        <div class="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 text-[11px] text-slate-300">
          <div class="text-slate-400 font-medium mb-1">💡 Tóm tắt nhận định Broker từ Overlap Context:</div>
          <p class="italic text-slate-300">Broker đánh giá tích cực với ${stock.ticker}, khuyến nghị theo sát điểm mua quanh vùng hỗ trợ và chú ý mốc kháng cự ngắn hạn.</p>
        </div>
      </div>
    `;

    tickerSignalsContainer.insertAdjacentHTML('beforeend', card);
  });
}

function renderFrameDetailsRow(frame) {
  if (currentFrameIndex === 1) {
    frameDetailsTableBody.innerHTML = '';
  }

  const tickersFormatted = frame.extractedTickers.map(t => 
    `<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800/60 mr-1 mb-1">
      ${t.ticker} (${t.matchedTerm})
    </span>`
  ).join('') || `<span class="text-slate-500 italic">Không tìm thấy mã</span>`;

  const rowHtml = `
    <tr class="hover:bg-slate-800/30 transition">
      <td class="py-3 px-4 font-mono text-emerald-400 font-semibold">
        Frame #${frame.id} (${frame.startTime}s - ${frame.endTime}s)
      </td>
      <td class="py-3 px-4 text-slate-400">
        ${frame.audioSnippetLabel}
      </td>
      <td class="py-3 px-4 text-slate-200 max-w-xs truncate">
        ${frame.rawTranscript}
      </td>
      <td class="py-3 px-4">
        ${tickersFormatted}
      </td>
      <td class="py-3 px-4 font-bold ${getActionBadgeColor(frame.recommendation.action)}">
        ${frame.recommendation.action}
      </td>
    </tr>
  `;

  frameDetailsTableBody.insertAdjacentHTML('afterbegin', rowHtml);
}

function getActionBadgeColor(action) {
  if (action.includes('MUA')) return 'text-emerald-400';
  if (action.includes('BÁN')) return 'text-rose-400';
  if (action.includes('CẮT')) return 'text-amber-400';
  return 'text-cyan-400';
}

function getActionBadgeStyle(action) {
  if (action.includes('MUA')) return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
  if (action.includes('BÁN')) return 'bg-rose-500/20 text-rose-300 border border-rose-500/40';
  if (action.includes('CẮT')) return 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
  return 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40';
}

// Start app when DOM ready
document.addEventListener('DOMContentLoaded', initApp);
