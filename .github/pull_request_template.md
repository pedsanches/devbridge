# Pull Request Checklist

## 🔍 UI Governance Check
*(Obrigatório se houve alteração em frontend)*
- [ ] **Tokens Only**: Confirmo que não usei HEX (`#000`), PX (`15px`) ou valores arbitrários (`bg-[#f0f]`) em componentes.
- [ ] **Components**: Usei componentes canônicos (`EvidenceTable`, `InsightCard`) ao invés de criar novos.
- [ ] **Anti-Patterns**: A interface está livre de sombras difusas, cores não-semânticas e "magic values".
- [ ] **Mobile**: Testei em viewport mobile (se aplicável).
- [ ] **Evidence**: Se adicionei insights de IA, garanti o link para evidência (R#).

## 🧪 Tests & Quality
- [ ] Rodei `make test` e passou.
- [ ] Rodei `make lint` (inclui `lint-ui`) e passou.

## 📝 Description
Descreva o que mudou e porquê. Se for UI, adicione screenshot.
