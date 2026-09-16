"use strict";

/*
 * RiscoIA - script.js
 * -------------------------------------------------------------------------
 * Reformatado a partir da versão original (que estava com cada função em
 * uma única linha longa). O comportamento é o mesmo, só ficou mais fácil
 * de ler e dar manutenção. Funções utilitárias (getUsers, normalize, etc.)
 * agora moram em utils.js e são usadas via o objeto global `RiscoIA`.
 */

// ---------------------------------------------------------------------
// Autenticação
// ---------------------------------------------------------------------
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const switchAuth = document.getElementById("switchAuth");

if (loginForm) {
    const loginButton = document.getElementById("loginButton");
    const loginButtonText = document.getElementById("loginButtonText");
    const loginLoading = document.getElementById("loginLoading");

    // Se a pessoa caiu aqui porque a sessão expirou (ver checagem periódica
    // de RiscoIA.isSessionValid mais abaixo), avisa o motivo em vez de só
    // devolver para a tela de login sem explicação.
    if (new URLSearchParams(location.search).get("expired") === "1") {
        RiscoIA.showMessage(document.getElementById("loginMessage"), "Sua sessão expirou. Faça login novamente.", "error");
    }

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const identity = RiscoIA.normalize(document.getElementById("loginUsername")?.value);
        const password = document.getElementById("loginPassword")?.value || "";
        const msg = document.getElementById("loginMessage");

        if (!identity || !password) {
            RiscoIA.showMessage(msg, "Preencha e-mail/usuário e senha.", "error");
            return;
        }

        loginButton && (loginButton.disabled = true);
        loginButtonText?.classList.add("hidden");
        loginLoading?.classList.remove("hidden");

        // Pequeno atraso artificial só para dar a sensação de "autenticando".
        await new Promise((resolve) => setTimeout(resolve, 350));

        const users = RiscoIA.getUsers();
        const user = users.find((u) => u.username === identity || u.email === identity);
        const passwordOk = user && (
            user.passwordHash
                ? await RiscoIA.verifyPassword(password, user.passwordHash)
                // Compatibilidade com contas antigas (versões anteriores salvavam
                // a senha em texto puro). Ao logar com sucesso, migramos a conta
                // para hash e removemos o texto puro do localStorage.
                : user.password === password
        );

        if (!passwordOk) {
            loginButton && (loginButton.disabled = false);
            loginButtonText?.classList.remove("hidden");
            loginLoading?.classList.add("hidden");
            RiscoIA.showMessage(msg, "Usuário/e-mail ou senha incorretos.", "error");
            return;
        }

        if (!user.passwordHash) {
            user.passwordHash = await RiscoIA.hashPassword(password);
            delete user.password;
            RiscoIA.saveUsers(users);
        }

        RiscoIA.startSession(user);
        window.location.href = "index.html";
    });
}

if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const name = document.getElementById("registerName")?.value.trim();
        const email = RiscoIA.normalize(document.getElementById("registerEmail")?.value);
        const username = RiscoIA.normalize(document.getElementById("registerUsername")?.value);
        const password = document.getElementById("registerPassword")?.value || "";
        const confirm = document.getElementById("registerPasswordConfirm")?.value || "";
        const msg = document.getElementById("registerMessage");

        if (!name || name.length < 3) {
            return RiscoIA.showMessage(msg, "Digite seu nome completo.", "error");
        }
        if (!RiscoIA.isValidEmail(email)) {
            return RiscoIA.showMessage(msg, "Digite um e-mail válido.", "error");
        }
        if (username.length < 3) {
            return RiscoIA.showMessage(msg, "O usuário precisa ter pelo menos 3 caracteres.", "error");
        }
        if (password.length < 6) {
            return RiscoIA.showMessage(msg, "A senha precisa ter pelo menos 6 caracteres.", "error");
        }
        if (password !== confirm) {
            return RiscoIA.showMessage(msg, "As senhas não coincidem.", "error");
        }

        const users = RiscoIA.getUsers();
        if (users.some((u) => u.username === username || u.email === email)) {
            return RiscoIA.showMessage(msg, "Este usuário ou e-mail já está cadastrado.", "error");
        }

        const user = {
            id: RiscoIA.generateId(),
            name,
            email,
            username,
            passwordHash: await RiscoIA.hashPassword(password),
            createdAt: new Date().toISOString()
        };

        users.push(user);
        RiscoIA.saveUsers(users);
        RiscoIA.showMessage(msg, "Cadastro realizado! Entrando no sistema...", "success");
        setTimeout(() => {
            RiscoIA.startSession(user);
            window.location.href = "index.html";
        }, 500);
    });
}

