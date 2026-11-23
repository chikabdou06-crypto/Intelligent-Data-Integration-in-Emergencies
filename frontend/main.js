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

    // Expose fillInput & cycling judge-ready prompts globally for quick-tag onclick
    window.fillInput = function(text) {
        userInput.value = text;
        userInput.focus();
    };

    const QUICK_PROMPT_BANKS = {
        weather: [
            "Check the current weather forecast and active AEMET warnings in Alicante.",
            "Are there any severe weather or coastal storm alerts across the Comunitat Valenciana today, and what is the UV index?",
            "What is the current forest fire risk level and coastal marine forecast for Alicante?",
            "Compare today's weather forecast, temperature, and wind conditions between Alicante and València.",
            "Is there any rain or strong wind expected in San Vicente del Raspeig and Elche over the next 48 hours?",
            "Give me a complete meteorological situation report for Alicante: daily forecast, active CAP alerts, and wildfire danger."
        ],
        flood: [
            "What is the official PATRICOVA flood risk in Alzira and what self-protection measures should citizens take?",
            "Check the PATRICOVA flood hazard level in Paiporta and València, and explain the DANA flash-flood risk.",
            "Analyze the flood risk in Orihuela (Vega Baja) and check if there are any active AEMET weather warnings right now.",
            "What is the PATRICOVA flood risk in Alicante and what cartography layers are available in the ICV WMS catalog?",
            "Search the ICV WMS catalog for PATRICOVA flood hazard and DANA risk maps in the Comunitat Valenciana.",
            "Compare the flood hazard exposure of Cullera and Dénia and provide citizen evacuation guidance for ground-floor residents."
        ],
        csv: [
            "Show me the municipal employment and Social Security affiliation dataset for Alicante.",
            "Can you cross-reference the registered unemployment data with the education levels for the municipality of Elche?",
            "Show me the historical unemployment trend in Alicante from paro_2008_2025.csv and compare recent years.",
            "What are the historical seismic events recorded near Alicante and Alcoy in the PELSISCAV seismic catalog CSV?",
            "I am planning to move to San Vicente del Raspeig. What are the housing rental prices in Alicante and what is today's weather forecast?",
            "Query the municipal demographic indicators and average income data for Alicante/Alacant."
        ]
    };

    const QUICK_PROMPT_LABELS = {
        weather: "🌤️ Alicante Weather & Alerts",
        flood: "🌊 Flood Hazards",
        csv: "📊 CSV Records"
    };

    const quickPromptIndices = { weather: 0, flood: 0, csv: 0 };

    window.cycleQuickPrompt = function(category, el) {
        const bank = QUICK_PROMPT_BANKS[category];
        if (!bank || bank.length === 0) return;

        const idx = quickPromptIndices[category] % bank.length;
        const promptText = bank[idx];
        quickPromptIndices[category] = (idx + 1) % bank.length;

        userInput.value = promptText;
        userInput.focus();

        if (el) {
            const baseLabel = QUICK_PROMPT_LABELS[category] || category;
            el.innerHTML = `${baseLabel} <small class="tag-cycle-hint">(${idx + 1}/${bank.length}) ↻</small>`;
            el.classList.add("quick-tag-cycled");
            setTimeout(() => el.classList.remove("quick-tag-cycled"), 280);
        }
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
        
        initAemetMap();
        if (aemetLeafletMap) {
            setTimeout(() => aemetLeafletMap.invalidateSize(), 100);
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

/* ===== INTERACTIVE AEMET, FLOOD RISK & FOREST FIRE LEAFLET MAP ===== */
let aemetLeafletMap = null;
let aemetWarningsLayer = null;
let floodRiskLayer = null;
let fireRiskLayer = null;
let citiesLayer = null;
let searchedCityMarker = null;
let patricovaWmsLayer = null;
let currentViewerMode = "integrated"; // 'integrated' or 'gva'
let latestWarningsCache = [];

// Dynamic filter configuration for official ICV PATRICOVA layers
let patricovaSubLayerFilters = {
    high: true,   // Layers 4, 5, 6 (Peligrosidad 1, 2, 3)
    mod: true,    // Layers 7, 8, 9 (Peligrosidad 4, 5, 6)
    geo: true,    // Layer 10 (Peligrosidad Geomorfológica)
    cauces: true  // Layer 3 (Red de Cauces)
};

function getActivePatricovaLayersQuery() {
    let layers = [];
    if (patricovaSubLayerFilters.cauces) layers.push(3);
    if (patricovaSubLayerFilters.high) layers.push(4, 5, 6);
    if (patricovaSubLayerFilters.mod) layers.push(7, 8, 9);
    if (patricovaSubLayerFilters.geo) layers.push(10);
    return layers.length > 0 ? "show:" + layers.join(",") : "show:-1";
}

window.setMapViewerMode = function(mode) {
    currentViewerMode = mode;
    const btnIntegrated = document.getElementById("btn-mode-integrated");
    const btnGva = document.getElementById("btn-mode-gva-visor");
    const leafletContainer = document.getElementById("aemet-leaflet-map");
    const gvaWrapper = document.getElementById("gva-visor-wrapper");
    const gvaIframe = document.getElementById("gva-visor-iframe");
    const controlsBar = document.getElementById("map-controls-bar");
    const legend = document.getElementById("aemet-map-legend");

    if (mode === "gva") {
        if (btnIntegrated) btnIntegrated.classList.remove("active");
        if (btnGva) btnGva.classList.add("active");
        if (leafletContainer) leafletContainer.style.display = "none";
        if (gvaWrapper) gvaWrapper.style.display = "flex";
        if (gvaIframe) {
            const targetUrl = gvaIframe.getAttribute("data-src") || "https://visor.gva.es/visor/?capas=spa_icv_orde_patricova_peligrosidad_inun";
            if (!gvaIframe.getAttribute("src") || gvaIframe.getAttribute("src") === "about:blank") {
                gvaIframe.setAttribute("src", targetUrl);
            }
        }
        if (controlsBar) controlsBar.style.display = "none";
        if (legend) legend.style.display = "none";
    } else {
        if (btnIntegrated) btnIntegrated.classList.add("active");
        if (btnGva) btnGva.classList.remove("active");
        if (leafletContainer) leafletContainer.style.display = "block";
        if (gvaWrapper) gvaWrapper.style.display = "none";
        if (controlsBar) controlsBar.style.display = "flex";
        if (legend) legend.style.display = "block";
        initAemetMap();
        if (aemetLeafletMap) {
            setTimeout(() => aemetLeafletMap.invalidateSize(), 50);
        }
    }
};

window.reloadGvaVisorIframe = function() {
    const gvaIframe = document.getElementById("gva-visor-iframe");
    if (gvaIframe) {
        const targetUrl = gvaIframe.getAttribute("data-src") || "https://visor.gva.es/visor/?capas=spa_icv_orde_patricova_peligrosidad_inun";
        gvaIframe.setAttribute("src", targetUrl);
    }
};

window.updatePatricovaSubLayers = function() {
    const chkHigh = document.getElementById("chk-pat-high");
    const chkMod = document.getElementById("chk-pat-mod");
    const chkGeo = document.getElementById("chk-pat-geo");
    const chkCauces = document.getElementById("chk-pat-cauces");

    patricovaSubLayerFilters.high = chkHigh ? chkHigh.checked : true;
    patricovaSubLayerFilters.mod = chkMod ? chkMod.checked : true;
    patricovaSubLayerFilters.geo = chkGeo ? chkGeo.checked : true;
    patricovaSubLayerFilters.cauces = chkCauces ? chkCauces.checked : true;

    if (patricovaWmsLayer && aemetLeafletMap) {
        patricovaWmsLayer.setParams({
            layers: getActivePatricovaLayersQuery()
        });
    }
};

window.toggleExtraHazards = function(enabled) {
    if (!aemetLeafletMap) return;
    if (aemetWarningsLayer) {
        if (enabled) aemetLeafletMap.addLayer(aemetWarningsLayer);
        else aemetLeafletMap.removeLayer(aemetWarningsLayer);
    }
    if (fireRiskLayer) {
        if (enabled) aemetLeafletMap.addLayer(fireRiskLayer);
        else aemetLeafletMap.removeLayer(fireRiskLayer);
    }
};

const CV_ZONE_POLYGONS = {
    "litoral norte de alicante": [[38.88, -0.15], [38.90, 0.14], [38.73, 0.23], [38.53, -0.08], [38.50, -0.25], [38.72, -0.28]],
    "litoral sur de alicante": [[38.53, -0.08], [38.35, -0.35], [37.85, -0.75], [38.05, -0.98], [38.38, -0.72], [38.50, -0.25]],
    "interior de alicante": [[38.78, -0.95], [38.85, -0.30], [38.50, -0.25], [38.38, -0.72], [38.45, -1.02]],
    "litoral de valencia": [[39.75, -0.38], [39.75, -0.18], [39.25, -0.20], [39.25, -0.48]],
    "litoral norte de valencia": [[39.75, -0.38], [39.75, -0.18], [39.35, -0.22], [39.35, -0.48]],
    "litoral sur de valencia": [[39.35, -0.45], [39.35, -0.18], [38.88, -0.05], [38.88, -0.38]],
    "interior norte de valencia": [[40.05, -1.45], [40.00, -0.45], [39.45, -0.50], [39.45, -1.48]],
    "interior sur de valencia": [[39.45, -1.48], [39.45, -0.45], [38.80, -0.35], [38.85, -1.25]],
    "litoral norte de castellón": [[40.55, 0.15], [40.52, 0.52], [40.08, 0.25], [40.12, -0.02]],
    "litoral sur de castellón": [[40.12, -0.02], [40.08, 0.25], [39.75, -0.18], [39.75, -0.38]],
    "interior norte de castellón": [[40.78, -0.32], [40.75, 0.18], [40.30, 0.10], [40.25, -0.40], [40.55, -0.48]],
    "interior sur de castellón": [[40.25, -0.40], [40.30, 0.10], [39.80, -0.35], [39.85, -0.72]]
};

// Official PATRICOVA Flood Risk Basins & DANA Flash-Flood Corridors
const PATRICOVA_FLOOD_ZONES = [
    {
        name: "Ribera del Júcar Flood Basin (Alzira · Algemesí · Cullera)",
        level: "VERY HIGH (PATRICOVA Nivel 1)",
        type: "Fluvial & Geomorphological Floodplain",
        municipalities: "Alzira, Algemesí, Carcaixent, Sueca, Cullera",
        description: "Historic Júcar & Magro river overflow zone. Critical DANA flood risk requiring early evacuation of ground floors and underpasses.",
        coords: [[39.24, -0.52], [39.25, -0.22], [39.08, -0.20], [39.06, -0.55]]
    },
    {
        name: "L'Horta Sud & Barranco del Poyo (Paiporta · Catarroja · Torrent)",
        level: "EXTREME (PATRICOVA Nivel 1 - Flash Flood Ravine)",
        type: "Rambla / Flash-Flood Corridor (DANA)",
        municipalities: "Paiporta, Catarroja, Massanassa, Benetússer, Aldaia, Torrent, Chiva",
        description: "High-velocity ravine flash-flood basin fed by Chiva mountains. Rapid water rise during convective DANA storms.",
        coords: [[39.46, -0.58], [39.45, -0.35], [39.34, -0.34], [39.35, -0.60]]
    },
    {
        name: "Vega Baja del Segura Floodplain (Orihuela · Dolores · Rojales)",
        level: "VERY HIGH (PATRICOVA Nivel 1)",
        type: "Segura River Alluvial Floodplain",
        municipalities: "Orihuela, Almoradí, Dolores, Callosa de Segura, Rojales, Guardamar",
        description: "Low-gradient alluvial plain highly vulnerable to Segura river overflows and persistent DANA episodes (e.g. Sept 2019 DANA).",
        coords: [[38.20, -1.02], [38.20, -0.63], [38.02, -0.64], [38.02, -1.04]]
    },
    {
        name: "Alicante Urban Ramblas (Barranco de las Ovejas · San Gabriel · Playa San Juan)",
        level: "HIGH (PATRICOVA Nivel 2)",
        type: "Urban Ravine & Coastal Runoff Zone",
        municipalities: "Alicante/Alacant, San Vicente del Raspeig, Sant Joan d'Alacant",
        description: "Urban flash-flood hazard along Barranco de las Ovejas, Juncaret, Albufereta, and low-lying Playa de San Juan depression.",
        coords: [[38.41, -0.54], [38.41, -0.40], [38.31, -0.41], [38.31, -0.55]]
    },
    {
        name: "Marina Alta Alluvial Coast (Dénia · Girona River · Xàbia)",
        level: "HIGH (PATRICOVA Nivel 2)",
        type: "Coastal & River Mouth Flood Zone",
        municipalities: "Dénia, Ondara, Els Poblets, Verger, Xàbia/Jávea",
        description: "Girona and Gorgos river mouths combined with coastal storm-surge flooding.",
        coords: [[38.89, -0.05], [38.87, 0.19], [38.74, 0.21], [38.75, -0.06]]
    },
    {
        name: "Plana Baixa & Mijares Delta (Burriana · Nules · Vila-real)",
        level: "HIGH (PATRICOVA Nivel 2)",
        type: "Littoral & Fluvial Delta Flood Zone",
        municipalities: "Burriana, Nules, Moncofa, Vila-real, Almassora",
        description: "Low coastal marshland and Mijares/Belcaire stream overflow zone.",
        coords: [[39.98, -0.18], [39.97, -0.01], [39.77, -0.08], [39.79, -0.24]]
    }
];

// Official AEMET / PREVIFOC Forest Fire Hazard Zones
const FOREST_FIRE_ZONES = [
    {
        name: "Sierra de Mariola & Font Roja Massif (Alcoy · Cocentaina)",
        level: "HIGH / EXTREME (PREVIFOC Nivel 3)",
        type: "Mediterranean Pine & Holm Oak Forest Massif",
        municipalities: "Alcoy/Alcoi, Cocentaina, Banyeres de Mariola, Ibi,Bocairent",
        description: "Dense protected forest park with steep topography and high fuel load. Strict fire ban during West/Poniente winds.",
        coords: [[38.80, -0.68], [38.80, -0.38], [38.62, -0.40], [38.62, -0.68]]
    },
    {
        name: "Vall d'Ebo & Marina Alta Mountains (Pego · Castell de Castells)",
        level: "EXTREME (PREVIFOC Nivel 3)",
        type: "Steep Mountain Scrub & Forest Zone",
        municipalities: "Vall d'Ebo, Pego, Vall de Gallinera, Castell de Castells, Callosa d'en Sarrià",
        description: "Recurrent major wildfire zone (e.g. 2022 Vall d'Ebo fire) with complex canyon winds and rural interface.",
        coords: [[38.86, -0.28], [38.86, -0.06], [38.66, -0.06], [38.66, -0.28]]
    },
    {
        name: "Sierras de Calderona & Espadán (Segorbe · Serra · Alcublas)",
        level: "HIGH (PREVIFOC Nivel 2-3)",
        type: "Cork Oak & Aleppine Pine Natural Parks",
        municipalities: "Segorbe, Altura, Serra, Náquera, Olocau, Eslida",
        description: "Continuous forested mountain corridor across southern Castellón and northern Valencia.",
        coords: [[40.00, -0.65], [40.00, -0.22], [39.65, -0.28], [39.66, -0.68]]
    },
    {
        name: "Macizo del Caroig & Interior Requena-Utiel (Requena · Ayora · Cofrentes)",
        level: "HIGH / EXTREME (PREVIFOC Nivel 3)",
        type: "Continental Forest Plateau & Canyon System",
        municipalities: "Requena, Utiel, Cofrentes, Cortes de Pallás, Ayora, Enguera",
        description: "Vast inland forest expanse vulnerable to summer dry-lightning storms and extreme heatwaves.",
        coords: [[39.58, -1.35], [39.58, -0.78], [38.95, -0.80], [38.95, -1.35]]
    },
    {
        name: "Alto Mijares & Tinença de Benifassà (Montanejos · Morella)",
        level: "HIGH (PREVIFOC Nivel 2-3)",
        type: "Mountain Forest & Ravine Ecosystem",
        municipalities: "Montanejos, Puebla de Arenoso, Morella, Vistabella del Maestrazgo",
        description: "High relief interior Castellón forest with critical Wildland-Urban Interface evacuation routes.",
        coords: [[40.68, -0.48], [40.68, 0.05], [40.08, -0.15], [40.08, -0.62]]
    }
];

const CV_MUNICIPALITIES = [
    { name: "Alicante", fullName: "Alicante / Alacant", lat: 38.3452, lon: -0.4815, floodRisk: "HIGH (Urban Ramblas & Coastal)", fireRisk: "MODERATE (Monte Benacantil / Orgegia)", summary: "Susceptible to intense DANA flash floods in San Gabriel, Barranco de las Ovejas & Playa de San Juan." },
    { name: "València", fullName: "València", lat: 39.4699, lon: -0.3763, floodRisk: "HIGH (Turia Southern Margin & L'Horta)", fireRisk: "HIGH (El Saler / Devesa Forest)", summary: "Metropolitan flood exposure along southern boundary and wildfire risk in Devesa de l'Albufera pine forest." },
    { name: "Castelló de la Plana", fullName: "Castelló de la Plana", lat: 39.9864, lon: -0.0513, floodRisk: "HIGH (Marjalería & Riu Sec)", fireRisk: "MODERATE (Desert de les Palmes)", summary: "Low-lying coastal Marjalería flood hazard and peri-urban wildfire risk in Desert de les Palmes." },
    { name: "Elche", fullName: "Elche / Elx", lat: 38.2699, lon: -0.7126, floodRisk: "MODERATE-HIGH (Vinalopó & Carrizales)", fireRisk: "MODERATE (Sierra del Molar)", summary: "Vinalopó ravine and southern agricultural basin flood risk during heavy autumn rainfall." },
    { name: "Alzira", fullName: "Alzira", lat: 39.1517, lon: -0.4400, floodRisk: "EXTREME (PATRICOVA Nivel 1 - Júcar)", fireRisk: "HIGH (Murta & Casella Valleys)", summary: "One of Spain's highest fluvial flood risk municipalities (Júcar river loop) plus forested mountain valleys." },
    { name: "Orihuela", fullName: "Orihuela", lat: 38.0848, lon: -0.9440, floodRisk: "EXTREME (PATRICOVA Nivel 1 - Segura)", fireRisk: "MODERATE (Sierra de Orihuela)", summary: "Critical Segura river floodplain (Vega Baja) and coastal rambla flash-flood exposure." },
    { name: "Paiporta", fullName: "Paiporta", lat: 39.4278, lon: -0.4167, floodRisk: "EXTREME (PATRICOVA Nivel 1 - Barranco del Poyo)", fireRisk: "LOW", summary: "Ground-zero flash-flood corridor intersected directly by the Rambla del Poyo ravine." },
    { name: "Catarroja", fullName: "Catarroja", lat: 39.4033, lon: -0.4028, floodRisk: "EXTREME (PATRICOVA Nivel 1 - Barranco del Poyo)", fireRisk: "LOW", summary: "High-risk alluvial flood basin between Rambla del Poyo and Albufera wetlands." },
    { name: "Torrent", fullName: "Torrent", lat: 39.4370, lon: -0.4654, floodRisk: "HIGH (Barranco del Poyo / l'Horteta)", fireRisk: "HIGH (El Vedat Forest)", summary: "Confluence of mountain ravines and dense El Vedat peri-urban pine forest." },
    { name: "Dénia", fullName: "Dénia", lat: 38.8408, lon: 0.1057, floodRisk: "HIGH (Girona & Alberca Lowlands)", fireRisk: "VERY HIGH (Montgó Natural Park)", summary: "Dual hazard: coastal/alluvial flooding in Les Marines and high WUI fire risk on Montgó slopes." },
    { name: "Alcoy", fullName: "Alcoy / Alcoi", lat: 38.6984, lon: -0.4735, floodRisk: "MODERATE (Serpis River Gorge)", fireRisk: "EXTREME (Sierra de Mariola & Font Roja)", summary: "Surrounded by protected Mediterranean forest massifs with very high summer wildfire risk." },
    { name: "San Vicente del Raspeig", fullName: "San Vicente del Raspeig", lat: 38.3964, lon: -0.5255, floodRisk: "MODERATE-HIGH (Rambuchar & Juncaret)", fireRisk: "MODERATE (Sabinar / Maigmó foothills)", summary: "Northern Alicante metropolitan ravine drainage feeding into urban flash-flood channels." },
    { name: "Torrevieja", fullName: "Torrevieja", lat: 37.9786, lon: -0.6823, floodRisk: "HIGH (Urban Endorheic Lagoon Basin)", fireRisk: "LOW-MODERATE", summary: "Heavy coastal storm surge and urban drainage flooding around the salt lagoons." },
    { name: "Benidorm", fullName: "Benidorm", lat: 38.5411, lon: -0.1225, floodRisk: "MODERATE-HIGH (Moralet & Derramador Ravines)", fireRisk: "HIGH (Serra Gelada & Finestrat)", summary: "High tourist density with steep mountain ravines and peri-urban pine forest." },
    { name: "Sagunto", fullName: "Sagunto / Sagunt", lat: 39.6796, lon: -0.2784, floodRisk: "HIGH (Palancia River Delta)", fireRisk: "HIGH (Sierra Calderona Eastern Flank)", summary: "Palancia river mouth flood zone and direct contact with Sierra Calderona forest." },
    { name: "Requena", fullName: "Requena", lat: 39.4883, lon: -1.1003, floodRisk: "MODERATE-HIGH (Magro River Headwaters)", fireRisk: "EXTREME (Interior Continental Forests)", summary: "Headwaters of the Magro river (DANA trigger) and extensive inland pine forests." },
    { name: "Cullera", fullName: "Cullera", lat: 39.1667, lon: -0.2528, floodRisk: "EXTREME (Júcar River Mouth & Coast)", fireRisk: "MODERATE (Muntanya de les Raboses)", summary: "Terminal discharge point of the Júcar river basin combined with coastal storm surges." }
];

function initAemetMap() {
    if (aemetLeafletMap || typeof L === "undefined") return;
    const container = document.getElementById("aemet-leaflet-map");
    if (!container) return;

    aemetLeafletMap = L.map("aemet-leaflet-map", {
        center: [39.30, -0.42], // Centered right on Valencia metropolitan & flood basin
        zoom: 9,
        zoomControl: true
    });

    // 1. Street Map Base
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; OpenStreetMap | ICV GVA PATRICOVA | AEMET'
    }).addTo(aemetLeafletMap);

    // 2. Official Transparent ICV GVA PATRICOVA Layer directly over real streets
    const ArcGISWms = L.TileLayer.extend({
        getTileUrl: function(coords) {
            const tileSize = this.options.tileSize;
            const nwPoint = coords.scaleBy(new L.Point(tileSize, tileSize));
            const sePoint = nwPoint.add(new L.Point(tileSize, tileSize));
            const nw = this._map.unproject(nwPoint, coords.z);
            const se = this._map.unproject(sePoint, coords.z);
            const layers = this.options.layers || "show:2,3,4,5,6,7,8,9,10,12";
            return "https://carto.icv.gva.es/arcgis/rest/services/tm_infraestructuras/ordenacion_territorial/MapServer/export" +
                `?bbox=${nw.lng},${se.lat},${se.lng},${nw.lat}&bboxSR=4326&imageSR=4326&size=${tileSize},${tileSize}&format=png32&transparent=true&layers=${layers}&f=image`;
        },
        setParams: function(params) {
            if (params.layers) this.options.layers = params.layers;
            this.redraw();
        }
    });

    patricovaWmsLayer = new ArcGISWms("", {
        tileSize: 512,
        opacity: 0.75,
        layers: getActivePatricovaLayersQuery(),
        attribution: "ICV GVA PATRICOVA"
    }).addTo(aemetLeafletMap);

    floodRiskLayer = L.layerGroup().addTo(aemetLeafletMap);
    fireRiskLayer = L.layerGroup().addTo(aemetLeafletMap);
    aemetWarningsLayer = L.layerGroup().addTo(aemetLeafletMap);
    citiesLayer = L.layerGroup().addTo(aemetLeafletMap);

    renderFloodAndFireZones();
    renderCityMarkers();
    initMapCitySearchInput();

    // Click anywhere on map to query official GVA PATRICOVA Identify API for that exact point
    aemetLeafletMap.on("click", async function(e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;
        const hintEl = document.getElementById("aemet-map-status-hint");
        if (hintEl) hintEl.textContent = `🌊 Querying official PATRICOVA for (${lat.toFixed(4)}, ${lon.toFixed(4)})...`;

        try {
            const identifyUrl = "https://carto.icv.gva.es/arcgis/rest/services/tm_infraestructuras/ordenacion_territorial/MapServer/identify" +
                `?f=json&geometry=${lon},${lat}&geometryType=esriGeometryPoint&sr=4326&layers=all:0,1,2,3,4,5,6,7,8,9,10,12&tolerance=10&mapExtent=${lon-0.05},${lat-0.05},${lon+0.05},${lat+0.05}&imageDisplay=800,600,96&returnGeometry=false`;
            const r = await fetch(identifyUrl);
            const data = await r.json();
            const results = data.results || [];
            let risks = [];
            results.forEach(res => {
                const attrs = res.attributes || {};
                const desc = attrs.leyenda || attrs.LEYENDA || attrs.DESCRIPCION || res.layerName;
                if (desc && !risks.includes(desc)) risks.push(desc);
            });

            const riskText = risks.length > 0 ? risks.join(", ") : "No direct flood risk detected at this specific point.";
            const popupHtml = `
                <div class="aemet-popup-card">
                    <div class="aemet-popup-header">
                        <span class="aemet-popup-badge" style="background:#7e22ce; color:#fff;">🌊 OFFICIAL PATRICOVA</span>
                    </div>
                    <div class="aemet-popup-zone">Point: ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E</div>
                    <div class="aemet-popup-desc"><strong>Identified Risk:</strong> ${riskText}</div>
                    <div class="aemet-popup-actions">
                        <button class="popup-action-btn popup-btn-flood" onclick="askAgentFromMap('Analyze the flood risk and civil protection guidance at coordinates ${lat.toFixed(4)}, ${lon.toFixed(4)}')">
                            💬 Ask AI Agent
                        </button>
                    </div>
                </div>
            `;
            L.popup().setLatLng([lat, lon]).setContent(popupHtml).openOn(aemetLeafletMap);
            if (hintEl) hintEl.textContent = `Point Risk: ${riskText.substring(0, 70)}`;
        } catch (err) {
            if (hintEl) hintEl.textContent = `Click query failed: ${err.message}`;
        }
    });

    if (latestWarningsCache.length > 0) {
        renderAemetWarningsOnMap(latestWarningsCache);
    }
}

