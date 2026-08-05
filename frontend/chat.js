import { renderMarkdown } from './markdown.js';

const TOOL_LABELS = {
    aemet_forecast: "AEMET Municipal Forecast",
    aemet_warnings: "AEMET CAP Warnings",
    aemet_marine: "AEMET Marine Prediction",
    aemet_fire_risk: "AEMET Fire Risk & UV",
    aemet_historical: "AEMET Climate Observations",
    patricova_flood_risk: "PATRICOVA Flood Identify",
    siscova_earthquakes: "SISCOVA Live Earthquakes",
    siscova_scraper: "SISCOVA Station Scraper",
    drive_list: "Drive File List",
    drive_read: "Drive File Reader",
    drive_read_sheet: "Drive Sheet Reader",
    csv_list: "CSV Schema Catalog",
    csv_reader: "Dynamic CSV Parser",
    csv_aggregate: "CSV Aggregator",
    file_reader: "Vault File Reader",
    vault_catalog: "Vault Catalog",
    vault_pdf_search: "Vault PDF Search (Pinecone)",
    web_search: "Web Search",
    tool_discover: "Tool Discoverer",
    vault_discover: "Vault Discoverer",
    multi_tool: "Multi-Tool Plan",
    general: "General Reasoning",
};

function getToolCategoryClass(toolUsed) {
    const t = toolUsed.toLowerCase();
    if (["aemet_forecast", "aemet_warnings", "aemet_marine", "aemet_fire_risk", "aemet_historical", "patricova_flood_risk", "siscova_earthquakes", "siscova_scraper"].includes(t)) {
        return "api";
    }
    if (["csv_list", "csv_reader", "csv_aggregate", "file_reader", "vault_catalog", "vault_pdf_search", "tool_discover", "vault_discover"].includes(t)) {
        return "data";
    }
    return "general";
}

export function highlightTool(toolName) {
    const card = document.querySelector(`.tool-card[data-ds-id="${toolName}"]`) || document.querySelector(`.tool-card[data-tool-name="${toolName}"]`);
    if (card) {
        card.style.borderColor = "rgba(99, 102, 241, 0.5)";
        card.style.background = "rgba(99, 102, 241, 0.08)";
        setTimeout(() => {
            card.style.borderColor = "rgba(255, 255, 255, 0.06)";
            card.style.background = "rgba(255, 255, 255, 0.02)";
        }, 4000);
    }
}

export function appendMessage(sender, content, toolUsed, plan, toolResults, chatHistory) {
    const wrapper = document.createElement("div");
    wrapper.className = `message message-${sender === "user" ? "user" : "bot"}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    if (sender === "bot" && toolUsed && toolUsed !== "general") {
        const banner = document.createElement("div");
        banner.className = "tool-banner";
        const label = TOOL_LABELS[toolUsed] || toolUsed;
        banner.innerHTML = `<span class="tool-banner-dot cat-dot-${getToolCategoryClass(toolUsed)}"></span> Routed to: ${label}`;
        bubble.appendChild(banner);
    }

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.innerHTML = renderMarkdown(content);
    bubble.appendChild(contentDiv);

    if (sender === "bot" && toolUsed && toolUsed !== "general" && (plan || toolResults)) {
        const tracePanel = document.createElement("details");
        tracePanel.className = "agent-trace-panel";
        const summary = document.createElement("summary");
        summary.innerHTML = `<span class="trace-icon">⚙️</span> Agent Trace (Dev Console)`;
        
        const traceContent = document.createElement("div");
        traceContent.className = "trace-content";
        
        if (plan && plan.length > 0) {
            const planHeader = document.createElement("h4");
            planHeader.textContent = "1. Planner Output (JSON)";
            const prePlan = document.createElement("pre");
            prePlan.className = "trace-json";
            prePlan.textContent = JSON.stringify(plan, null, 2);
            traceContent.appendChild(planHeader);
            traceContent.appendChild(prePlan);
        }
        
        if (toolResults && toolResults.length > 0) {
            const resultsHeader = document.createElement("h4");
            resultsHeader.textContent = "2. Execution Trace to Synthesizer (JSON)";
            const preResults = document.createElement("pre");
            preResults.className = "trace-json";
            preResults.textContent = JSON.stringify(toolResults, null, 2);
            traceContent.appendChild(resultsHeader);
            traceContent.appendChild(preResults);
        }
        
        tracePanel.appendChild(summary);
        tracePanel.appendChild(traceContent);
        bubble.appendChild(tracePanel);
    }

    wrapper.appendChild(bubble);
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTo({ top: chatHistory.scrollHeight, behavior: "smooth" });
}

export function showTypingIndicator(chatHistory) {
    const wrapper = document.createElement("div");
    wrapper.className = "message message-bot";
    wrapper.id = "typing-indicator-wrapper";
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    const indicator = document.createElement("div");
    indicator.className = "typing-indicator";
    indicator.innerHTML = `<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>`;
    bubble.appendChild(indicator);
    wrapper.appendChild(bubble);
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTo({ top: chatHistory.scrollHeight, behavior: "smooth" });
    return wrapper;
}

export function removeTypingIndicator(el) {
    if (el && el.parentNode) {
        el.parentNode.removeChild(el);
    }
}
