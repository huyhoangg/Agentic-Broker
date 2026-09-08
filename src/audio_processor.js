// Audio Pipeline Simulator & Sliding Window Buffer Engine
import { extractStockTickers } from './stock_dictionary.js';

export class AudioWindowProcessor {
  constructor(options = {}) {
    this.frameDuration = options.frameDuration || 10; // seconds
    this.overlapDuration = options.overlapDuration || 3; // seconds
    this.stepDuration = this.frameDuration - this.overlapDuration; // 7s
    this.bufferFrames = [];
    this.processedSignals = [];
  }

  setParameters(frameDuration, overlapDuration) {
    this.frameDuration = frameDuration;
    this.overlapDuration = overlapDuration;
    this.stepDuration = Math.max(1, frameDuration - overlapDuration);
  }

  /**
   * Process a single 10s audio frame input
   * @param {Object} rawFrame - { id, startTime, endTime, audioSnippetLabel, rawTranscript }
   */
  processFrame(rawFrame) {
    // 1. STT Speech To Text Simulation / Extraction
    const tickers = extractStockTickers(rawFrame.rawTranscript);

    // 2. Extract key trading recommendation context from frame
    const recommendation = this.analyzeFrameContext(rawFrame.rawTranscript, tickers);

    const frameResult = {
      ...rawFrame,
      extractedTickers: tickers,
      recommendation: recommendation,
      timestamp: new Date().toLocaleTimeString('vi-VN')
    };

    this.bufferFrames.push(frameResult);

    // Keep sliding buffer of last 5 frames (approx 35s-50s rolling context)
    if (this.bufferFrames.length > 5) {
      this.bufferFrames.shift();
    }

    // 3. Perform Overlap Context Synthesis (Loại bỏ trùng lặp & ghép context từ nhiều frame)
    const rollingContextSummary = this.synthesizeRollingContext(this.bufferFrames);

    return {
      currentFrame: frameResult,
      rollingContextSummary,
      activeBufferCount: this.bufferFrames.length
    };
  }

  /**
   * Heuristic sentiment & trading recommendation analyzer per text chunk
   */
  analyzeFrameContext(text, tickers) {
    const lower = text.toLowerCase();

    let action = "THEO DÕI"; // MUA, BÁN, THEO DÕI, CẮT LỖ
    let target = null;
    let support = null;
    let resistance = null;
    let confidence = "Trung bình";

    if (lower.includes("mút") || lower.includes("mua") || lower.includes("gom") || lower.includes("mở vị thế") || lower.includes("múc")) {
      action = "MUA";
    } else if (lower.includes("bán") || lower.includes("chốt lời") || lower.includes("hạ tỷ trọng") || lower.includes("ra hàng")) {
      action = "BÁN";
    } else if (lower.includes("cắt lỗ") || lower.includes("stop loss") || lower.includes("quản trị rủi ro")) {
      action = "CẮT LỖ";
    }

    // Target / Price extraction regex
    const priceMatches = text.match(/(\d+[.,]?\d*)/g);
    if (priceMatches && priceMatches.length > 0) {
      if (lower.includes("kháng cự") || lower.includes("mục tiêu") || lower.includes("target")) {
        resistance = priceMatches[0];
      }
      if (lower.includes("hỗ trợ") || lower.includes("vùng giá") || lower.includes("đáy")) {
        support = priceMatches[0];
      }
    }

    return {
      action,
      tickers: tickers.map(t => t.ticker),
      support,
      resistance,
      summarySnippet: text
    };
  }

