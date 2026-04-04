# Portfólio de Projetos

Três projetos Python prontos para apresentação em GitHub e uso pessoal para oportunidades de trabalho remoto.

## Projetos

### 1. Job Tracker
- **Descrição**: Plataforma web para registrar vagas, gerenciar candidaturas e acompanhar entrevistas
- **Tecnologias**: Python, Flask, JavaScript, HTML, CSS
- **Pasta**: `job-tracker/`

### 2. Workflow Automation
- **Descrição**: Script de automação para limpeza de dados e geração de relatórios Excel
- **Tecnologias**: Python, Pandas, openpyxl
- **Pasta**: `workflow-automation/`

### 3. Portfolio Website
- **Descrição**: Site de apresentação com projetos, habilidades e contatos profissionais
- **Tecnologias**: Python, Flask, HTML, CSS, JavaScript
- **Pasta**: `portfolio/`

## Como usar cada projeto

1. Navegue para a pasta do projeto
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Execute conforme o projeto:
   - **job-tracker**: `python app.py` (acesse http://127.0.0.1:5000)
   - **workflow-automation**: `python automations.py`
   - **portfolio**: `python app.py` (acesse http://127.0.0.1:5000)

## Personalização

- Atualize o `portfolio/app.py` com seu usuário do GitHub para que os links dos projetos apontem para seus repositórios
- Substitua `firmenetto@gmail.com` pelo seu e-mail conforme necessário
- Adapte as descrições dos projetos para refletir sua experiência

## Deploy

Cada projeto pode ser deployado em:
- **Heroku** (com Procfile)
- **GitHub Pages** (versões estáticas)
- **Seu servidor** (VPS, Cloud)
