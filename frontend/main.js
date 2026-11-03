import { initVaultModals, DATA_SOURCES } from './vault.js';
import { appendMessage, showTypingIndicator, removeTypingIndicator, highlightTool } from './chat.js';

let currentSessionId = null; // Managed by the backend

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initVaultModals();
    initMainViews();
    buildDataSourcesStrip();
    buildToolStatusList();
    startClock();
    fetchTelemetry();
    fetchSessionStats();

    const chatHistory = document.getElementById("chat-history");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const themeBtn = document.getElementById("theme-toggle-btn");
    const quickCsvBtn = document.getElementById("btn-quick-csv");
    const quickAlertsBtn = document.getElementById("btn-quick-alerts");
    const chatFilterInput = document.getElementById("chat-filter-input");

    // Theme Toggle Listener
    if (themeBtn) {
        themeBtn.addEventListener("click", toggleTheme);
    }

    // Quick Action: CSV Vault
    if (quickCsvBtn) {
        quickCsvBtn.addEventListener("click", () => {
            const openCsvBtn = document.getElementById("open-database-btn");
            if (openCsvBtn) openCsvBtn.click();
        });
    }

    // Alerts Widget & Dropdown Interaction
    const alertsWidget = document.getElementById("alerts-widget");
    const alertsDropdown = document.getElementById("alerts-dropdown");
    if (alertsWidget && alertsDropdown && !alertsWidget.hasAttribute('data-click-bound')) {
        alertsWidget.addEventListener("click", (e) => {
            e.stopPropagation();
            const willOpen = alertsDropdown.classList.contains("hidden");
            if (willOpen) {
                alertsDropdown.classList.remove("hidden");
                alertsWidget.classList.add("dropdown-open");
            } else {
                alertsDropdown.classList.add("hidden");
                alertsWidget.classList.remove("dropdown-open");
            }
        });
        document.addEventListener("click", () => {
            alertsDropdown.classList.add("hidden");
            alertsWidget.classList.remove("dropdown-open");
        });
        alertsWidget.setAttribute('data-click-bound', 'true');
    }


    // Live Conversation Search Filter
    if (chatFilterInput) {
        chatFilterInput.addEventListener("input", () => {
            const q = chatFilterInput.value.trim().toLowerCase();
            const messages = document.querySelectorAll("#chat-history .message");
            messages.forEach(msg => {
                const text = msg.textContent.toLowerCase();
                if (!q || text.includes(q)) {
                    msg.style.display = "";
                } else {
                    msg.style.display = "none";
                }
            });
        });
    }

    function setInputState(enabled) {
        userInput.disabled = !enabled;
        sendBtn.disabled = !enabled;
    }

    // Expose fillInput globally for quick-tag onclick
    window.fillInput = function(text) {
        userInput.value = text;
        userInput.focus();
    };

    if (chatForm) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const message = userInput.value.trim();
            if (!message) return;

            appendMessage("user", message, null, null, null, chatHistory);
            userInput.value = "";
            userInput.focus();

            setInputState(false);
            resetToolStatusAll();
            const typingEl = showTypingIndicator(chatHistory);

            try {
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message, session_id: currentSessionId })
                });

                const data = await response.json();
                removeTypingIndicator(typingEl);

                // Persist session_id for conversational memory
                if (data.session_id) {
                    currentSessionId = data.session_id;
                }

                if (data.error) {
                    appendMessage("bot", `Error: ${data.error}`, null, null, null, chatHistory);
                } else {
                    const toolUsed = data.tool_used || "general";
                    const reply = data.reply || "No response generated.";
                    const plan = data.plan || null;
                    const toolResults = data.tool_results || null;
                    appendMessage("bot", reply, toolUsed, plan, toolResults, chatHistory);

                    // Update dashboard panels
                    updateToolStatus(toolUsed, data.tools_used || []);
                    updateMapDisplay(data);
                    updateDataResults(data);

                    highlightTool(toolUsed);
                    if (data.tools_used && data.tools_used.length > 1) {
                        data.tools_used.forEach(t => highlightTool(t));
                    }
                    fetchSessionStats();
                }
            } catch (err) {
                removeTypingIndicator(typingEl);
                appendMessage("bot", `Connection Error: Could not reach the backend server.`, null, null, null, chatHistory);
            }

            setInputState(true);
        });
    }
});

