RiscoIA — Projeto Frontend Integrado

ESTRUTURA
- index.html       -> tela de login/cadastro
- dashboard.html   -> interface principal protegida
- login.css        -> estilos da tela de acesso
- style.css        -> estilos da interface/mapa
- script.js        -> autenticação + mapa + menu + animações

FLUXO
1. Abra index.html.
2. Crie uma conta.
3. O sistema salva o usuário no localStorage apenas para TESTE.
4. Após o cadastro/login, o usuário é enviado para dashboard.html.
5. dashboard.html verifica o token da sessão.
6. O botão "Sair" encerra a sessão e volta para index.html.

IMPORTANTE
Este login é apenas para demonstração frontend. Senhas não devem ser armazenadas
em localStorage em um sistema real. Para produção, substitua a autenticação
por uma API/backend.

MAPA
O mapa visual é o componente frontend já existente no projeto. Os botões de
zoom e centralização funcionam pelo JavaScript. Os links do Infosiga continuam
apontando para as plataformas oficiais.
