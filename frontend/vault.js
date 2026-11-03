export const DATA_SOURCES = [
    {
        id: "aemet_forecast",
        title: "Previsión Meteorológica AEMET",
        shortDesc: "Pronóstico municipal diario/horario",
        type: "API en Vivo",
        origin: "AEMET OpenData (opendata.aemet.es)",
        description: "Consulta en tiempo real el pronóstico meteorológico municipal de la Agencia Estatal de Meteorología (AEMET). Proporciona temperatura máxima/mínima, probabilidad de precipitación, estado del cielo, y viento para los próximos 7 días en cualquier municipio de España.",
        category: "api"
    },
    {
        id: "aemet_warnings",
        title: "Avisos Meteorológicos AEMET",
        shortDesc: "Alertas CAP oficiales activas",
        type: "API en Vivo",
        origin: "AEMET OpenData (opendata.aemet.es)",
        description: "Recupera las alertas meteorológicas oficiales activas en formato CAP (Common Alerting Protocol). Incluye avisos por lluvia, viento, temperatura extrema, nevadas y tormentas con niveles de severidad (amarillo, naranja, rojo).",
        category: "api"
    },
    {
        id: "aemet_fire",
        title: "Riesgo de Incendio & UV AEMET",
        shortDesc: "Índice de riesgo forestal e índice UV",
        type: "API en Vivo",
        origin: "AEMET OpenData (opendata.aemet.es)",
        description: "Obtiene el índice diario de riesgo de incendio forestal y el índice de radiación ultravioleta (UV) por provincia, directamente desde AEMET.",
        category: "api"
    },
    {
        id: "siscova_live",
        title: "Terremotos en Vivo (SISCOVA)",
        shortDesc: "Telemetría sísmica en tiempo real",
        type: "API en Vivo",
        origin: "SISCOVA (Sismología CV)",
        description: "Obtiene los eventos sísmicos más recientes detectados por la red de estaciones sismológicas de la Comunitat Valenciana. Incluye magnitud, profundidad, coordenadas del epicentro y hora exacta del evento.",
        category: "api"
    },
    {
        id: "patricova",
        title: "PATRICOVA Riesgo Inundación",
        shortDesc: "Identificación de peligrosidad por coordenadas",
        type: "API en Vivo",
        origin: "GVA (gva.es WMS)",
        description: "Consulta el Plan de Acción Territorial sobre Prevención del Riesgo de Inundación en la Comunitat Valenciana (PATRICOVA). Dada una coordenada geográfica, identifica el nivel de peligrosidad (1-6) y periodo de retorno de inundación.",
        category: "api"
    },
    {
        id: "seismic_catalog",
        title: "Catálogo Sísmico Histórico",
        shortDesc: "PELSISCAV — Terremotos CV desde 1396",
        type: "CSV Local",
        origin: "pelsiscav_clean_seismic_catalog.csv (180 KB)",
        description: "Base de datos completa del catálogo sísmico histórico del Plan Especial frente al Riesgo Sísmico (PELSISCAV). Contiene fecha, hora, magnitud, intensidad, profundidad y localización de todos los terremotos registrados en la Comunitat Valenciana, con datos desde el año 1396.",
        category: "data"
    },
    {
        id: "flood_risk",
        title: "Riesgo de Inundaciones",
        shortDesc: "Mapeo de zonas inundables por municipio",
        type: "CSV Local",
        origin: "riesgo_inundaciones.csv (6 MB)",
        description: "Dataset geográfico que delimita las zonas con riesgo de inundación en la Comunitat Valenciana. Incluye polígonos de riesgo, niveles de peligrosidad, periodo de retorno y municipios afectados según la cartografía oficial PATRICOVA.",
        category: "data"
    },
    {
        id: "flood_hazard",
        title: "Peligrosidad de Inundación",
        shortDesc: "Clasificación de peligrosidad PATRICOVA",
        type: "CSV Local",
        origin: "peligrosidad_inun.csv (9 MB)",
        description: "Datos detallados de clasificación de peligrosidad de inundación según PATRICOVA. Incluye niveles de peligrosidad (1-6), profundidad de calado, frecuencia (periodos de retorno T25, T100, T500) y extensión geográfica de las zonas afectadas.",
        category: "data"
    },
    {
        id: "hydro_stations",
        title: "Estaciones Hidrológicas Júcar",
        shortDesc: "Red de estaciones de medición hídrica",
        type: "CSV Local",
        origin: "estaciones_hidrologicas_jucar.csv",
        description: "Ubicación y datos de la red de estaciones hidrológicas de la Confederación Hidrográfica del Júcar (CHJ). Incluye coordenadas, nombre de la estación, cuenca asociada y tipo de medición (aforo, pluviometría).",
        category: "data"
    },
    {
        id: "hydro_demarcaciones",
        title: "Demarcaciones Hidrográficas",
        shortDesc: "Cuencas y subcuencas de la CV",
        type: "CSV Local",
        origin: "demarcaciones_hidograficas.csv (874 KB)",
        description: "Delimitación territorial de las demarcaciones hidrográficas que afectan a la Comunitat Valenciana (Júcar, Segura, Ebro). Incluye datos de subcuencas, masas de agua y autoridades competentes.",
        category: "data"
    },
    {
        id: "emergency_docs",
        title: "Protocolos de Emergencia (PAM)",
        shortDesc: "Planes de actuación municipal vectorizados",
        type: "Búsqueda Semántica",
        origin: "Pinecone + PELSISCAV/PATRICOVA PDFs",
        description: "Búsqueda semántica sobre los documentos oficiales de protección civil: Plan de Actuación Municipal (PAM), protocolos de evacuación, directrices PELSISCAV para riesgo sísmico y documentación PATRICOVA para inundaciones. Permite encontrar procedimientos exactos por tipo de emergencia.",
        category: "mcp"
    },
    {
        id: "risk_summary",
        title: "Resumen de Riesgos CV",
        shortDesc: "Todos los riesgos por municipio",
        type: "PDF Vectorizado",
        origin: "RESUM RISCS CV.pdf (666 KB)",
        description: "Documento oficial de la Generalitat Valenciana que resume todos los riesgos naturales (inundación, sismicidad, incendio forestal, temporal marítimo) por municipio de la Comunitat Valenciana. Usado como referencia cruzada para validar análisis multi-riesgo.",
        category: "mcp"
    },
    {
        id: "drive_demographics",
        title: "Demografía San Vicente",
        shortDesc: "Población, sexo, edad, nacionalidad",
        type: "Google Drive CSV",
        origin: "poblacion_segun_sexo.csv + 8 archivos más",
        description: "Datos demográficos completos del municipio de San Vicente del Raspeig: población por sexo, por sección censal, por edad, por nacionalidad, por país de nacimiento, indicadores demográficos municipales, y padrón continuo histórico.",
        category: "api"
    },
    {
        id: "drive_economy",
        title: "Economía & Empleo",
        shortDesc: "Paro, contratos, afiliados, renta",
        type: "Google Drive CSV",
        origin: "paro_2008_2025.csv + contratos + afiliados",
        description: "Series temporales de empleo del municipio: paro registrado (2008-2025), contratos firmados (2006-2025), afiliados a la Seguridad Social (2022-2025), indicadores de renta por sección censal, distribución por fuente de ingresos y pensiones contributivas.",
        category: "api"
    },
    {
        id: "drive_catastro",
        title: "Catastro & Inmuebles",
        shortDesc: "Parcelas, construcciones, posiciones",
        type: "Google Drive CSV",
        origin: "Parcela_urbana.csv + Parcela_rustica.csv + más",
        description: "Información catastral completa: parcelas urbanas y rústicas, polígonos catastrales, datos de construcciones e inmuebles con geolocalización, número total de inmuebles, calles catastrales y posiciones de inmuebles de San Vicente del Raspeig.",
        category: "api"
    },
    {
        id: "drive_budget",
        title: "Presupuestos Municipales",
        shortDesc: "Previsiones y créditos iniciales",
        type: "Google Drive CSV",
        origin: "Prevision_inicales_presupuestos.csv + Creditos",
        description: "Presupuestos del Ayuntamiento de San Vicente del Raspeig: previsiones iniciales de ingresos, créditos iniciales de gastos y desglose por área de gasto presupuestario.",
        category: "api"
    },
    {
        id: "drive_security",
        title: "Criminalidad Municipal",
        shortDesc: "Delitos generales, robos, ciberdelincuencia",
        type: "Google Drive CSV",
        origin: "criminalidad_general.csv + 3 archivos más",
        description: "Estadísticas de criminalidad del municipio: criminalidad general, delitos convencionales (robos, hurtos), criminalidad sexual y ciberdelincuencia. Datos oficiales del Ministerio del Interior.",
        category: "api"
    }
];

