"use strict";

/*
 * RiscoIA - autenticação frontend
 *
 * Esta versão funciona sem backend para testes:
 * - Cadastro: localStorage
 * - Login: valida os dados cadastrados
 * - Sessão: sessionStorage
 * - Após entrar: dashboard.html
 *
 * IMPORTANTE:
 * Para produção, não armazene senhas no localStorage.
 * Substitua as funções de cadastro/login por chamadas à sua API.
 */

const STORAGE_USERS = "riscoIA_users";
const SESSION_TOKEN = "token";
const SESSION_USER = "riscoIA_current_user";

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const switchAuth = document.getElementById("switchAuth");
const switchText = document.getElementById("switchText");
const formTitle = document.getElementById("formTitle");
const formSubtitle = document.getElementById("formSubtitle");

function getUsers() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_USERS)) || [];
    } catch {
        return [];
    }
}

function saveUsers(users) {
    localStorage.setItem(STORAGE_USERS, JSON.stringify(users));
}

function normalize(value) {
    return value.trim().toLowerCase();
}

function createToken(user) {
    return "RiscoIA-" + btoa(
        encodeURIComponent(user.username + "|" + Date.now())
    );
}

function showMessage(element, text, type) {
    element.textContent = text;
    element.className = "message " + type;
}

function clearMessage(element) {
    element.textContent = "";
    element.className = "message hidden";
}

function setLoginMode() {
    loginForm.classList.remove("hidden");
    registerForm.classList.add("hidden");

    formTitle.textContent = "Acesse o sistema";
    formSubtitle.textContent =
        "Entre para visualizar o mapa de risco e as análises de sinistros de trânsito.";

    switchText.textContent = "Ainda não possui uma conta?";
    switchAuth.textContent = "Criar conta";

    clearMessage(document.getElementById("loginMessage"));
}

function setRegisterMode() {
    loginForm.classList.add("hidden");
    registerForm.classList.remove("hidden");

    formTitle.textContent = "Criar sua conta";
    formSubtitle.textContent =
        "Cadastre seus dados para acessar o sistema de análise de risco.";

    switchText.textContent = "Já possui uma conta?";
    switchAuth.textContent = "Entrar";

    clearMessage(document.getElementById("registerMessage"));
}

switchAuth.addEventListener("click", () => {
    if (loginForm.classList.contains("hidden")) {
        setLoginMode();
    } else {
        setRegisterMode();
    }
});

document.querySelectorAll(".password-toggle").forEach(button => {
    button.addEventListener("click", () => {
        const input = document.getElementById(button.dataset.target);

        if (input.type === "password") {
            input.type = "text";
            button.textContent = "Ocultar";
        } else {
            input.type = "password";
            button.textContent = "Mostrar";
        }
    });
});

registerForm.addEventListener("submit", event => {
    event.preventDefault();

    const name = document.getElementById("registerName").value.trim();
    const email = normalize(document.getElementById("registerEmail").value);
    const username = normalize(document.getElementById("registerUsername").value);
    const password = document.getElementById("registerPassword").value;
    const confirmPassword =
        document.getElementById("registerPasswordConfirm").value;

    const message = document.getElementById("registerMessage");

    if (name.length < 3) {
        showMessage(message, "Digite seu nome completo.", "error");
        return;
    }

    if (username.length < 3) {
        showMessage(message, "O usuário precisa ter pelo menos 3 caracteres.", "error");
        return;
    }

    if (password.length < 6) {
        showMessage(message, "A senha precisa ter pelo menos 6 caracteres.", "error");
        return;
    }

    if (password !== confirmPassword) {
        showMessage(message, "As senhas não coincidem.", "error");
        return;
    }

    const users = getUsers();

    const alreadyExists = users.some(user =>
        user.username === username || user.email === email
    );

    if (alreadyExists) {
        showMessage(
            message,
            "Este usuário ou e-mail já está cadastrado.",
            "error"
        );
        return;
    }

    const newUser = {
        id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
        name,
        email,
        username,
        password,
        createdAt: new Date().toISOString()
    };

    users.push(newUser);
    saveUsers(users);

    showMessage(
        message,
        "Cadastro realizado! Entrando no sistema...",
        "success"
    );

    setTimeout(() => {
        loginWithUser(newUser);
    }, 700);
});

loginForm.addEventListener("submit", event => {
    event.preventDefault();

    const username = normalize(
        document.getElementById("loginUsername").value
    );
    const password =
        document.getElementById("loginPassword").value;

    const message = document.getElementById("loginMessage");
    const button = document.getElementById("loginButton");
    const buttonText = document.getElementById("loginButtonText");
    const loading = document.getElementById("loginLoading");

    clearMessage(message);

    button.disabled = true;
    buttonText.classList.add("hidden");
    loading.classList.remove("hidden");

    setTimeout(() => {
        const users = getUsers();

        const user = users.find(item =>
            (item.username === username || item.email === username) &&
            item.password === password
        );

        if (!user) {
            button.disabled = false;
            buttonText.classList.remove("hidden");
            loading.classList.add("hidden");

            showMessage(
                message,
                "Usuário/e-mail ou senha incorretos.",
                "error"
            );
            return;
        }

        loginWithUser(user);
    }, 450);
});

