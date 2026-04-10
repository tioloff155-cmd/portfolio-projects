# Workflow Automation

Aplicação em Python para automatizar relatórios e limpeza de dados de planilhas.

## Funcionalidades

- importa dados de arquivos CSV ou planilhas
- realiza limpeza e transformação básica dos dados
- gera relatórios consolidados em Excel ou CSV
- exporta métricas de vendas, estoque e lucro

## Tecnologias

- Python
- Pandas
- openpyxl

## Como rodar

```bash
cd workflow-automation
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python automations.py
```

O script usa `input/sales.csv` como exemplo de entrada e gera `output/sales_report.xlsx`.