/* ===== THEME CONTROLLER ===== */
function initTheme() {
    const savedTheme = localStorage.getItem("muni_theme") || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    const icon = document.getElementById("theme-icon");
    if (theme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        if (icon) icon.textContent = "☀️";
    } else {
        document.documentElement.removeAttribute("data-theme");
        if (icon) icon.textContent = "🌙";
    }
}

window.toggleTheme = function() {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const newTheme = isDark ? "light" : "dark";
    localStorage.setItem("muni_theme", newTheme);
    applyTheme(newTheme);
};

/* ===== VIEW SWITCHER (CHAT VS SPATIAL MAP) ===== */
function initMainViews() {
    const savedView = localStorage.getItem("muni_active_view") || "chat";
    switchMainView(savedView);
}

export function switchMainView(viewName) {
    const chatTab = document.getElementById("nav-tab-chat");
    const mapTab = document.getElementById("nav-tab-map");
    const chatView = document.getElementById("view-chat");
    const mapView = document.getElementById("view-map");

    if (viewName === "map") {
        if (chatView) chatView.style.display = "none";
        if (mapView) mapView.style.display = "flex";
        if (chatTab) chatTab.classList.remove("active");
        if (mapTab) mapTab.classList.add("active");
        localStorage.setItem("muni_active_view", "map");
        
        // Trigger resize on iframe for optimal rendering
        const iframe = document.getElementById("default-map-iframe");
        if (iframe && iframe.contentWindow) {
            try {
                iframe.contentWindow.dispatchEvent(new Event('resize'));
            } catch (e) {}
        }
    } else {
        if (chatView) chatView.style.display = "flex";
        if (mapView) mapView.style.display = "none";
        if (chatTab) chatTab.classList.add("active");
        if (mapTab) mapTab.classList.remove("active");
        localStorage.setItem("muni_active_view", "chat");
        
        const input = document.getElementById("user-input");
        if (input) input.focus();
    }
}
window.switchMainView = switchMainView;

/* ===== CLOCK ===== */
function startClock() {
    const el = document.getElementById("header-clock");
    if (!el) return;
    function tick() {
        const now = new Date();
        el.textContent = now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }
    tick();
    setInterval(tick, 1000);
}

/* ===== DATA SOURCES STRIP ===== */
function buildDataSourcesStrip() {
    const container = document.getElementById("data-sources-list");
    if (!container) return;

    container.style.display = "flex";
    container.style.gap = "6px";
    container.style.overflowX = "auto";
    container.style.flexShrink = "0";

    container.innerHTML = DATA_SOURCES.map(ds => `
        <div class="ds-pill" data-ds-id="${ds.id}">
            <span class="ds-pill-dot cat-dot-${ds.category}"></span>
            ${ds.title}
        </div>
    `).join("");
}

/* ===== TOOL STATUS LIST ===== */
const TOOL_NAMES = {
    aemet_forecast: "AEMET Forecast",
    aemet_warnings: "AEMET Warnings",
    aemet_marine: "AEMET Marine",
    aemet_fire_risk: "Fire Risk & UV",
    aemet_historical: "Climate Obs.",
    aemet_lightning: "Lightning",
    aemet_mountain: "Mountain",
    aemet_climatology: "Climatology",
    aemet_observations: "Observations",
    patricova_flood_risk: "PATRICOVA Flood",
    siscova_earthquakes: "SISCOVA Live",
    siscova_scraper: "SISCOVA Scraper",
    drive_list: "Drive List",
    drive_read: "Drive Reader",
    drive_read_sheet: "Drive Sheets",
    csv_list: "CSV Catalog",
    csv_reader: "CSV Parser",
    csv_aggregate: "CSV Aggregator",
    file_reader: "File Reader",
    vault_catalog: "Vault Catalog",
    vault_pdf_search: "PDF Search",
    web_search: "Web Search",
    tool_discover: "Tool Discovery",
    vault_discover: "Vault Discovery",
    vision_map_analyzer: "Vision Analyzer",
    icv_wms_search: "ICV WMS Search",
    general: "General AI",
};