if (switchAuth) {
    const showLogin = () => {
        loginForm?.classList.remove("hidden");
        registerForm?.classList.add("hidden");
        const title = document.getElementById("formTitle");
        const subtitle = document.getElementById("formSubtitle");
        title && (title.textContent = "Acesse o sistema");
        subtitle && (subtitle.textContent = "Entre para visualizar o mapa de risco e as análises de sinistros de trânsito.");
    };
    const showRegister = () => {
        loginForm?.classList.add("hidden");
        registerForm?.classList.remove("hidden");
        const title = document.getElementById("formTitle");
        const subtitle = document.getElementById("formSubtitle");
        title && (title.textContent = "Criar sua conta");
        subtitle && (subtitle.textContent = "Cadastre seus dados para acessar o sistema de análise de risco.");
    };
    switchAuth.addEventListener("click", () => {
        loginForm?.classList.contains("hidden") ? showLogin() : showRegister();
    });
}
// OBS: o toggle de mostrar/ocultar senha (.password-toggle) é tratado apenas em
// enhancements.js, que é carregado em todas as páginas com campos de senha.
// Duplicar aqui fazia o campo alternar de tipo duas vezes por clique (um
// listener desfazendo o outro).

// ---------------------------------------------------------------------
// Proteção das páginas internas (agora respeitando expiração de sessão)
// ---------------------------------------------------------------------
const isLoginPage = location.pathname.endsWith("/login.html") || location.pathname.endsWith("/forgot-password.html");
const isProtectedPage = Boolean(document.getElementById("logoutButton") || document.getElementById("predictionForm"));

if (!isLoginPage && isProtectedPage && !RiscoIA.isSessionValid()) {
    RiscoIA.clearSession();
    window.location.replace("login.html");
}

if (!isLoginPage && isProtectedPage) {
    // Confere periodicamente se a sessão expirou enquanto a pessoa navega
    // (antes o token nunca expirava, então isso nunca era checado).
    setInterval(() => {
        if (!RiscoIA.isSessionValid()) {
            RiscoIA.clearSession();
            window.location.replace("login.html?expired=1");
        }
    }, 60000);
}

document.getElementById("logoutButton")?.addEventListener("click", () => {
    RiscoIA.clearSession();
    window.location.href = "login.html";
});

// Usuário (nome + @usuário, consistente em todas as páginas internas)
(() => {
    const user = RiscoIA.getSessionUser();
    const nameEl = document.getElementById("navUserName");
    if (nameEl && user) {
        nameEl.textContent = user.name + (user.username ? " • @" + user.username : "");
    }
    if (user) {
        document.title = "RiscoIA | " + user.name;
    }
})();

// Menu mobile
const mobileMenu = document.getElementById("mobileMenu");
mobileMenu?.addEventListener("click", () => {
    document.querySelector(".nav-menu")?.classList.toggle("mobile-open");
});

// ---------------------------------------------------------------------
// Mapa Leaflet com zonas e filtros
// ---------------------------------------------------------------------
let riskMapInstance = null;
let riskLayers = [];

// Dados demonstrativos. `via` e `horario` usam o MESMO vocabulário do
// formulário de predição (RiscoIA.VIA_OPTIONS / RiscoIA.HORARIO_OPTIONS),
// então o nome exibido em qualquer lugar do site vem sempre de
// RiscoIA.LABELS, e não pode mais ficar dessincronizado entre telas.
const zoneData = [
    { via: "francisco-junqueira", coords: [[-21.172, -47.820], [-21.168, -47.808], [-21.181, -47.804], [-21.185, -47.817]], risk: "alto", horario: "pico-noite", clima: "chuva", veiculo: "carro", prob: 85 },
    { via: "dom-pedro", coords: [[-21.185, -47.770], [-21.178, -47.758], [-21.192, -47.754], [-21.199, -47.768]], risk: "medio", horario: "pico-manha", clima: "sol", veiculo: "moto", prob: 62 },
    { via: "anhanguera", coords: [[-21.214, -47.870], [-21.207, -47.846], [-21.220, -47.841], [-21.229, -47.863]], risk: "alto", horario: "fora-pico", clima: "chuva", veiculo: "carro", prob: 78 },
    { via: "botanico", coords: [[-21.197, -47.832], [-21.190, -47.821], [-21.203, -47.814], [-21.210, -47.827]], risk: "baixo", horario: "fora-pico", clima: "sol", veiculo: "onibus", prob: 24 },
    { via: "centro", coords: [[-21.176, -47.816], [-21.168, -47.805], [-21.179, -47.799], [-21.188, -47.810]], risk: "medio", horario: "pico-manha", clima: "sol", veiculo: "moto", prob: 58 }
];