function renderFloodAndFireZones() {
    if (!aemetLeafletMap || typeof L === "undefined") return;

    // 1. Render PATRICOVA Flood Risk Polygons (Blue dashed polygons)
    if (floodRiskLayer) {
        floodRiskLayer.clearLayers();
        PATRICOVA_FLOOD_ZONES.forEach(fz => {
            const poly = L.polygon(fz.coords, {
                color: "#0284c7",
                weight: 2,
                dashArray: "6, 4",
                fillColor: "#38bdf8",
                fillOpacity: 0.28
            });
            const popupHtml = `
                <div class="aemet-popup-card">
                    <div class="aemet-popup-header">
                        <span class="aemet-popup-badge" style="background:#0284c7; color:#fff;">🌊 FLOOD RISK · ${fz.level}</span>
                    </div>
                    <div class="aemet-popup-zone">${fz.name}</div>
                    <div class="aemet-popup-desc"><strong>Affected Municipalities:</strong> ${fz.municipalities}</div>
                    <div class="aemet-popup-sub">${fz.description}</div>
                    <div class="aemet-popup-actions">
                        <button class="popup-action-btn popup-btn-flood" onclick="askAgentFromMap('Check the PATRICOVA flood risk and evacuation protocol for ${fz.municipalities.split(',')[0].trim()}')">
                            🌊 Inspect PATRICOVA Flood Protocol
                        </button>
                    </div>
                </div>
            `;
            poly.bindPopup(popupHtml, { maxWidth: 320 });
            poly.bindTooltip(`🌊 Flood Risk Zone: ${fz.name} (${fz.level})`, { sticky: true });
            floodRiskLayer.addLayer(poly);
        });
    }

    // 2. Render Forest Fire Risk Polygons (Orange-Red dotted polygons)
    if (fireRiskLayer) {
        fireRiskLayer.clearLayers();
        FOREST_FIRE_ZONES.forEach(fire => {
            const poly = L.polygon(fire.coords, {
                color: "#ea580c",
                weight: 2,
                dashArray: "4, 4",
                fillColor: "#fb923c",
                fillOpacity: 0.26
            });
            const popupHtml = `
                <div class="aemet-popup-card">
                    <div class="aemet-popup-header">
                        <span class="aemet-popup-badge" style="background:#ea580c; color:#fff;">🔥 FOREST FIRE RISK · ${fire.level}</span>
                    </div>
                    <div class="aemet-popup-zone">${fire.name}</div>
                    <div class="aemet-popup-desc"><strong>Key Municipalities:</strong> ${fire.municipalities}</div>
                    <div class="aemet-popup-sub">${fire.description}</div>
                    <div class="aemet-popup-actions">
                        <button class="popup-action-btn" style="background:#ea580c;" onclick="askAgentFromMap('What is the forest fire risk today and wildfire emergency protocol for ${fire.municipalities.split(',')[0].trim()}?')">
                            🔥 Check Wildfire Risk &amp; Protocol
                        </button>
                    </div>
                </div>
            `;
            poly.bindPopup(popupHtml, { maxWidth: 320 });
            poly.bindTooltip(`🔥 Forest Fire Risk: ${fire.name} (${fire.level})`, { sticky: true });
            fireRiskLayer.addLayer(poly);
        });
    }
}