const TOOL_CATEGORIES = {
    aemet_forecast: "api", aemet_warnings: "api", aemet_marine: "api",
    aemet_fire_risk: "api", aemet_historical: "api", aemet_lightning: "api",
    aemet_mountain: "api", aemet_climatology: "api", aemet_observations: "api",
    patricova_flood_risk: "api", siscova_earthquakes: "api", siscova_scraper: "api",
    drive_list: "api", drive_read: "api", drive_read_sheet: "api",
    icv_wms_search: "api", vision_map_analyzer: "api",
    csv_list: "data", csv_reader: "data", csv_aggregate: "data",
    file_reader: "data", vault_catalog: "data", vault_pdf_search: "mcp",
    web_search: "api", tool_discover: "data", vault_discover: "data",
    general: "general",
};

function buildToolStatusList() {
    const list = document.getElementById("tool-status-list");
    if (!list) return;

    list.innerHTML = Object.entries(TOOL_NAMES).map(([id, name]) => {
        const cat = TOOL_CATEGORIES[id] || "general";
        return `
        <div class="tool-status-item" data-tool-name="${id}" id="ts-${id}">
            <span class="tool-status-dot cat-dot-${cat}"></span>
            <span class="tool-status-name">${name}</span>
            <span class="tool-status-tag tag-idle">IDLE</span>
        </div>`;
    }).join("");
}

function resetToolStatusAll() {
    document.querySelectorAll(".tool-status-item").forEach(el => {
        el.classList.remove("active");
        const tag = el.querySelector(".tool-status-tag");
        if (tag) {
            tag.className = "tool-status-tag tag-idle";
            tag.textContent = "IDLE";
        }
    });
}

function updateToolStatus(primary, allTools) {
    const used = new Set(allTools.length > 0 ? allTools : [primary]);
    used.forEach(toolId => {
        const el = document.getElementById(`ts-${toolId}`);
        if (el) {
            el.classList.add("active");
            const tag = el.querySelector(".tool-status-tag");
            if (tag) {
                tag.className = "tool-status-tag tag-used";
                tag.textContent = "USED";
            }
            // Scroll into view
            el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    });
}

/* ===== MAP DISPLAY ===== */

/** Extract a URL from a string that may be a bare URL or markdown image ![alt](url) */
function extractImageUrl(value) {
    if (!value || typeof value !== "string") return null;
    // Markdown image: ![alt](url)
    const mdMatch = value.match(/!\[[^\]]*\]\(([^)]+)\)/);
    if (mdMatch) return mdMatch[1];
    // Bare URL
    if (value.startsWith("http")) return value;
    return null;
}

function updateMapDisplay(data) {
    const mapDisplay = document.getElementById("map-display");
    const mapBadge = document.getElementById("map-badge");
    if (!mapDisplay) return;

    let imageUrl = null;

    if (data.tool_results && data.tool_results.length > 0) {
        for (const step of data.tool_results) {
            const r = step.result;
            // String result — could be a bare URL or markdown image
            if (typeof r === "string") {
                const url = extractImageUrl(r);
                if (url) { imageUrl = url; break; }
            }
            // Object result — check common URL fields
            if (typeof r === "object" && r !== null) {
                for (const key of ["map_url", "image_url", "url"]) {
                    if (r[key]) {
                        const url = extractImageUrl(r[key]);
                        if (url) { imageUrl = url; break; }
                    }
                }
                if (imageUrl) break;
            }
        }
    }

    // Fallback: try extracting any URL from the reply text
    if (!imageUrl && data.reply) {
        // Match markdown images first
        const mdMatch = data.reply.match(/!\[[^\]]*\]\((https?:\/\/[^)]+)\)/);
        if (mdMatch) {
            imageUrl = mdMatch[1];
        } else {
            // Match bare URLs with image extensions
            const urlMatch = data.reply.match(/https?:\/\/\S+\.(png|jpg|jpeg|gif|webp)/i);
            if (urlMatch) imageUrl = urlMatch[0];
        }
    }

    if (imageUrl) {
        mapDisplay.innerHTML = `<img src="${imageUrl}" alt="Cartografía Oficial PATRICOVA" loading="lazy" style="display:block; width:100%; height:100%; object-fit:cover; position:absolute; inset:0;" onerror="this.outerHTML='<div class=\\'map-empty-state\\'><div class=\\'map-empty-icon\\'>❌</div><p>Error al cargar la cartografía en vivo</p></div>'">`;
        if (mapBadge) {
            mapBadge.className = "dash-panel-badge badge-live";
            mapBadge.textContent = "PATRICOVA LIVE";
        }
    }
}