const riskColors = { alto: "#ef4444", medio: "#f59e0b", baixo: "#22c55e" };

function currentMapFilters() {
    return {
        horario: document.getElementById("mapFilterHorario")?.value || "todos",
        clima: document.getElementById("mapFilterClima")?.value || "todos",
        veiculo: document.getElementById("mapFilterVeiculo")?.value || "todos"
    };
}

function renderRiskMap() {
    if (!riskMapInstance) return;
    riskLayers.forEach((l) => l.remove());
    riskLayers = [];

    const filters = currentMapFilters();
    zoneData.filter((z) => RiscoIA.zoneMatches(z, filters)).forEach((z) => {
        const name = RiscoIA.LABELS.via[z.via] || z.via;
        const layer = L.polygon(z.coords, {
            color: riskColors[z.risk],
            fillColor: riskColors[z.risk],
            fillOpacity: 0.38,
            weight: 2
        }).bindPopup(`<strong>${name}</strong><br>Risco: ${z.risk.toUpperCase()}<br>Probabilidade estimada: ${z.prob}%`);
        layer.addTo(riskMapInstance);
        riskLayers.push(layer);
    });
}

function initRiskMap() {
    const el = document.getElementById("riskMap");
    if (!el || typeof L === "undefined") return;

    const loadingEl = document.getElementById("mapLoadingState");
    if (loadingEl) loadingEl.hidden = false;

    riskMapInstance = L.map(el, { zoomControl: false }).setView([-21.1775, -47.8103], 12);

    const tileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors"
    }).addTo(riskMapInstance);

    // Estado de carregamento do mapa: os tiles do OpenStreetMap dependem de
    // uma requisição de rede que pode demorar ou falhar (bloqueio de rede,
    // sem internet). Antes não havia nenhum feedback visual disso.
    if (loadingEl) {
        tileLayer.on("load", () => { loadingEl.hidden = true; });
        tileLayer.on("tileerror", () => {
            loadingEl.textContent = "Não foi possível carregar os mapas (verifique sua conexão).";
        });
    }

    L.control.zoom({ position: "topright" }).addTo(riskMapInstance);
    renderRiskMap();

    ["mapFilterHorario", "mapFilterClima", "mapFilterVeiculo"].forEach((id) => {
        document.getElementById(id)?.addEventListener("change", renderRiskMap);
    });
}

// ---------------------------------------------------------------------
// Gráficos Chart.js - agora alimentados pelo histórico real de previsões
// (RiscoIA_prediction_history) quando ele existe, com um conjunto de
// dados demonstrativo como fallback enquanto não há nenhuma previsão salva.
// ---------------------------------------------------------------------
let periodChartInstance = null;
let roadsChartInstance = null;

const DEMO_PERIOD_DATA = { Manhã: 28, Tarde: 24, Noite: 38, Madrugada: 10 };
const DEMO_ROADS_DATA = zoneData.reduce((acc, z) => {
    acc[RiscoIA.LABELS.via[z.via] || z.via] = z.prob;
    return acc;
}, {});

function computeChartDataFromHistory(history) {
    if (!history || !history.length) return null;

    const periodCounts = { Manhã: 0, Tarde: 0, Noite: 0, Madrugada: 0 };
    const roadSums = {};

    history.forEach((item) => {
        const periodo = RiscoIA.periodoFromHorario(item.horario);
        if (periodo) periodCounts[periodo]++;

        const label = RiscoIA.LABELS.via[item.via] || item.via;
        if (!roadSums[label]) roadSums[label] = { n: 0, sum: 0 };
        roadSums[label].n++;
        roadSums[label].sum += item.probabilidade;
    });

    const roadsData = {};
    Object.entries(roadSums).forEach(([label, v]) => {
        roadsData[label] = Math.round(v.sum / v.n);
    });

    return { periodData: periodCounts, roadsData };
}