function buildCityPopupHtml(city) {
    const safeName = city.name.split("/")[0].trim();
    const floodColor = city.floodRisk.includes("EXTREME") || city.floodRisk.includes("HIGH") ? "#0284c7" : "#64748b";
    const fireColor = city.fireRisk.includes("EXTREME") || city.fireRisk.includes("HIGH") ? "#ea580c" : "#64748b";
    return `
        <div class="aemet-popup-card">
            <div class="aemet-popup-header">
                <span class="aemet-popup-badge badge-city">📍 MUNICIPALITY</span>
                <strong>${city.fullName || city.name}</strong>
            </div>
            <div class="aemet-popup-risk-pills">
                <div class="risk-pill" style="border-left: 3px solid ${floodColor};">
                    <strong>🌊 Flood Risk:</strong> ${city.floodRisk}
                </div>
                <div class="risk-pill" style="border-left: 3px solid ${fireColor};">
                    <strong>🔥 Forest Fire:</strong> ${city.fireRisk}
                </div>
            </div>
            <div class="aemet-popup-sub">${city.summary}</div>
            <div class="aemet-popup-actions">
                <button class="popup-action-btn popup-btn-flood" onclick="askAgentFromMap('Check the PATRICOVA flood risk in ${safeName}')">
                    🌊 Flood Check
                </button>
                <button class="popup-action-btn" style="background:#ea580c;" onclick="askAgentFromMap('What is the forest fire risk and weather forecast in ${safeName}?')">
                    🔥 Fire &amp; Weather
                </button>
            </div>
        </div>
    `;
}