/* ===== DATA RESULTS ===== */
function updateDataResults(data) {
    const container = document.getElementById("data-results");
    const badge = document.getElementById("data-badge");
    if (!container) return;

    const payload = data.tool_results || data.tool_data;

    if (payload && (Array.isArray(payload) ? payload.length > 0 : Object.keys(payload).length > 0)) {
        container.innerHTML = `<pre>${JSON.stringify(payload, null, 2)}</pre>`;
        if (badge) {
            badge.className = "dash-panel-badge badge-live";
            badge.textContent = `${data.tools_used ? data.tools_used.length : 1} tool(s)`;
        }
    }
}

/* ===== PROVIDER TOGGLE & STATUS ===== */
window.toggleProviderMenu = function() {
    const menu = document.getElementById('provider-menu');
    if (menu.style.display === 'none' || !menu.style.display) {
        menu.style.display = 'flex';
        fetchProviderStatus();
    } else {
        menu.style.display = 'none';
    }
};

document.addEventListener('click', (e) => {
    const menu = document.getElementById('provider-menu');
    const chip = document.getElementById('provider-toggle-chip');
    if (menu && chip && !menu.contains(e.target) && !chip.contains(e.target)) {
        menu.style.display = 'none';
    }
});

window.selectProviderMode = async function(mode) {
    try {
        const res = await fetch('/api/providers/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode })
        });
        const data = await res.json();
        if (data.status === 'success') {
            await fetchProviderStatus();
            document.getElementById('provider-menu').style.display = 'none';
        }
    } catch (err) {
        console.error("Failed to select provider:", err);
    }
};

async function fetchProviderStatus() {
    try {
        const res = await fetch('/api/providers/status');
        const data = await res.json();
        
        // Update Subtexts
        const geminiSub = document.getElementById('status-gemini-sub');
        if (geminiSub) {
            geminiSub.textContent = data.gemini.available ? "✅ API Key Ready" : "❌ Missing Key";
        }
        const ollamaSub = document.getElementById('status-ollama-sub');
        if (ollamaSub) {
            ollamaSub.textContent = data.ollama.available 
                ? `✅ Ready (${data.ollama.models.length} models)` 
                : "❌ Not running locally";
        }
            
        // Update Options UI
        document.querySelectorAll('.provider-option').forEach(el => el.classList.remove('active'));
        const activeOpt = document.getElementById(`opt-${data.mode}`);
        if (activeOpt) activeOpt.classList.add('active');
        
        // Update Main Chip
        const chipText = document.getElementById('provider-status-text');
        const chipDot = document.getElementById('provider-status-dot');
        
        if (chipText && chipDot) {
            if (data.mode === 'gemini') {
                chipText.textContent = "☁️ Force: Gemini";
                chipDot.style.background = data.gemini.available ? "var(--success)" : "var(--error)";
            } else if (data.mode === 'ollama') {
                chipText.textContent = "💻 Force: Ollama";
                chipDot.style.background = data.ollama.available ? "var(--success)" : "var(--error)";
            } else {
                chipText.textContent = "⚡ Auto";
                chipDot.style.background = (data.gemini.available || data.ollama.available) ? "var(--success)" : "var(--error)";
            }
        }
    } catch (err) {
        console.error("Failed to fetch provider status:", err);
    }
}

// Initial fetch and poll every 15s
fetchProviderStatus();
setInterval(fetchProviderStatus, 15000);

