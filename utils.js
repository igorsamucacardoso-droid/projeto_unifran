/*
 * RiscoIA - utils.js
 * -------------------------------------------------------------------------
 * Camada compartilhada usada por script.js e enhancements.js (e testável
 * isoladamente via Node, sem precisar de navegador/DOM).
 *
 * Por que este arquivo existe:
 * - Antes, script.js e enhancements.js tinham cópias duplicadas de
 *   getUsers/saveUsers/normalize/showMessage. Agora existe uma única versão.
 * - Antes, o mapa (script.js) e o formulário de predição usavam dois
 *   vocabulários diferentes para "horário" e "via" (ex.: mapa usava "pico",
 *   predição usava "pico-manha"/"pico-noite"). Agora as duas telas usam as
 *   mesmas listas (VIA_OPTIONS, HORARIO_OPTIONS, CLIMA_OPTIONS) definidas
 *   aqui, então não têm mais como ficar dessincronizadas.
 */
(function (root, factory) {
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.RiscoIA = factory();
    }
})(typeof window !== "undefined" ? window : globalThis, function () {
    "use strict";

    // ---------------------------------------------------------------------
    // Configuração
    // ---------------------------------------------------------------------
    // URL da API centralizada aqui: para apontar para outro backend (ou
    // ambiente de produção), troque só esta linha em vez de procurar por
    // "localhost" espalhado pelo código.
    const CONFIG = {
        API_BASE_URL: (typeof window !== "undefined" && window.RISCOIA_API_BASE_URL)
            || "http://localhost:3000",
        SESSION_DURATION_MS: 12 * 60 * 60 * 1000 // 12 horas
    };

    // ---------------------------------------------------------------------
    // Vocabulário único (via / horário / clima) usado pelo mapa,
    // pela predição e pelos relatórios.
    // ---------------------------------------------------------------------
    const VIA_OPTIONS = [
        { value: "francisco-junqueira", label: "Av. Francisco Junqueira" },
        { value: "dom-pedro", label: "Av. Dom Pedro I" },
        { value: "anhanguera", label: "Rod. Anhanguera" },
        { value: "centro", label: "Centro" },
        { value: "botanico", label: "Jardim Botânico" }
    ];

    const HORARIO_OPTIONS = [
        { value: "pico-manha", label: "07h-09h (pico manhã)", periodo: "Manhã" },
        { value: "fora-pico", label: "10h-16h (fora do pico)", periodo: "Tarde" },
        { value: "pico-noite", label: "17h-19h (pico noite)", periodo: "Noite" },
        { value: "madrugada", label: "00h-06h (madrugada)", periodo: "Madrugada" }
    ];

    const CLIMA_OPTIONS = [
        { value: "chuva", label: "Chuva" },
        { value: "sol", label: "Sol" },
        { value: "nublado", label: "Nublado" }
    ];

    const VEICULO_OPTIONS = [
        { value: "carro", label: "Carro" },
        { value: "moto", label: "Moto" },
        { value: "onibus", label: "Ônibus" }
    ];

    // Nos <select> de dia da semana, o valor exibido já é o próprio rótulo
    // (não existe um slug separado como em via/horário/clima).
    const DIA_OPTIONS = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"];

    function toLabelMap(options) {
        const map = {};
        options.forEach(function (opt) { map[opt.value] = opt.label; });
        return map;
    }

    const LABELS = {
        via: toLabelMap(VIA_OPTIONS),
        horario: toLabelMap(HORARIO_OPTIONS),
        clima: toLabelMap(CLIMA_OPTIONS),
        veiculo: toLabelMap(VEICULO_OPTIONS)
    };

    function periodoFromHorario(horarioValue) {
        const found = HORARIO_OPTIONS.find(function (opt) { return opt.value === horarioValue; });
        return found ? found.periodo : null;
    }

    // ---------------------------------------------------------------------
    // Storage helpers (usuários)
    // ---------------------------------------------------------------------
    const STORAGE_USERS = "riscoIA_users";
    const SESSION_TOKEN = "token";
    const SESSION_EXPIRES = "riscoIA_session_expires";
    const SESSION_USER = "riscoIA_current_user";

    function getUsers() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_USERS)) || [];
        } catch (e) {
            return [];
        }
    }

    function saveUsers(users) {
        localStorage.setItem(STORAGE_USERS, JSON.stringify(users));
    }

    function normalize(value) {
        return String(value || "").trim().toLowerCase();
    }

    function isValidEmail(value) {
        // Checagem simples de formato (não substitui validação real por e-mail).
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
    }

    function generateId() {
        if (typeof crypto !== "undefined" && crypto.randomUUID) {
            return crypto.randomUUID();
        }
        // Fallback sem crypto.randomUUID: junta timestamp + número aleatório
        // para reduzir (não eliminar) risco de colisão entre cadastros no
        // mesmo milissegundo.
        return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
    }

    // ---------------------------------------------------------------------
    // Hash de senha (SHA-256). Não é um hash "forte" para produção
    // (idealmente seria bcrypt/argon2 no backend, com salt por usuário),
    // mas já evita guardar a senha em texto puro no localStorage, que é o
    // pior cenário do protótipo anterior.
    // ---------------------------------------------------------------------
    async function sha256Hex(text) {
        if (typeof crypto !== "undefined" && crypto.subtle && crypto.subtle.digest) {
            const data = new TextEncoder().encode(text);
            const digest = await crypto.subtle.digest("SHA-256", data);
            return Array.from(new Uint8Array(digest))
                .map(function (b) { return b.toString(16).padStart(2, "0"); })
                .join("");
        }
        // Fallback para ambientes sem Web Crypto (ex.: testes em Node).
        const nodeCrypto = require("crypto");
        return nodeCrypto.createHash("sha256").update(text).digest("hex");
    }

    async function hashPassword(plainPassword) {
        return sha256Hex(plainPassword);
    }

    async function verifyPassword(plainPassword, hash) {
        return (await sha256Hex(plainPassword)) === hash;
    }

    // ---------------------------------------------------------------------
    // Sessão com expiração (antes o token nunca expirava)
    // ---------------------------------------------------------------------
    function createSessionToken(user) {
        return "RiscoIA-" + btoa(encodeURIComponent(user.username + "|" + Date.now()));
    }

    function startSession(user) {
        const expiresAt = Date.now() + CONFIG.SESSION_DURATION_MS;
        sessionStorage.setItem(SESSION_TOKEN, createSessionToken(user));
        sessionStorage.setItem(SESSION_EXPIRES, String(expiresAt));
        sessionStorage.setItem(SESSION_USER, JSON.stringify({
            id: user.id, name: user.name, email: user.email, username: user.username
        }));
    }

    function isSessionValid() {
        const token = sessionStorage.getItem(SESSION_TOKEN);
        const expiresAt = Number(sessionStorage.getItem(SESSION_EXPIRES) || 0);
        return Boolean(token) && Date.now() < expiresAt;
    }

    function getSessionUser() {
        try {
            return JSON.parse(sessionStorage.getItem(SESSION_USER));
        } catch (e) {
            return null;
        }
    }

    function clearSession() {
        sessionStorage.removeItem(SESSION_TOKEN);
        sessionStorage.removeItem(SESSION_EXPIRES);
        sessionStorage.removeItem(SESSION_USER);
    }

    // ---------------------------------------------------------------------
    // UI helpers
    // ---------------------------------------------------------------------
    function showMessage(el, text, type) {
        if (!el) return;
        el.textContent = text;
        el.className = "message " + type;
    }

    function clearMessage(el) {
        if (!el) return;
        el.textContent = "";
        el.className = "message hidden";
    }

    // ---------------------------------------------------------------------
    // Lógica de predição (pura, sem DOM - por isso é testável direto)
    // ---------------------------------------------------------------------
    function calculateFallback(data) {
        let score = 30;
        if (data.horario === "pico-manha" || data.horario === "pico-noite") score += 25;
        if (data.clima === "chuva") score += 20;
        if (data.via === "francisco-junqueira") score += 10;
        if (data.via === "anhanguera") score += 8;

        // Dia da semana: sexta tende a ter mais tráfego/saídas noturnas;
        // fins de semana tendem a ter menos tráfego de deslocamento (embora
        // possam ter mais risco noturno em outros contextos). É uma
        // heurística demonstrativa, não um resultado de modelo estatístico.
        if (data.dia === "Sexta-feira") score += 5;
        if (data.dia === "Sábado" || data.dia === "Domingo") score -= 5;

        return Math.max(5, Math.min(97, score));
    }

    function levelFromProb(prob) {
        return prob >= 70 ? "alto" : prob >= 40 ? "medio" : "baixo";
    }

    function zoneMatches(zone, filters) {
        const horario = (filters && filters.horario) || "todos";
        const clima = (filters && filters.clima) || "todos";
        const veiculo = (filters && filters.veiculo) || "todos";
        return (horario === "todos" || zone.horario === horario)
            && (clima === "todos" || zone.clima === clima)
            && (veiculo === "todos" || zone.veiculo === veiculo);
    }

    // ---------------------------------------------------------------------
    // "Tempo real" honesto: não existe fluxo contínuo de sinistros ao vivo
    // (o InfoSiga só publica um arquivo novo por mês), então o que dá para
    // ter em tempo real é a CONDIÇÃO atual (hora + clima reais) alimentando
    // o modelo/heurística de risco - não a ocorrência de sinistros em si.
    // ---------------------------------------------------------------------

    // Coordenadas aproximadas do centro de Ribeirão Preto/SP, usadas para
    // consultar o clima atual na Open-Meteo (API pública, sem chave, com
    // CORS liberado para uso direto do navegador).
    const RIBEIRAO_PRETO_COORDS = { latitude: -21.1775, longitude: -47.8103 };

    function diaAtualPtBR(date) {
        const d = date || new Date();
        // getDay(): 0 = domingo ... 6 = sábado
        const index = [6, 0, 1, 2, 3, 4, 5][d.getDay()]; // reordena para bater com DIA_OPTIONS (segunda primeiro)
        return DIA_OPTIONS[index];
    }

    function horarioAtualBucket(date) {
        const hour = (date || new Date()).getHours();
        if (hour >= 7 && hour <= 9) return "pico-manha";
        if (hour >= 10 && hour <= 16) return "fora-pico";
        // As faixas de horário do formulário cobrem só 07h-19h + madrugada;
        // as horas entre 20h e 23h ficam fora dos rótulos originais, então
        // são tratadas aqui como extensão do horário de pico noturno.
        if (hour >= 17 && hour <= 21) return "pico-noite";
        return "madrugada"; // 22h-06h
    }

    function climaFromWeatherCode(code) {
        // Códigos meteorológicos WMO usados pela Open-Meteo.
        if (code === 0) return "sol";
        if ([1, 2, 3, 45, 48].includes(code)) return "nublado";
        return "chuva"; // 51+ cobre garoa, chuva, pancadas e tempestade
    }

    async function fetchLiveWeatherClima() {
        const { latitude, longitude } = RIBEIRAO_PRETO_COORDS;
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=weather_code&timezone=America%2FSao_Paulo`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Falha ao consultar o clima atual");
        const data = await response.json();
        return climaFromWeatherCode(data.current.weather_code);
    }

    return {
        CONFIG: CONFIG,
        VIA_OPTIONS: VIA_OPTIONS,
        HORARIO_OPTIONS: HORARIO_OPTIONS,
        CLIMA_OPTIONS: CLIMA_OPTIONS,
        VEICULO_OPTIONS: VEICULO_OPTIONS,
        DIA_OPTIONS: DIA_OPTIONS,
        LABELS: LABELS,
        periodoFromHorario: periodoFromHorario,
        getUsers: getUsers,
        saveUsers: saveUsers,
        normalize: normalize,
        isValidEmail: isValidEmail,
        generateId: generateId,
        hashPassword: hashPassword,
        verifyPassword: verifyPassword,
        startSession: startSession,
        isSessionValid: isSessionValid,
        getSessionUser: getSessionUser,
        clearSession: clearSession,
        showMessage: showMessage,
        clearMessage: clearMessage,
        calculateFallback: calculateFallback,
        levelFromProb: levelFromProb,
        zoneMatches: zoneMatches,
        diaAtualPtBR: diaAtualPtBR,
        horarioAtualBucket: horarioAtualBucket,
        climaFromWeatherCode: climaFromWeatherCode,
        fetchLiveWeatherClima: fetchLiveWeatherClima
    };
});
