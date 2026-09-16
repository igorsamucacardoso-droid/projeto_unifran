# RiscoIA - Atualizações desta versão

Este arquivo documenta o que mudou em relação à versão anterior do
protótipo. O `README.txt` original foi mantido como estava.

## Arquivos novos

- **`utils.js`** — camada compartilhada carregada antes de `script.js` e
  `enhancements.js` em todas as páginas. Contém:
  - o vocabulário único de vias/horários/clima (`VIA_OPTIONS`,
    `HORARIO_OPTIONS`, `CLIMA_OPTIONS` e os mapas `LABELS`), usado tanto
    pelo mapa quanto pelo formulário de predição e pelos relatórios — antes
    cada tela tinha sua própria lista e elas estavam dessincronizadas;
  - hashing de senha (SHA-256) e checagem de sessão com expiração;
  - as funções puras de lógica (`calculateFallback`, `levelFromProb`,
    `zoneMatches`, `isValidEmail`), escritas para funcionar tanto no
    navegador quanto no Node — por isso dá para testá-las isoladamente.
- **`tests/logic.test.js`** — testes automatizados simples (sem framework)
  para as funções de `utils.js`. Para rodar:
  ```
  node tests/logic.test.js
  ```

## O que mudou em cada arquivo existente

- **`script.js`**: reformatado (estava tudo em uma linha por função);
  senha passa a ser guardada com hash (`passwordHash`) em vez de texto
  puro; sessão expira depois de 12h e é checada periodicamente; URL da
  API extraída para `RiscoIA.CONFIG.API_BASE_URL`; zonas do mapa usam o
  mesmo vocabulário de vias/horários do formulário de predição; os
  gráficos (`Chart.js`) agora são atualizados com o histórico real de
  previsões assim que ele existir, e não ficam mais travados em números
  fixos.
- **`enhancements.js`**: recuperação de senha agora tem uma segunda etapa
  com código de verificação (gerado e mostrado na tela, já que é um
  protótipo sem backend de e-mail — deixado bem explícito na interface);
  o histórico de previsões passa a ser salvo reagindo a um evento
  (`riscoia:prediction`) disparado por `script.js`, em vez de observar o
  DOM com `MutationObserver`; adicionado um filtro por via nos relatórios.
- **`index.html`**: opções de horário do filtro do mapa atualizadas para o
  vocabulário unificado; adicionado um estado de carregamento sobre o
  mapa enquanto os tiles do OpenStreetMap carregam.
- **`forgot-password.html`**: formulário dividido em duas etapas
  (identificar a conta → confirmar código → definir nova senha).
- **`relatorios.html`**: novo campo de filtro por via.
- **`login.html` / `predicao.html` / `relatorios.html`**: agora carregam
  `utils.js` antes dos outros scripts.

## Limitações que continuam existindo (e por quê)

- Ainda não há backend real: login, cadastro e histórico continuam em
  `localStorage`/`sessionStorage`. O hash de senha melhora o cenário, mas
  não substitui autenticação server-side de verdade.
- O código de verificação da recuperação de senha é mostrado na própria
  tela porque não existe servidor de e-mail neste protótipo — isso está
  documentado na própria interface para não passar a impressão de que é
  assim que funcionaria em produção.
- Não implementei um alternador de tema claro/escuro: o layout já é
  inteiramente escuro por padrão e as cores estão espalhadas por um
  `style.css` de ~1900 linhas sem variáveis CSS. Fazer isso direito exigiria
  extrair essas cores para `:root`/`prefers-color-scheme` em todo o arquivo
  — um refactor grande demais para entrar "de brinde" numa rodada de
  ajustes, e arriscado sem conseguir visualizar o resultado num navegador
  de verdade. Prefiro sinalizar isso do que entregar um toggle que pode
  quebrar o visual em alguma seção.