function renderCityMarkers() {
    if (!citiesLayer || typeof L === "undefined") return;
    citiesLayer.clearLayers();

    CV_MUNICIPALITIES.forEach(city => {
        const isHighFlood = city.floodRisk.includes("EXTREME") || city.floodRisk.includes("HIGH");
        const isHighFire = city.fireRisk.includes("EXTREME") || city.fireRisk.includes("VERY HIGH");
        const fillColor = isHighFlood ? "#0284c7" : (isHighFire ? "#ea580c" : "#2563eb");

        const marker = L.circleMarker([city.lat, city.lon], {
            radius: 7,
            fillColor: fillColor,
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.95
        });

        marker.bindPopup(buildCityPopupHtml(city), { maxWidth: 320 });
        marker.bindTooltip(`📍 ${city.name} · 🌊 ${city.floodRisk.split(" ")[0]} · 🔥 ${city.fireRisk.split(" ")[0]}`, {
            direction: "top",
            offset: [0, -6]
        });
        citiesLayer.addLayer(marker);
    });
}

function initMapCitySearchInput() {
    const input = document.getElementById("map-city-search-input");
    const suggestionsEl = document.getElementById("map-search-suggestions");
    if (!input || !suggestionsEl || input.hasAttribute("data-bound")) return;
    input.setAttribute("data-bound", "true");

    input.addEventListener("input", () => {
        const q = input.value.trim().toLowerCase();
        if (!q) {
            suggestionsEl.classList.add("hidden");
            return;
        }
        const matches = CV_MUNICIPALITIES.filter(c =>
            c.name.toLowerCase().includes(q) || c.fullName.toLowerCase().includes(q)
        );
        if (matches.length === 0) {
            suggestionsEl.innerHTML = `
                <div class="map-suggestion-item" onclick="searchMapCity()">
                    <span>🔍 Search "<strong>${input.value.trim()}</strong>" via live geocoder &amp; check flood/fire risk</span>
                </div>
            `;
        } else {
            suggestionsEl.innerHTML = matches.map(c => `
                <div class="map-suggestion-item" onclick="selectSuggestedCity('${c.name.replace(/'/g, "\\'")}')">
                    <div><strong>📍 ${c.fullName}</strong></div>
                    <div class="map-suggestion-meta">🌊 Flood: ${c.floodRisk.split("(")[0].trim()} · 🔥 Fire: ${c.fireRisk.split("(")[0].trim()}</div>
                </div>
            `).join("");
        }
        suggestionsEl.classList.remove("hidden");
    });

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            suggestionsEl.classList.add("hidden");
            window.searchMapCity();
        }
    });

    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !suggestionsEl.contains(e.target)) {
            suggestionsEl.classList.add("hidden");
        }
    });
}