  /**
   * Synthesize overlapping audio frames to build deduplicated rolling summary
   */
  synthesizeRollingContext(frames) {
    if (!frames || frames.length === 0) return null;

    // Deduplicate tickers across overlapping window
    const tickerMap = new Map();
    const transcripts = [];

    frames.forEach(f => {
      transcripts.push(f.rawTranscript);
      f.extractedTickers.forEach(t => {
        if (!tickerMap.has(t.ticker)) {
          tickerMap.set(t.ticker, {
            ...t,
            actionCount: { MUA: 0, BÁN: 0, "THEO DÕI": 0 },
            lastMentionedFrame: f.id,
            transcripts: []
          });
        }
        const item = tickerMap.get(t.ticker);
        item.actionCount[f.recommendation.action] = (item.actionCount[f.recommendation.action] || 0) + 1;
        item.transcripts.push(f.rawTranscript);
      });
    });

    const activeTickers = Array.from(tickerMap.values()).map(item => {
      // Determine consensus action
      let finalAction = "THEO DÕI";
      if (item.actionCount.MUA > item.actionCount.BÁN) finalAction = "MUA (Khuyên Dùng)";
      else if (item.actionCount.BÁN > item.actionCount.MUA) finalAction = "BÁN / CHỐT LỜI";

      return {
        ticker: item.ticker,
        name: item.name,
        industry: item.industry,
        consensusAction: finalAction,
        mentionFrequency: item.transcripts.length
      };
    });

    return {
      windowTimeRange: `${frames[0].startTime}s - ${frames[frames.length - 1].endTime}s`,
      mergedTranscript: transcripts.join(" ... "),
      activeTickers,
      totalFramesCombined: frames.length
    };
  }
}

// Sample realistic VN Stock Broker Livestream Simulation Scripts
export const SAMPLE_BROKER_LIVESTREAM_FRAMES = [
  {
    id: 1,
    startTime: 0,
    endTime: 10,
    rawTranscript: "Chào anh em nha, hôm nay VN-Index giữ nhịp rất tốt quanh vùng 1280 điểm. Hôm nay dòng thép đang có dấu hiệu mút mạnh đặc biệt là Hòa Phát.",
    audioSnippetLabel: "Frame 001 [0s - 10s]"
  },
  {
    id: 2,
    startTime: 7,
    endTime: 17,
    rawTranscript: "...dấu hiệu mút mạnh đặc biệt là Hòa Phát con HPG giá 28.5 này anh em gom dần vùng này được, mục tiêu ngắn hạn cản 31 nhé.",
    audioSnippetLabel: "Frame 002 [7s - 17s] (Overlap 3s)"
  },
  {
    id: 3,
    startTime: 14,
    endTime: 24,
    rawTranscript: "...gom dần vùng giá này. Tiếp theo về nhóm chứng khoán thì anh chị em chú ý cổ phiếu SSI nhé. Ép-sơ-sơ-y hiện tại đang tạo đáy 2 rất đẹp.",
    audioSnippetLabel: "Frame 003 [14s - 24s] (Overlap 3s)"
  },
  {
    id: 4,
    startTime: 21,
    endTime: 31,
    rawTranscript: "...đang tạo đáy 2 rất đẹp. SSI quanh 34.5 anh em mở vị thế được, kháng cự quanh 37. Còn dòng bất động sản con Đê Y Gê thì thôi ra hàng đi.",
    audioSnippetLabel: "Frame 004 [21s - 31s] (Overlap 3s)"
  },
  {
    id: 5,
    startTime: 28,
    endTime: 38,
    rawTranscript: "...bất động sản con Đê Y Gê con DIG yếu quá, anh em nên hạ tỷ trọng bán chốt lời hoặc hạ margin vùng 26 nhé.",
    audioSnippetLabel: "Frame 005 [28s - 38s] (Overlap 3s)"
  },
  {
    id: 6,
    startTime: 35,
    endTime: 45,
    rawTranscript: "...hạ margin vùng 26. Còn Novaland NVL thì ai đang cầm vùng giá 14 hỗ trợ tốt, tiếp tục nắm giữ chờ sóng tới.",
    audioSnippetLabel: "Frame 006 [35s - 45s] (Overlap 3s)"
  }
];
