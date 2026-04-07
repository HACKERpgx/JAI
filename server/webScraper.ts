import axios from "axios";
import * as cheerio from "cheerio";

// Get API keys from environment
const SERPAPI_KEY = process.env.SERPAPI_KEY;
const NEWSAPI_KEY = process.env.NEWSAPI_KEY;

// Keywords that indicate real-time data is needed
const REAL_TIME_KEYWORDS = [
  "live", "score", "today", "now", "latest", "current", "price",
  "weather", "news", "headline", "bitcoin", "crypto", "stock",
  "market", "update", "cricket", "football", "sports", "search",
  "find", "lookup", "info", "information"
];

// Scraping sources
const SCRAPING_SOURCES = {
  cricket: {
    url: "https://www.cricbuzz.com/cricket-match/live-scores",
    selector: ".cb-mtch-lst .cb-lv-scrs-col"
  },
  bitcoin: {
    url: "https://coinmarketcap.com/currencies/bitcoin/",
    selector: ".priceValue"
  },
  news: {
    url: "https://news.google.com/topstories",
    selector: "article h4"
  }
};

export interface ScrapingResult {
  source: string;
  data: string;
  isLive: boolean;
  url?: string;
}

/**
 * Detect if a query requires real-time data
 */
export function requiresRealTimeData(query: string): boolean {
  const lowerQuery = query.toLowerCase();
  return REAL_TIME_KEYWORDS.some(keyword => lowerQuery.includes(keyword));
}

/**
 * Extract query intent
 */
export function extractQueryIntent(query: string): string | null {
  const lowerQuery = query.toLowerCase();
  
  if (lowerQuery.includes("cricket") || lowerQuery.includes("score")) {
    return "cricket";
  }
  if (lowerQuery.includes("bitcoin") || lowerQuery.includes("btc")) {
    return "bitcoin";
  }
  if (lowerQuery.includes("weather")) {
    return "weather";
  }
  if (lowerQuery.includes("news") || lowerQuery.includes("headline")) {
    return "news";
  }
  if (lowerQuery.includes("stock") || lowerQuery.includes("price")) {
    return "stocks";
  }
  
  return null;
}

/**
 * NewsAPI Search - Fetch top headlines using NewsAPI
 */
async function newsApiSearch(query?: string): Promise<ScrapingResult | null> {
  if (!NEWSAPI_KEY) {
    console.log("NewsAPI key not configured");
    return null;
  }

  try {
    const endpoint = query 
      ? `https://newsapi.org/v2/everything?q=${encodeURIComponent(query)}&apiKey=${NEWSAPI_KEY}&pageSize=5&sortBy=publishedAt`
      : `https://newsapi.org/v2/top-headlines?country=us&apiKey=${NEWSAPI_KEY}&pageSize=5`;

    const response = await axios.get(endpoint, { timeout: 15000 });
    const data = response.data;

    if (data.status !== "ok" || !data.articles || data.articles.length === 0) {
      return null;
    }

    const articles = data.articles.slice(0, 5);
    const formatted = articles.map((article: any, index: number) => {
      const source = article.source?.name || "Unknown";
      return `${index + 1}. ${article.title}\n   📰 ${source} | ${new Date(article.publishedAt).toLocaleDateString()}\n   🔗 ${article.url}`;
    });

    return {
      source: "newsapi",
      data: `📰 Latest News${query ? ` for "${query}"` : ""}:\n\n${formatted.join("\n\n")}`,
      isLive: true,
      url: "https://newsapi.org"
    };
  } catch (error) {
    console.error("NewsAPI error:", error);
    return null;
  }
}

/**
 * SerpAPI Search - Enhanced search results using Google via SerpAPI
 */
