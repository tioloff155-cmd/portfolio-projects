from flask import Flask, render_template

app = Flask(__name__)

github_username = 'tioloff155-cmd'

projects = [
    {
        'name': 'Job Tracker',
        'description': 'Plataforma para registrar vagas, gerenciar candidaturas e acompanhar entrevistas.',
        'tech': 'Python, Flask, JavaScript, HTML, CSS',
        'link': f'https://github.com/{github_username}/job-tracker'
    },
    {
        'name': 'Workflow Automation',
        'description': 'Automação de planilhas com limpeza de dados e geração de relatórios Excel.',
        'tech': 'Python, Pandas, openpyxl',
        'link': f'https://github.com/{github_username}/workflow-automation'
    },
    {
        'name': 'Portfolio Website',
        'description': 'Site de apresentação com projetos, habilidades e contatos profissionais.',
        'tech': 'Python, Flask, HTML, CSS',
        'link': f'https://github.com/{github_username}/portfolio'
    }
]

skills = [
    'Python', 'Flask', 'Pandas', 'Automation', 'APIs', 'HTML', 'CSS', 'JavaScript', 'Git', 'DevOps'
]

@app.route('/')
def home():
    return render_template('index.html', projects=projects, skills=skills)

if __name__ == '__main__':
    app.run(debug=True)