function initCharts() {
    if (typeof Chart === "undefined") return;

    const p = document.getElementById("periodChart");
    const r = document.getElementById("roadsChart");

    if (p) {
        periodChartInstance = new Chart(p, {
            type: "doughnut",
            data: {
                labels: Object.keys(DEMO_PERIOD_DATA),
                datasets: [{ data: Object.values(DEMO_PERIOD_DATA) }]
            },
            options: { responsive: true, plugins: { legend: { position: "bottom" } } }
        });
    }

    if (r) {
        roadsChartInstance = new Chart(r, {
            type: "bar",
            data: {
                labels: Object.keys(DEMO_ROADS_DATA),
                datasets: [{ label: "Incidência", data: Object.values(DEMO_ROADS_DATA) }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } }
        });
    }

    // Exposto para o módulo de histórico (enhancements.js) atualizar os
    // gráficos assim que houver previsões reais, sem repetir a lógica de
    // montagem do Chart.js.
    window.RiscoIACharts = {
        update(history) {
            const computed = computeChartDataFromHistory(history);
            const periodData = computed ? computed.periodData : DEMO_PERIOD_DATA;
            const roadsData = computed ? computed.roadsData : DEMO_ROADS_DATA;

            if (periodChartInstance) {
                periodChartInstance.data.labels = Object.keys(periodData);
                periodChartInstance.data.datasets[0].data = Object.values(periodData);
                periodChartInstance.update();
            }
            if (roadsChartInstance) {
                roadsChartInstance.data.labels = Object.keys(roadsData);
                roadsChartInstance.data.datasets[0].data = Object.values(roadsData);
                roadsChartInstance.update();
            }
        }
    };
}

// ---------------------------------------------------------------------
// Predição com API + fallback demonstrativo
// ---------------------------------------------------------------------
function updateResult(prob, factors, meta) {
    const card = document.getElementById("predictionResult");
    const tag = document.getElementById("riskTag");
    const title = document.getElementById("riskTitle");
    const percent = document.getElementById("riskPercent");
    const meter = document.getElementById("riskMeter");
    const why = document.getElementById("riskFactors");
    if (!card) return;

    const level = RiscoIA.levelFromProb(prob);
    tag.textContent = level === "alto" ? "RISCO ELEVADO" : level === "medio" ? "RISCO MÉDIO" : "RISCO BAIXO";
    card.className = `result-card ${level}`;
    percent.textContent = `${prob}% de probabilidade de sinistro`;
    title.textContent = level === "alto" ? "Atenção recomendada" : level === "medio" ? "Atenção moderada" : "Condição de menor risco";
    why.textContent = factors;
    meter.style.width = prob + "%";
    card.hidden = false;

    // Em vez de um MutationObserver "espionando" o DOM para descobrir que
    // uma previsão aconteceu, disparamos um evento explícito com os dados -
    // enhancements.js escuta esse evento para salvar o histórico.
    document.dispatchEvent(new CustomEvent("riscoia:prediction", {
        detail: { probabilidade: prob, risco: level, ...meta }
    }));
}