// ==========================================
// TELEMETRY & STATS
// ==========================================
async function fetchTelemetry() {
    try {
        const res = await fetch('/api/dashboard/telemetry');
        const data = await res.json();
        
        // 1. Temperature
        const tempEl = document.getElementById("rt-temp");
        const tempVal = (data.weather && data.weather.temperature !== undefined) ? data.weather.temperature : data.temperature;
        if (tempEl && tempVal !== undefined && tempVal !== null) {
            tempEl.textContent = `${tempVal}°C`;
        }
        const conditionEl = document.getElementById("rt-condition");
        if (conditionEl && data.weather && data.weather.condition) {
            conditionEl.textContent = data.weather.condition;
        }
        
        // 2. UV Index
        const uvEl = document.getElementById("rt-uv");
        const uvRiskEl = document.getElementById("rt-uv-risk");
        if (uvEl && data.uv_index !== undefined && data.uv_index !== null) {
            const uvVal = parseInt(data.uv_index, 10);
            uvEl.textContent = isNaN(uvVal) ? data.uv_index : uvVal;
            if (uvVal >= 8) {
                uvEl.style.color = "var(--danger)";
                if (uvRiskEl) uvRiskEl.textContent = "Very High (Protection Required)";
            } else if (uvVal >= 6) {
                uvEl.style.color = "#f97316";
                if (uvRiskEl) uvRiskEl.textContent = "High Risk (Sunscreen Advised)";
            } else if (uvVal >= 3) {
                uvEl.style.color = "var(--warning)";
                if (uvRiskEl) uvRiskEl.textContent = "Moderate (AEMET OpenData)";
            } else {
                uvEl.style.color = "var(--success)";
                if (uvRiskEl) uvRiskEl.textContent = "Low Risk (Safe Exposure)";
            }
        }
        
        // 3. Alerts
        const alertsEl = document.getElementById("rt-alerts");
        const alertsDropdown = document.getElementById("alerts-dropdown-content");
        
        if (alertsEl && data.warnings !== undefined) {
            if (Array.isArray(data.warnings) && data.warnings.length > 0) {
                alertsEl.textContent = `${data.warnings.length} Active`;
                alertsEl.style.color = "var(--danger)";
                
                if (alertsDropdown) {
                    alertsDropdown.innerHTML = "";
                    data.warnings.slice(0, 6).forEach(warn => {
                        const level = warn.nivel || "Aviso";
                        const desc = warn.instruccion || warn.texto || "Active civil protection bulletin.";
                        const zone = warn.zona_meteo || warn.nombre_zona || "Comunitat Valenciana";
                        const lvlLower = level.toLowerCase();
                        const borderColor = lvlLower.includes('rojo') ? 'var(--danger)' : lvlLower.includes('naranja') ? 'var(--warning)' : 'var(--accent)';
                        const html = `
                            <div class="alert-item" style="border-left-color: ${borderColor}">
                                <div class="alert-item-title">${level.toUpperCase()} - ${zone}</div>
                                <div class="alert-item-desc">${desc.substring(0, 95)}...</div>
                            </div>
                        `;
                        alertsDropdown.innerHTML += html;
                    });
                }
            } else {
                alertsEl.textContent = "0 Active";
                alertsEl.style.color = "var(--success)";
                if (alertsDropdown) {
                    alertsDropdown.innerHTML = `<div class="alert-item"><div class="alert-item-title">All Clear</div><div class="alert-item-desc">No active weather warnings for Alicante or CV at this time.</div></div>`;
                }
            }
            
            // Dropdown Click Handler (Elevated to prevent clipping under other elements)
            const widget = document.getElementById("alerts-widget");
            const dropdown = document.getElementById("alerts-dropdown");
            if (widget && dropdown && !widget.hasAttribute('data-click-bound')) {
                widget.addEventListener("click", (e) => {
                    e.stopPropagation();
                    const willOpen = dropdown.classList.contains("hidden");
                    if (willOpen) {
                        dropdown.classList.remove("hidden");
                        widget.classList.add("dropdown-open");
                    } else {
                        dropdown.classList.add("hidden");
                        widget.classList.remove("dropdown-open");
                    }
                });
                document.addEventListener("click", () => {
                    dropdown.classList.add("hidden");
                    widget.classList.remove("dropdown-open");
                });
                widget.setAttribute('data-click-bound', 'true');
            }
        }
    } catch (err) {
        console.error("Telemetry fetch error:", err);
    }
}

async function fetchSessionStats() {
    try {
        const res = await fetch('/api/session-stats');
        const data = await res.json();
        const tokensEl = document.getElementById("rt-tokens");
        if (tokensEl && data.tokens_used !== undefined) {
            tokensEl.textContent = `${data.tokens_used.toLocaleString()} Tokens Used`;
        }
    } catch (err) {
        console.error("Session stats error:", err);
    }
}

// Start polling immediately and on recurring schedule
fetchTelemetry();
fetchSessionStats();
setInterval(fetchTelemetry, 60000); // 1 minute
setInterval(fetchSessionStats, 10000); // 10 seconds