export function initVaultModals() {
    const dsModal = document.getElementById("data-source-modal");
    const dsCloseModalBtn = document.getElementById("ds-close-modal-btn");
    const dsModalTitle = document.getElementById("ds-modal-title");
    const dsModalType = document.getElementById("ds-modal-type");
    const dsModalOrigin = document.getElementById("ds-modal-origin");
    const dsModalDesc = document.getElementById("ds-modal-desc");
    
    function openDataSourceModal(source) {
        dsModalTitle.textContent = source.title;
        dsModalType.textContent = source.type;
        dsModalOrigin.textContent = source.origin;
        dsModalDesc.textContent = source.description;
        dsModalType.className = `badge badge-type badge-${source.category}`;
        dsModal.classList.add("active");
    }

    if (dsCloseModalBtn) {
        dsCloseModalBtn.addEventListener("click", () => dsModal.classList.remove("active"));
    }
    if (dsModal) {
        dsModal.addEventListener("click", (e) => {
            if (e.target === dsModal) dsModal.classList.remove("active");
        });
    }

    // Use event delegation for data source clicks (pills or cards)
    document.addEventListener("click", (e) => {
        const pill = e.target.closest("[data-ds-id]");
        if (pill) {
            const id = pill.getAttribute("data-ds-id");
            const source = DATA_SOURCES.find(s => s.id === id);
            if (source) openDataSourceModal(source);
        }
    });

    // CSV Database Modal Logic
    const databaseModal = document.getElementById("database-modal");
    const openDatabaseBtn = document.getElementById("open-database-btn");
    const closeModalBtn = document.getElementById("close-modal-btn");
    const csvFileSelect = document.getElementById("csv-file-select");
    const csvSearchInput = document.getElementById("csv-search-input");

    if (openDatabaseBtn && databaseModal) {
        openDatabaseBtn.addEventListener("click", () => {
            databaseModal.classList.add("active");
            loadCsvData();
        });
    }
    if (closeModalBtn && databaseModal) {
        closeModalBtn.addEventListener("click", () => {
            databaseModal.classList.remove("active");
        });
    }
    if (databaseModal) {
        databaseModal.addEventListener("click", (e) => {
            if (e.target === databaseModal) {
                databaseModal.classList.remove("active");
            }
        });
    }
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && databaseModal && databaseModal.classList.contains("active")) {
            databaseModal.classList.remove("active");
        }
    });

    if (csvFileSelect) {
        csvFileSelect.addEventListener("change", () => loadCsvData(csvFileSelect.value));
    }

    if (csvSearchInput) {
        csvSearchInput.addEventListener("input", () => {
            filterCurrentCsvRows(csvSearchInput.value);
        });
    }
}

