export function renderMarkdown(text) {
    if (!text) return "";

    let html = text;

    // Escape HTML entities first
    html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // Code blocks (```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre class="code-block"><code>${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // Bold (**text**)
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

    // Italic (*text*)
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");

    // Headers
    html = html.replace(/^### (.+)$/gm, '<h4 style="margin:10px 0 6px; font-size:14px;">$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3 style="margin:12px 0 8px; font-size:15px;">$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2 style="margin:14px 0 8px; font-size:16px;">$1</h2>');

    // Images: ![alt](url) — render inline images for maps/charts
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, url) => {
        return `<div class="inline-image-container">
            <img src="${url}" alt="${alt}" class="inline-image" loading="lazy" style="cursor: pointer;" onclick="window.open('${url}', '_blank')" onerror="this.outerHTML='<span class=\'image-error\'>[No se pudo cargar la cartografía en vivo]</span>'">
            <div class="image-caption">
                <span>🗺️ ${alt || 'Cartografía Oficial PATRICOVA'}</span>
                <a href="javascript:void(0)" onclick="if(window.switchMainView) window.switchMainView('map');" style="margin-left:auto; color:var(--primary); font-size:11px; text-decoration:none; font-weight:600;">Ver en Visor Espacial ↗</a>
            </div>
        </div>`;
    });

    // Clickable links: [text](url) — render as clickable <a> tags
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
        // Detect file type for special icons
        const lower = url.toLowerCase();
        let icon = '&#x1F517;'; // link icon
        if (lower.endsWith('.pdf')) icon = '&#x1F4C4;'; // PDF icon
        else if (lower.endsWith('.csv')) icon = '&#x1F4CA;'; // chart icon
        else if (lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg')) icon = '&#x1F5BC;'; // image icon
        return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="chat-link">${icon} ${text}</a>`;
    });

    // Auto-detect bare URLs (http/https) and make them clickable
    html = html.replace(/(^|\s)(https?:\/\/[^\s<]+)/g, (match, prefix, url) => {
        const lower = url.toLowerCase();
        // If it looks like an image URL, render as inline image
        if (lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg') || lower.endsWith('.gif') || lower.endsWith('.webp')) {
            return `${prefix}<div class="inline-image-container"><img src="${url}" alt="Image" class="inline-image" loading="lazy" onerror="this.outerHTML='<span class=\'image-error\'>[Image could not be loaded]</span>'"><div class="image-caption"><a href="${url}" target="_blank" class="chat-link">Open full size</a></div></div>`;
        }
        return `${prefix}<a href="${url}" target="_blank" rel="noopener noreferrer" class="chat-link">${url}</a>`;
    });

    // Unordered lists
    html = html.replace(/^- (.+)$/gm, '<li style="margin-left:16px; list-style:disc;">$1</li>');

    // Markdown tables: detect and convert
    html = convertMarkdownTables(html);

    // Line breaks
    html = html.replace(/\n/g, "<br>");

    // Clean up consecutive <br> tags
    html = html.replace(/(<br>\s*){3,}/g, "<br><br>");

    return html;
}

function convertMarkdownTables(text) {
    // Match markdown table blocks
    const tableRegex = /(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)/g;

    return text.replace(tableRegex, (match, headerRow, separatorRow, bodyRows) => {
        // Parse headers
        const headers = headerRow.split("|").filter(c => c.trim()).map(c => c.trim());

        // Parse body rows
        const rows = bodyRows.trim().split("\n").map(row =>
            row.split("|").filter(c => c.trim()).map(c => c.trim())
        );

        // Build HTML table
        let tableHtml = '<div class="inline-table-container"><table class="inline-table"><thead><tr>';
        headers.forEach(h => { tableHtml += `<th>${h}</th>`; });
        tableHtml += "</tr></thead><tbody>";

        rows.forEach(row => {
            tableHtml += "<tr>";
            row.forEach(cell => { tableHtml += `<td>${cell}</td>`; });
            tableHtml += "</tr>";
        });

        tableHtml += "</tbody></table></div>";
        return tableHtml;
    });
}