window.selectSuggestedCity = function(cityName) {
    const input = document.getElementById("map-city-search-input");
    const suggestionsEl = document.getElementById("map-search-suggestions");
    if (input) input.value = cityName;
    if (suggestionsEl) suggestionsEl.classList.add("hidden");
    window.searchMapCity();
};

function evaluatePointHazards(lat, lon) {
    // Check if coordinates fall inside any known PATRICOVA Flood Zone or Forest Fire Zone
    let floodStatus = "MODERATE (Local Urban Drainage / Check PATRICOVA Live)";
    let fireStatus = "MODERATE (Standard Mediterranean Scrub/Urban Interface)";

    for (const fz of PATRICOVA_FLOOD_ZONES) {
        const lats = fz.coords.map(c => c[0]);
        const lons = fz.coords.map(c => c[1]);
        if (lat >= Math.min(...lats) && lat <= Math.max(...lats) && lon >= Math.min(...lons) && lon <= Math.max(...lons)) {
            floodStatus = `${fz.level} — ${fz.name}`;
            break;
        }
    }
    for (const fire of FOREST_FIRE_ZONES) {
        const lats = fire.coords.map(c => c[0]);
        const lons = fire.coords.map(c => c[1]);
        if (lat >= Math.min(...lats) && lat <= Math.max(...lats) && lon >= Math.min(...lons) && lon <= Math.max(...lons)) {
            fireStatus = `${fire.level} — ${fire.name}`;
            break;
        }
    }
    return { floodStatus, fireStatus };
}