async function handlePrediction(e) {
    e.preventDefault();

    const via = document.getElementById("predVia").value;
    const horario = document.getElementById("predHorario").value;
    const clima = document.getElementById("predClima").value;
    const dia = document.getElementById("predDia").value;

    const btn = document.getElementById("calculateRisk");
    const txt = document.getElementById("predictionButtonText");
    const spin = document.getElementById("predictionSpinner");
    const err = document.getElementById("predictionError");
    if (!via || !horario || !clima || !dia) return;

    err.hidden = true;
    btn.disabled = true;
    txt.textContent = "Analisando dados via IA...";
    spin?.classList.remove("hidden");

    try {
        const response = await fetch(`${RiscoIA.CONFIG.API_BASE_URL}/api/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ via, horario, clima, dia })
        });
        if (!response.ok) throw new Error("API indisponível");

        const result = await response.json();
        const prob = Math.round(Number(result.probabilidade ?? result.probability ?? result.risco ?? 0));
        updateResult(
            prob,
            result.fatores || result.factors || "Resultado retornado pelo modelo de IA.",
            { via, horario, clima, dia, origem: "API / modelo" }
        );
    } catch (error) {
        const prob = RiscoIA.calculateFallback({ via, horario, clima, dia });
        const climaTexto = clima === "chuva" ? "Chuva intensa" : "Condição climática favorável";
        const horarioTexto = (horario === "pico-manha" || horario === "pico-noite") ? "horário de pico" : "horário fora do pico";
        updateResult(
            prob,
            `Fator principal: ${climaTexto} + ${horarioTexto}. A API não respondeu, então foi exibida uma estimativa demonstrativa do frontend.`,
            { via, horario, clima, dia, origem: "Frontend demonstrativo" }
        );
        err.textContent = "Não foi possível conectar ao servidor de IA. Tente novamente mais tarde.";
        err.hidden = false;
    } finally {
        btn.disabled = false;
        txt.textContent = "Calcular Risco";
        spin?.classList.add("hidden");
    }
}

const predictionForm = document.getElementById("predictionForm");
if (predictionForm) {
    const selects = ["predVia", "predHorario", "predClima", "predDia"].map((id) => document.getElementById(id));
    const button = document.getElementById("calculateRisk");
    const validate = () => { button.disabled = !selects.every((s) => s && s.value); };
    selects.forEach((s) => s?.addEventListener("change", validate));
    validate();
    predictionForm.addEventListener("submit", handlePrediction);
}

// Botão "usar condições de agora": preenche horário e dia a partir do
// relógio do dispositivo e o clima a partir de uma consulta real à
// Open-Meteo (API pública, sem chave). Não deixa os sinistros do InfoSiga
// "em tempo real" (isso não existe, o InfoSiga só publica mensalmente),
// mas deixa a simulação usando as condições reais deste exato momento.
const liveConditionsButton = document.getElementById("useLiveConditions");
if (liveConditionsButton) {
    const liveText = document.getElementById("liveConditionsText");
    const liveSpinner = document.getElementById("liveConditionsSpinner");
    const err = document.getElementById("predictionError");

    liveConditionsButton.addEventListener("click", async () => {
        liveConditionsButton.disabled = true;
        liveSpinner?.classList.remove("hidden");
        err.hidden = true;

        const now = new Date();
        document.getElementById("predHorario").value = RiscoIA.horarioAtualBucket(now);
        document.getElementById("predDia").value = RiscoIA.diaAtualPtBR(now);

        try {
            document.getElementById("predClima").value = await RiscoIA.fetchLiveWeatherClima();
        } catch (error) {
            // Sem conexão com a Open-Meteo: mantém o preenchimento de
            // horário/dia (que não depende de rede) e avisa sobre o clima.
            err.textContent = "Não foi possível consultar o clima atual agora; horário e dia foram preenchidos, selecione o clima manualmente.";
            err.hidden = false;
        }

        ["predVia", "predHorario", "predClima", "predDia"].forEach((id) => {
            document.getElementById(id)?.dispatchEvent(new Event("change"));
        });
        // Se a via ainda não foi escolhida, o botão de calcular continua
        // desabilitado até a pessoa selecionar - de propósito, não escolhemos
        // uma via por ela.

        liveConditionsButton.disabled = false;
        liveSpinner?.classList.add("hidden");
    });
}

// ---------------------------------------------------------------------
// Widget "Risco agora" do dashboard: mesma ideia do botão acima, mas
// calculado para as 5 vias monitoradas de uma vez, com a heurística local
// (RiscoIA.calculateFallback) - sem chamar a API do modelo repetidamente
// só para popular um painel passivo do dashboard.
// ---------------------------------------------------------------------
async function renderLiveRisk() {
    const grid = document.getElementById("liveRiskGrid");
    const title = document.getElementById("liveRiskTitle");
    const badge = document.getElementById("liveRiskBadge");
    if (!grid) return;

    const now = new Date();
    const horario = RiscoIA.horarioAtualBucket(now);
    const dia = RiscoIA.diaAtualPtBR(now);
    let clima = "sol";
    let climaOrigem = "estimativa (sem conexão com a Open-Meteo)";
    try {
        clima = await RiscoIA.fetchLiveWeatherClima();
        climaOrigem = "Open-Meteo";
    } catch (error) {
        // Mantém o painel funcionando mesmo sem internet, só avisa a origem do dado de clima.
    }

    const resultados = zoneData
        .map((z) => ({
            via: RiscoIA.LABELS.via[z.via] || z.via,
            prob: RiscoIA.calculateFallback({ via: z.via, horario, clima, dia })
        }))
        .sort((a, b) => b.prob - a.prob);

    title.textContent = `${dia}, ${RiscoIA.LABELS.horario[horario]} · ${RiscoIA.LABELS.clima[clima]} (${climaOrigem})`;
    const piorNivel = RiscoIA.levelFromProb(resultados[0].prob);
    badge.textContent = "RISCO " + piorNivel.toUpperCase();
    badge.className = "smart-badge " + piorNivel;

    grid.innerHTML = resultados.map((r) => {
        const nivel = RiscoIA.levelFromProb(r.prob);
        return `<div class="live-risk-item ${nivel}"><span class="live-risk-via">${r.via}</span><span class="live-risk-value">${r.prob}%</span></div>`;
    }).join("");
}

document.getElementById("refreshLiveRisk")?.addEventListener("click", renderLiveRisk);

document.addEventListener("DOMContentLoaded", () => {
    initRiskMap();
    initCharts();
    renderLiveRisk();
});
