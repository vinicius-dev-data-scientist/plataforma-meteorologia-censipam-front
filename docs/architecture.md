# Arquitetura do Projeto

## Visão Geral
- Distribuição, organização e escalonamento de funcionalidades do sistema.

## Organização Geral
- app.py: ponto de entrada da aplicação
- pages/: páginas da aplicação
- components/: componentes reutilizáveis da interface
- services/: regras de negócio e acesso a dados
- utils/: funções auxiliares
- datasets/: dados utilizados pela aplicação
- img/: imagens utilizadas na aplicação
- requirements/: dependências necessários para o desenvolvimento, aplicação e funcionamento do projeto
- style/: aplicação de seletores de estilização das páginas do projeto.

## Fluxo de Execução
1. O Streamlit inicia a partir de app.py
2. app.py configura o layout e o estado global
3. As páginas são carregadas a partir de pages/
4. Cada página utiliza componentes de components/
5. Acessos aos dados ficam em datasets/ e img/
6. Processamentos de dados ficam em services/
7. Dados processados são exibidos de volta em pages/