window.searchMapCity = async function() {
    closeToolMapOverlay();
    initAemetMap();
    const input = document.getElementById("map-city-search-input");
    const suggestionsEl = document.getElementById("map-search-suggestions");
    if (suggestionsEl) suggestionsEl.classList.add("hidden");
    if (!input || !aemetLeafletMap) return;

    const query = input.value.trim();
    if (!query) return;

    // 1. Check local known CV municipalities first
    const qLower = query.toLowerCase();
    const known = CV_MUNICIPALITIES.find(c =>
        c.name.toLowerCase() === qLower ||
        c.fullName.toLowerCase().includes(qLower) ||
        c.name.toLowerCase().includes(qLower)
    );

    if (known) {
        aemetLeafletMap.flyTo([known.lat, known.lon], 12, { duration: 0.8 });
        if (citiesLayer) {
            citiesLayer.eachLayer(layer => {
                if (layer.getLatLng && Math.abs(layer.getLatLng().lat - known.lat) < 0.01 && Math.abs(layer.getLatLng().lng - known.lon) < 0.01) {
                    layer.openPopup();
                }
            });
        }
        return;
    }

    // 2. Otherwise geocode any town/city via OpenStreetMap Nominatim
    const hintEl = document.getElementById("aemet-map-status-hint");
    if (hintEl) hintEl.textContent = `🔍 Locating "${query}"...`;

    try {
        const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query + ", España")}&format=json&limit=1`;
        const res = await fetch(url);
        const geo = await res.json();
        if (geo && geo.length > 0) {
            const lat = parseFloat(geo[0].lat);
            const lon = parseFloat(geo[0].lon);
            const displayName = geo[0].display_name.split(",")[0];
            const hazards = evaluatePointHazards(lat, lon);

            if (searchedCityMarker) {
                aemetLeafletMap.removeLayer(searchedCityMarker);
            }

            const customCity = {
                name: displayName,
                fullName: displayName,
                lat: lat,
                lon: lon,
                floodRisk: hazards.floodStatus,
                fireRisk: hazards.fireStatus,
                summary: `Located at ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E. Click below to run a live PATRICOVA flood or AEMET wildfire/weather check.`
            };

            searchedCityMarker = L.circleMarker([lat, lon], {
                radius: 9,
                fillColor: "#7c3aed",
                color: "#ffffff",
                weight: 2.5,
                opacity: 1,
                fillOpacity: 0.95
            }).addTo(aemetLeafletMap);

            searchedCityMarker.bindPopup(buildCityPopupHtml(customCity), { maxWidth: 320 });
            aemetLeafletMap.flyTo([lat, lon], 12, { duration: 0.8 });
            searchedCityMarker.openPopup();
            if (hintEl) hintEl.textContent = `📍 Located ${displayName} — showing Flood & Fire hazard profile`;
        } else {
            if (hintEl) hintEl.textContent = `⚠️ Could not find "${query}". Try another municipality name.`;
        }
    } catch (e) {
        if (hintEl) hintEl.textContent = `⚠️ Search failed: ${e.message}`;
    }
};

function getWarningColorStyle(levelStr) {
    const lvl = (levelStr || "").toLowerCase();
    if (lvl.includes("rojo") || lvl.includes("red") || lvl.includes("extreme")) {
        return { color: "#dc2626", fillColor: "#ef4444", label: "ROJO (Extreme)" };
    }
    if (lvl.includes("naranja") || lvl.includes("orange") || lvl.includes("severe")) {
        return { color: "#d97706", fillColor: "#f97316", label: "NARANJA (Severe)" };
    }
    return { color: "#ca8a04", fillColor: "#eab308", label: "AMARILLO (Moderate)" };
}

function renderAemetWarningsOnMap(warnings) {
    latestWarningsCache = Array.isArray(warnings) ? warnings : [];
    const hintEl = document.getElementById("aemet-map-status-hint");
    const mapBadge = document.getElementById("map-badge");

    if (!aemetLeafletMap) {
        initAemetMap();
    }
    if (!aemetWarningsLayer || typeof L === "undefined") return;

    aemetWarningsLayer.clearLayers();

    if (latestWarningsCache.length === 0) {
        if (hintEl) hintEl.textContent = "🌊 Flood & 🔥 Fire Risk zones active · 0 AEMET Weather Alerts";
        if (mapBadge) {
            mapBadge.className = "dash-panel-badge badge-active";
            mapBadge.textContent = "Flood & Fire Active";
        }
        return;
    }

    let drawnCount = 0;
    latestWarningsCache.forEach(warn => {
        const levelRaw = warn.nivel || warn.level || warn.severity || "Amarillo";
        const styleInfo = getWarningColorStyle(levelRaw);
        const zoneName = warn.zona_meteo || (Array.isArray(warn.affected_areas) ? warn.affected_areas.join(", ") : "") || "Comunitat Valenciana";
        const eventName = warn.event || "Meteorological Hazard";
        const headline = warn.headline || `${eventName} (${levelRaw})`;
        const desc = warn.description || warn.instruccion || "Follow civil protection guidance.";
        const onset = warn.onset ? warn.onset.replace("T", " ").substring(0, 16) : "Active";
        const expires = warn.expires ? warn.expires.replace("T", " ").substring(0, 16) : "Ongoing";

        let polyList = [];
        if (Array.isArray(warn.polygons) && warn.polygons.length > 0) {
            polyList = warn.polygons;
        } else {
            const zLower = zoneName.toLowerCase();
            for (const [key, coords] of Object.entries(CV_ZONE_POLYGONS)) {
                if (zLower.includes(key) || key.includes(zLower)) {
                    polyList.push(coords);
                }
            }
        }

        const popupHtml = `
            <div class="aemet-popup-card">
                <div class="aemet-popup-header">
                    <span class="aemet-popup-badge" style="background:${styleInfo.fillColor}; color:#fff;">⚠️ ${styleInfo.label}</span>
                    <strong>${eventName}</strong>
                </div>
                <div class="aemet-popup-zone">📍 ${zoneName}</div>
                <div class="aemet-popup-desc">${headline}</div>
                <div class="aemet-popup-sub">${desc}</div>
                <div class="aemet-popup-time">🕒 ${onset} &rarr; ${expires}</div>
                <div class="aemet-popup-actions">
                    <button class="popup-action-btn" onclick="askAgentFromMap('Give me emergency self-protection instructions for the ${eventName} alert in ${zoneName}')">
                        💬 Ask Agent for Guidance
                    </button>
                </div>
            </div>
        `;

        polyList.forEach(coords => {
            const poly = L.polygon(coords, {
                color: styleInfo.color,
                weight: 2.5,
                fillColor: styleInfo.fillColor,
                fillOpacity: 0.35
            });
            poly.bindPopup(popupHtml, { maxWidth: 320 });
            poly.bindTooltip(`⚠️ ${levelRaw.toUpperCase()}: ${eventName} (${zoneName})`, { sticky: true });
            aemetWarningsLayer.addLayer(poly);
            drawnCount++;
        });
    });

    if (hintEl) {
        hintEl.textContent = `⚠️ ${latestWarningsCache.length} AEMET alert(s) + 🌊 Flood & 🔥 Fire risk zones active`;
    }
    if (mapBadge) {
        mapBadge.className = "dash-panel-badge badge-live";
        mapBadge.textContent = `${latestWarningsCache.length} Alert(s) + Risks`;
    }
}

window.toggleMapLayer = function(layerName) {
    initAemetMap();
    if (!aemetLeafletMap) return;

    layerState[layerName] = !layerState[layerName];
    const btn = document.getElementById(`btn-layer-${layerName}`);
    if (btn) {
        btn.classList.toggle("active", layerState[layerName]);
    }

    if (layerName === "aemet" && aemetWarningsLayer) {
        if (layerState.aemet) aemetLeafletMap.addLayer(aemetWarningsLayer);
        else aemetLeafletMap.removeLayer(aemetWarningsLayer);
    } else if (layerName === "flood" && floodRiskLayer) {
        if (layerState.flood) aemetLeafletMap.addLayer(floodRiskLayer);
        else aemetLeafletMap.removeLayer(floodRiskLayer);
    } else if (layerName === "fire" && fireRiskLayer) {
        if (layerState.fire) aemetLeafletMap.addLayer(fireRiskLayer);
        else aemetLeafletMap.removeLayer(fireRiskLayer);
    }
};

window.resetAemetMapView = function() {
    closeToolMapOverlay();
    initAemetMap();
    if (!aemetLeafletMap) return;
    aemetLeafletMap.flyTo([39.15, -0.48], 8, { duration: 0.7 });
};

window.askAgentFromMap = function(queryText) {
    switchMainView("chat");
    const input = document.getElementById("user-input");
    const form = document.getElementById("chat-form");
    if (input && form) {
        input.value = queryText;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
    }
};

window.closeToolMapOverlay = function() {
    const overlay = document.getElementById("tool-map-overlay");
    if (overlay) overlay.classList.add("hidden");
};

/** Extract a URL from a string that may be a bare URL or markdown image ![alt](url) */
function extractImageUrl(value) {
    if (!value || typeof value !== "string") return null;
    const mdMatch = value.match(/!\[[^\]]*\]\(([^)]+)\)/);
    if (mdMatch) return mdMatch[1];
    if (value.startsWith("http")) return value;
    return null;
}

function updateMapDisplay(data) {
    const mapBadge = document.getElementById("map-badge");
    let imageUrl = null;
    let coords = null;

    if (data.tool_results && data.tool_results.length > 0) {
        for (const step of data.tool_results) {
            const r = step.result;
            if (typeof r === "string") {
                const url = extractImageUrl(r);
                if (url) { imageUrl = url; break; }
            }
            if (typeof r === "object" && r !== null) {
                if (r.coordinates && r.coordinates.lat && r.coordinates.lon) {
                    coords = r.coordinates;
                }
                if (Array.isArray(r.data) && step.tool === "aemet_warnings") {
                    renderAemetWarningsOnMap(r.data);
                }
                for (const key of ["map_url", "image_url", "url"]) {
                    if (r[key]) {
                        const url = extractImageUrl(r[key]);
                        if (url) { imageUrl = url; break; }
                    }
                }
            }
        }
    }

    // If tool returned coordinates (e.g. patricova_flood_risk), fly the interactive map there
    if (coords && aemetLeafletMap) {
        aemetLeafletMap.flyTo([coords.lat, coords.lon], 13, { duration: 0.8 });
    }

    if (!imageUrl && data.reply) {
        const mdMatch = data.reply.match(/!\[[^\]]*\]\((https?:\/\/[^)]+)\)/);
        if (mdMatch) {
            imageUrl = mdMatch[1];
        } else {
            const urlMatch = data.reply.match(/https?:\/\/\S+\.(png|jpg|jpeg|gif|webp)/i);
            if (urlMatch) imageUrl = urlMatch[0];
        }
    }

    if (imageUrl) {
        const overlay = document.getElementById("tool-map-overlay");
        const overlayImg = document.getElementById("tool-map-overlay-img");
        if (overlay && overlayImg) {
            overlayImg.src = imageUrl;
            overlay.classList.remove("hidden");
        }
        if (mapBadge) {
            mapBadge.className = "dash-panel-badge badge-live";
            mapBadge.textContent = "CARTOGRAPHY LIVE";
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
        
        // Update Main Chip to show the actual active LLM model
        const chipText = document.getElementById('provider-status-text');
        const chipDot = document.getElementById('provider-status-dot');
        const activeModelName = data.active_model || "Gemini 3.5 Flash";
        
        if (chipText && chipDot) {
            if (data.mode === 'ollama') {
                chipText.textContent = "Qwen 2.5 7B (Local)";
                chipDot.style.background = data.ollama.available ? "var(--success)" : "var(--error)";
            } else {
                chipText.textContent = activeModelName;
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
            renderAemetWarningsOnMap(data.warnings);
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
