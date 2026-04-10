# Job Tracker

Aplicação fullstack para acompanhar candidaturas de emprego e status de vagas.

## Funcionalidades

- Cadastro de vagas com status (candidat@, entrevista, rejeitado, oferecido)
- Filtros por empresa, tecnologia e prioridade
- Dashboard simples com métricas de progresso
- Exportação de dados para CSV

## Tecnologias

- Backend: Flask, SQLite
- Frontend: HTML, CSS, JavaScript

## Como rodar

```bash
cd job-tracker
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:5000` no navegador.
