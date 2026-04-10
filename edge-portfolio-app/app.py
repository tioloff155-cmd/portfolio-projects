from flask import Flask, render_template

app = Flask(__name__)
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

PROJECTS = [
    {
        'name': 'Job Tracker',
        'description': 'Task management platform for job opportunities. RESTful API with SQLite backend, real-time frontend updates, and comprehensive error handling.',
        'tech': 'Python, Flask, SQLite, JavaScript, HTML5, CSS3',
        'link': 'https://github.com/tioloff155-cmd/portfolio-projects'
    },
    {
        'name': 'Workflow Automation',
        'description': 'Data ETL pipeline with CSV ingestion, transformation, validation, and Excel export. Optimized for 100k+ row datasets with comprehensive error recovery.',
        'tech': 'Python, Pandas, openpyxl',
        'link': 'https://github.com/tioloff155-cmd/portfolio-projects'
    },
    {
        'name': 'Portfolio Website',
        'description': 'Production-grade web presence with server-side rendering, zero external dependencies, and performance optimization. Lighthouse 95+ score.',
        'tech': 'Python, Flask, JavaScript, CSS3',
        'link': 'https://github.com/tioloff155-cmd/portfolio-projects'
    }
]

SKILLS = [
    'Python 3.10+',
    'Flask / Web Frameworks',
    'Data Engineering & ETL',
    'Pandas / NumPy',
    'SQL / Database Design',
    'REST API Architecture',
    'Vanilla JavaScript',
    'Docker / Containerization',
    'Git / Version Control',
    'AWS / Cloud Services',
    'Performance Optimization',
    'SOLID Principles'
]

@app.route('/')
def home():
    return render_template('index.html', projects=PROJECTS, skills=SKILLS)

if __name__ == '__main__':
    app.run()