async function serpApiSearch(query: string): Promise<ScrapingResult | null> {
  if (!SERPAPI_KEY) {
    console.log("SerpAPI key not configured");
    return null;
  }

  try {
    const params = new URLSearchParams({
      engine: "google",
      q: query,
      api_key: SERPAPI_KEY,
      num: "5"
    });

    const response = await axios.get(
      `https://serpapi.com/search?${params.toString()}`,
      { timeout: 15000 }
    );

    const data = response.data;
    
    // Extract organic results
    const results = data.organic_results || [];
    
    if (results.length === 0) {
      return null;
    }

    // Format results
    const formatted = results.slice(0, 3).map((result: any, index: number) => {
      return `${index + 1}. ${result.title}\n   ${result.snippet || "No description available"}\n   🔗 ${result.link}`;
    });

    return {
      source: "serpapi",
      data: `🔍 Search Results for "${query}":\n\n${formatted.join("\n\n")}`,
      isLive: true,
      url: data.search_metadata?.google_url || "https://www.google.com"
    };
  } catch (error) {
    console.error("SerpAPI error:", error);
    return null;
  }
}

/**
 * Scrape cricket scores
 */
async function scrapeCricketScores(): Promise<ScrapingResult> {
  try {
    const response = await axios.get("https://www.cricbuzz.com/cricket-match/live-scores", {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      },
      timeout: 10000
    });
    
    const $ = cheerio.load(response.data);
    const matches: string[] = [];
    
    $(".cb-mtch-lst").each((_, elem) => {
      const title = $(elem).find(".cb-lv-scrs-col").text().trim();
      if (title) matches.push(title);
    });
    
    if (matches.length === 0) {
      // Try SerpAPI fallback
      const serpResult = await serpApiSearch("live cricket scores today");
      if (serpResult) {
        return { ...serpResult, source: "cricket (via SerpAPI)" };
      }
      
      return {
        source: "cricket",
        data: "No live cricket matches found at the moment.",
        isLive: true,
        url: "https://www.cricbuzz.com/cricket-match/live-scores"
      };
    }
    
    return {
      source: "cricket",
      data: `🏏 Live Cricket Scores:\n${matches.slice(0, 3).join("\n")}`,
      isLive: true,
      url: "https://www.cricbuzz.com/cricket-match/live-scores"
    };
  } catch (error) {
    console.error("Cricket scraping error:", error);
    
    // Try SerpAPI fallback
    const serpResult = await serpApiSearch("live cricket scores today");
    if (serpResult) {
      return { ...serpResult, source: "cricket (via SerpAPI)" };
    }
    
    return {
      source: "cricket",
      data: "I couldn't fetch live cricket scores right now. Please try again.",
      isLive: true
    };
  }
}

/**
 * Scrape Bitcoin price
 */
async function scrapeBitcoinPrice(): Promise<ScrapingResult> {
  try {
    // Using CoinGecko API (free, no key required for basic usage)
    const response = await axios.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
      { timeout: 10000 }
    );
    
    const data = response.data;
    const price = data.bitcoin.usd;
    const change = data.bitcoin.usd_24h_change;
    const changeEmoji = change >= 0 ? "📈" : "📉";
    
    return {
      source: "bitcoin",
      data: `₿ Bitcoin Price: $${price.toLocaleString()} USD\n${changeEmoji} 24h Change: ${change.toFixed(2)}%`,
      isLive: true,
      url: "https://coinmarketcap.com/currencies/bitcoin/"
    };
  } catch (error) {
    console.error("Bitcoin scraping error:", error);
    
    // Try SerpAPI fallback
    const serpResult = await serpApiSearch("bitcoin price usd today");
    if (serpResult) {
      return { ...serpResult, source: "bitcoin (via SerpAPI)" };
    }
    
    return {
      source: "bitcoin",
      data: "I couldn't fetch the current Bitcoin price right now. Please try again.",
      isLive: true
    };
  }
}

/**
 * Scrape news headlines
 */