let _cachedHeaders = [];
let _cachedRows = [];

export function populateCsvFileSelect(csvList) {
    const csvFileSelect = document.getElementById("csv-file-select");
    if (!csvFileSelect || !csvList?.available_files) return;
    const files = Object.keys(csvList.available_files).sort();
    if (files.length === 0) return;
    csvFileSelect.innerHTML = files.map(f => `<option value="${f}">${f}</option>`).join("");
}

export function renderTable(headers, rows, note = "") {
    const headersRow = document.getElementById("table-headers");
    const bodyRows = document.getElementById("table-rows");
    const countBadge = document.getElementById("csv-row-badge");

    if (!headersRow || !bodyRows) return;

    headersRow.innerHTML = headers.map(h => `<th title="${h}">${h}</th>`).join("");

    if (rows.length === 0) {
        bodyRows.innerHTML = `<tr><td colspan="${headers.length || 1}" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching rows found.</td></tr>`;
        if (countBadge) countBadge.textContent = "0 rows";
        return;
    }

    if (countBadge) {
        countBadge.textContent = `${rows.length} rows`;
    }

    bodyRows.innerHTML = note + rows.map(row => {
        return "<tr>" + headers.map(h => {
            const val = row[h] !== undefined && row[h] !== null ? String(row[h]) : "";
            return `<td title="${val}">${val}</td>`;
        }).join("") + "</tr>";
    }).join("");
}

