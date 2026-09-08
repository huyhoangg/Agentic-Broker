// Vietnamese Stock Ticker Dictionary & Mapper Database
export const VN_STOCK_DICTIONARY = [
  {
    ticker: "HPG",
    name: "Tập đoàn Hòa Phát",
    industry: "Thép",
    aliases: ["hòa phát", "h-p-g", "hát pơ gờ", "h p g", "thép hòa phát"],
    exchange: "HOSE"
  },
  {
    ticker: "SSI",
    name: "Công ty Cổ phần Chứng khoán SSI",
    industry: "Chứng khoán",
    aliases: ["ssi", "s-s-i", "ép-sơ-sơ-y", "chứng khoán ssi", "chứng khoán s i"],
    exchange: "HOSE"
  },
  {
    ticker: "VHM",
    name: "Công ty Cổ phần Vinhomes",
    industry: "Bất động sản",
    aliases: ["vinhomes", "v-h-m", "ve hát mờ", "v h m", "vin home"],
    exchange: "HOSE"
  },
  {
    ticker: "VIC",
    name: "Tập đoàn Vingroup",
    industry: "Bất động sản / Đa ngành",
    aliases: ["vingroup", "v-i-c", "ve y cờ", "v i c", "bác vượng"],
    exchange: "HOSE"
  },
  {
    ticker: "DIG",
    name: "Tổng Công ty Cổ phần Đầu tư Phát triển Xây dựng (DIC Corp)",
    industry: "Bất động sản",
    aliases: ["đê y gê", "d-i-g", "dic corp", "d i g", "đích corp"],
    exchange: "HOSE"
  },
  {
    ticker: "CEO",
    name: "Tập đoàn CEO",
    industry: "Bất động sản",
    aliases: ["c-e-o", "xê e o", "c e o", "tập đoàn ceo"],
    exchange: "HNX"
  },
  {
    ticker: "NVL",
    name: "Công ty Cổ phần Tập đoàn Đầu tư Địa ốc No Va (Novaland)",
    industry: "Bất động sản",
    aliases: ["novaland", "n-v-l", "nờ ve lờ", "n v l", "nova land"],
    exchange: "HOSE"
  },
  {
    ticker: "MWG",
    name: "Công ty Cổ phần Đầu tư Thế Giới Di Động",
    industry: "Bán lẻ",
    aliases: ["thế giới di động", "m-w-g", "mờ vê gê", "m w g", "tgdd", "bách hóa xanh"],
    exchange: "HOSE"
  },
  {
    ticker: "FPT",
    name: "Công ty Cổ phần FPT",
    industry: "Công nghệ",
    aliases: ["fpt", "f-p-t", "ép bê tê", "f p t", "tập đoàn fpt"],
    exchange: "HOSE"
  },
  {
    ticker: "VCB",
    name: "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)",
    industry: "Ngân hàng",
    aliases: ["vietcombank", "vcb", "v-c-b", "ve xê bê", "v c b"],
    exchange: "HOSE"
  },
  {
    ticker: "TCB",
    name: "Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank)",
    industry: "Ngân hàng",
    aliases: ["techcombank", "tcb", "t-c-b", "tê xê bê", "t c b"],
    exchange: "HOSE"
  },
  {
    ticker: "STB",
    name: "Ngân hàng TMCP Sài Gòn Thương Tín (Sacombank)",
    industry: "Ngân hàng",
    aliases: ["sacombank", "stb", "s-t-b", "ép tê bê", "s t b"],
    exchange: "HOSE"
  },
  {
    ticker: "PDR",
    name: "Công ty Cổ phần Phát triển Bất động sản Phát Đạt",
    industry: "Bất động sản",
    aliases: ["phát đạt", "p-d-r", "bê dê rờ", "p d r"],
    exchange: "HOSE"
  },
  {
    ticker: "VND",
    name: "Công ty Cổ phần Chứng khoán VNDIRECT",
    industry: "Chứng khoán",
    aliases: ["vndirect", "vnd", "v-n-d", "ve nờ dê", "v n d"],
    exchange: "HOSE"
  },
  {
    ticker: "VCI",
    name: "Công ty Cổ phần Chứng khoán Vietcap",
    industry: "Chứng khoán",
    aliases: ["vietcap", "vci", "v-c-i", "chứng khoán bản việt", "v c i"],
    exchange: "HOSE"
  },
  {
    ticker: "HSG",
    name: "Tập đoàn Hoa Sen",
    industry: "Thép",
    aliases: ["hoa sen", "hsg", "h-s-g", "hát ép gê", "thép hoa sen"],
    exchange: "HOSE"
  },
  {
    ticker: "NKG",
    name: "Công ty Cổ phần Thép Nam Kim",
    industry: "Thép",
    aliases: ["nam kim", "nkg", "n-k-g", "nờ ca gê", "thép nam kim"],
    exchange: "HOSE"
  },
  {
    ticker: "DGC",
    name: "Công ty Cổ phần Tập đoàn Hóa chất Đức Giang",
    industry: "Hóa chất",
    aliases: ["đức giang", "dgc", "d-g-c", "dê gê xê", "hóa chất đức giang"],
    exchange: "HOSE"
  },
  {
    ticker: "ANV",
    name: "Công ty Cổ phần Nam Việt",
    industry: "Thủy sản",
    aliases: ["nam việt", "anv", "a-n-v", "a nờ ve", "thủy sản nam việt"],
    exchange: "HOSE"
  },
  {
    ticker: "VNM",
    name: "Công ty Cổ phần Sữa Việt Nam (Vinamilk)",
    industry: "Thực phẩm",
    aliases: ["vinamilk", "vnm", "v-n-m", "ve nờ mờ", "sữa vinamilk"],
    exchange: "HOSE"
  }
];

/**
 * Scan raw speech text and detect mapped VN stock tickers
 * @param {string} text - Raw speech text from STT engine
 * @returns {Array<{ticker: string, matchedTerm: string, confidence: number}>}
 */
export function extractStockTickers(text) {
  if (!text) return [];
  const normalizedText = text.toLowerCase();
  const results = [];
  const foundTickers = new Set();

  VN_STOCK_DICTIONARY.forEach(stock => {
    // 1. Direct Ticker search (e.g., "HPG", "SSI")
    const tickerRegex = new RegExp(`\\b${stock.ticker.toLowerCase()}\\b`, 'gi');
    if (tickerRegex.test(normalizedText)) {
      if (!foundTickers.has(stock.ticker)) {
        foundTickers.add(stock.ticker);
        results.push({
          ticker: stock.ticker,
          name: stock.name,
          industry: stock.industry,
          matchedTerm: stock.ticker,
          confidence: 0.98
        });
      }
      return;
    }

    // 2. Alias / Spoken phonetics search (e.g., "hòa phát", "đê y gê")
    for (const alias of stock.aliases) {
      if (normalizedText.includes(alias.toLowerCase())) {
        if (!foundTickers.has(stock.ticker)) {
          foundTickers.add(stock.ticker);
          results.push({
            ticker: stock.ticker,
            name: stock.name,
            industry: stock.industry,
            matchedTerm: alias,
            confidence: 0.90
          });
        }
        break;
      }
    }
  });

  return results;
}
