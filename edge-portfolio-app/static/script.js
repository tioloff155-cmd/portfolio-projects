const projectGrid = document.getElementById('projectGrid');
const tags = document.querySelectorAll('.tag');

function normalizeTech(text) {
    return text.toLowerCase();
}

function filterProjects(filter) {
    const cards = document.querySelectorAll('.project-card');
    cards.forEach(card => {
        const techText = normalizeTech(card.dataset.tech);
        if (filter === 'all' || techText.includes(normalizeTech(filter))) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

tags.forEach(tag => {
    tag.addEventListener('click', () => {
        tags.forEach(item => item.classList.remove('active'));
        tag.classList.add('active');
        filterProjects(tag.dataset.filter);
    });
});