export function filterCurrentCsvRows(query) {
    if (!_cachedHeaders.length) return;
    const q = (query || "").trim().toLowerCase();
    if (!q) {
        renderTable(_cachedHeaders, _cachedRows);
        return;
    }

    const filtered = _cachedRows.filter(row => {
        return _cachedHeaders.some(h => {
            const val = row[h];
            return val !== undefined && val !== null && String(val).toLowerCase().includes(q);
        });
    });

    renderTable(_cachedHeaders, filtered);
}

export async function loadCsvData(selectedFile = "") {
    const csvFileSelect = document.getElementById("csv-file-select");
    const headersRow = document.getElementById("table-headers");
    const bodyRows = document.getElementById("table-rows");
    const countBadge = document.getElementById("csv-row-badge");
    const searchInput = document.getElementById("csv-search-input");

    if (searchInput) searchInput.value = "";
    if (countBadge) countBadge.textContent = "Loading...";

    if (!headersRow || !bodyRows) return;

    headersRow.innerHTML = "<th>Loading...</th>";
    bodyRows.innerHTML = "<tr><td style='padding:24px;text-align:center;'>Fetching dataset from backend vault...</td></tr>";

    const targetFile = selectedFile || (csvFileSelect ? csvFileSelect.value : "");
    const url = targetFile ? `/api/csv-data?file=${encodeURIComponent(targetFile)}` : "/api/csv-data";

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.csv_list) {
            populateCsvFileSelect(data.csv_list);
            if (csvFileSelect && data.selected_file) {
                csvFileSelect.value = data.selected_file;
            }
        }

        const csvData = data.default_data;

        if (!csvData || csvData.status !== "success") {
            bodyRows.innerHTML = `<tr><td style="color:var(--danger);padding:20px;">Error loading CSV: ${csvData?.message || "File unavailable"}</td></tr>`;
            if (countBadge) countBadge.textContent = "Error";
            return;
        }

        _cachedHeaders = csvData.headers || [];
        _cachedRows = csvData.data || [];

        let note = "";
        if (csvData.truncated) {
            note = `<tr class="csv-note-row"><td colspan="${_cachedHeaders.length}" style="background:var(--accent-subtle);color:var(--accent);font-weight:600;padding:8px 16px;">Previewing ${_cachedRows.length} of ${csvData.total_rows || _cachedRows.length} rows from dataset.</td></tr>`;
        }

        renderTable(_cachedHeaders, _cachedRows, note);

    } catch (err) {
        bodyRows.innerHTML = "<tr><td style='color:var(--danger);padding:24px;'>Failed to fetch CSV data. Is the backend server running?</td></tr>";
        if (countBadge) countBadge.textContent = "Offline";
    }
}