async function scrapeNewsHeadlines(query?: string): Promise<ScrapingResult> {
  // Try NewsAPI first (primary source)
  const newsApiResult = await newsApiSearch(query);
  if (newsApiResult) {
    return newsApiResult;
  }

  // Try SerpAPI second
  if (SERPAPI_KEY) {
    const serpResult = await serpApiSearch(query || "latest news headlines today");
    if (serpResult) {
      return { ...serpResult, source: "news (via SerpAPI)" };
    }
  }

  // Fallback to RSS feeds
  try {
    const response = await axios.get("https://feeds.bbci.co.uk/news/rss.xml", {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      },
      timeout: 10000
    });
    
    const $ = cheerio.load(response.data, { xmlMode: true });
    const headlines: string[] = [];
    
    $("item").each((index, elem) => {
      if (index < 5) {
        const title = $(elem).find("title").text().trim();
        if (title) headlines.push(`${index + 1}. ${title}`);
      }
    });
    
    if (headlines.length === 0) {
      return {
        source: "news",
        data: "Could not fetch news headlines at the moment.",
        isLive: true,
        url: "https://www.bbc.com/news"
      };
    }
    
    return {
      source: "news",
      data: `📰 Top News Headlines:\n${headlines.join("\n")}`,
      isLive: true,
      url: "https://www.bbc.com/news"
    };
  } catch (error) {
    console.error("News scraping error:", error);
    
    return {
      source: "news",
      data: "I couldn't fetch the latest news right now. Please try again.",
      isLive: true
    };
  }
}

/**
 * Get weather (using a simple API approach)
 */
async function getWeather(location: string): Promise<ScrapingResult> {
  const openWeatherKey = process.env.OPENWEATHER_API_KEY;
  
  try {
    if (openWeatherKey) {
      // Use OpenWeatherMap API
      const response = await axios.get(
        `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(location)}&appid=${openWeatherKey}&units=metric`,
        { timeout: 10000 }
      );
      
      const data = response.data;
      const temp = data.main.temp;
      const condition = data.weather[0].description;
      const humidity = data.main.humidity;
      
      return {
        source: "weather",
        data: `🌤️ Weather in ${data.name}:\nTemperature: ${temp}°C\nCondition: ${condition}\nHumidity: ${humidity}%`,
        isLive: true,
        url: `https://openweathermap.org/city/${data.id}`
      };
    }
    
    // Try SerpAPI fallback
    const serpResult = await serpApiSearch(`weather ${location} today`);
    if (serpResult) {
      return { ...serpResult, source: "weather (via SerpAPI)" };
    }
    
    return {
      source: "weather",
      data: `🌤️ Weather for ${location}:\nPlease add OPENWEATHER_API_KEY to .env.local for accurate weather data.`,
      isLive: true
    };
  } catch (error) {
    console.error("Weather API error:", error);
    
    // Try SerpAPI fallback
    const serpResult = await serpApiSearch(`weather ${location} today`);
    if (serpResult) {
      return { ...serpResult, source: "weather (via SerpAPI)" };
    }
    
    return {
      source: "weather",
      data: "I couldn't fetch weather data right now. Please try again.",
      isLive: true
    };
  }
}

/**
 * Main scraping function
 */
export async function scrapeRealTimeData(query: string): Promise<ScrapingResult | null> {
  if (!requiresRealTimeData(query)) {
    return null;
  }
  
  const intent = extractQueryIntent(query);
  
  // If no specific intent but SerpAPI is available, do a general search
  if (!intent && SERPAPI_KEY) {
    const serpResult = await serpApiSearch(query);
    if (serpResult) {
      return serpResult;
    }
  }
  
  if (!intent) {
    return null;
  }
  
  switch (intent) {
    case "cricket":
      return await scrapeCricketScores();
    case "bitcoin":
      return await scrapeBitcoinPrice();
    case "news":
      return await scrapeNewsHeadlines(query);
    case "weather":
      // Extract location from query (simple approach)
      const locationMatch = query.match(/in\s+([a-zA-Z\s]+)/i);
      const location = locationMatch ? locationMatch[1].trim() : "London";
      return await getWeather(location);
    default:
      // For any other query, try SerpAPI if available
      if (SERPAPI_KEY) {
        return await serpApiSearch(query);
      }
      return null;
  }
}