function loginWithUser(user) {
    const token = createToken(user);

    sessionStorage.setItem(SESSION_TOKEN, token);
    sessionStorage.setItem(
        SESSION_USER,
        JSON.stringify({
            id: user.id,
            name: user.name,
            email: user.email,
            username: user.username
        })
    );

    const remember = document.getElementById("rememberMe");

    if (remember && remember.checked) {
        localStorage.setItem("riscoIA_remember", "true");
    } else {
        localStorage.removeItem("riscoIA_remember");
    }

    window.location.href = "dashboard.html";
}

/*
 * Se já existe uma sessão, não deixa o usuário ficar
 * parado na tela de login.
 */
document.addEventListener("DOMContentLoaded", () => {
    const token = sessionStorage.getItem(SESSION_TOKEN);

    if (token) {
        window.location.href = "dashboard.html";
    }
});


/* =====================================================
   RiscoIA
   JavaScript principal
===================================================== */


/* =====================================================
   VARIÁVEIS DO MAPA
===================================================== */

let zoom = 1;


/* =====================================================
   ZOOM +
===================================================== */

function zoomIn() {

    const map =
        document.getElementById("riskMap");


    zoom += 0.15;


    if (zoom > 1.7) {

        zoom = 1.7;

    }


    map.style.transform =
        `scale(${zoom})`;

}


/* =====================================================
   ZOOM -
===================================================== */

function zoomOut() {

    const map =
        document.getElementById("riskMap");


    zoom -= 0.15;


    if (zoom < 1) {

        zoom = 1;

    }


    map.style.transform =
        `scale(${zoom})`;

}


/* =====================================================
   CENTRALIZAR MAPA
===================================================== */

function mapHome() {

    const map =
        document.getElementById("riskMap");


    zoom = 1;

    map.style.transform =
        "scale(1)";

}


/* =====================================================
   MENU MOBILE
===================================================== */

const mobileMenu =
    document.getElementById("mobileMenu");

if (mobileMenu) {
mobileMenu.addEventListener(
    "click",
    function () {

        const menu =
            document.querySelector(".nav-menu");


        if (
            menu.style.display === "flex"
        ) {

            menu.style.display = "none";

        } else {

            menu.style.display = "flex";

            menu.style.position =
                "absolute";

            menu.style.top = "72px";

            menu.style.left = "0";

            menu.style.width = "100%";

            menu.style.height = "auto";

            menu.style.padding = "20px";

            menu.style.background =
                "#050f1d";

            menu.style.flexDirection =
                "column";

        }

    }
);
}

/* =====================================================
   FECHAR MENU MOBILE AO CLICAR
===================================================== */

const links =
    document.querySelectorAll(".nav-link");


links.forEach(link => {

    link.addEventListener(
        "click",
        function () {

            const menu =
                document.querySelector(".nav-menu");


            if (
                window.innerWidth <= 900
            ) {

                menu.style.display = "none";

            }

        }
    );

});


/* =====================================================
   MENU ATIVO
===================================================== */

const sections =
    document.querySelectorAll(
        "section[id]"
    );


window.addEventListener(
    "scroll",
    function () {

        let current = "";


        sections.forEach(section => {

            const top =
                section.offsetTop - 130;


            const height =
                section.offsetHeight;


            if (
                window.scrollY >= top &&
                window.scrollY <
                top + height
            ) {

                current =
                    section.getAttribute("id");

            }

        });


        links.forEach(link => {

            link.classList.remove(
                "active"
            );


            if (
                link.getAttribute("href") ===
                "#" + current
            ) {

                link.classList.add(
                    "active"
                );

            }

        });

    }
);


/* =====================================================
   ANIMAÇÃO DOS INDICADORES
===================================================== */

const cards =
    document.querySelectorAll(
        ".stat-card"
    );


const observer =
    new IntersectionObserver(
        function (entries) {

            entries.forEach(entry => {

                if (
                    entry.isIntersecting
                ) {

                    entry.target.style.opacity =
                        "1";

                    entry.target.style.transform =
                        "translateY(0)";

                }

            });

        },
        {
            threshold: 0.2
        }
    );


cards.forEach(card => {

    card.style.opacity = "0";

    card.style.transform =
        "translateY(15px)";

    card.style.transition =
        "all .5s ease";

    observer.observe(card);

});


/* =====================================================
   LOG
===================================================== */

console.log(
    "RiscoIA carregado."
);


console.log(
    "Fonte oficial: Infosiga / Detran-SP"
);


/* =====================================================
   USUÁRIO LOGADO
===================================================== */
try {
    const user = JSON.parse(sessionStorage.getItem("riscoIA_current_user"));
    if (user) {
        document.title = "RiscoIA | " + user.name;
    }
} catch (error) {
    console.warn("Sessão do usuário indisponível.", error);
}
