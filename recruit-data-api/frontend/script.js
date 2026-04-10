const form = document.getElementById('job-form');
const jobsContainer = document.getElementById('jobs');
const exportButton = document.getElementById('export');

function loadJobs() {
  fetch('/api/jobs')
    .then(response => response.json())
    .then(data => {
      jobsContainer.innerHTML = data.map(job => `
        <div class="job-card">
          <strong>${job.company} - ${job.position}</strong>
          <div class="meta">Status: ${job.status} | Prioridade: ${job.priority}</div>
          <p>${job.notes || 'Sem notas'}</p>
          <button onclick="deleteJob(${job.id})">Remover</button>
        </div>
      `).join('');
    });
}

function deleteJob(id) {
  fetch(`/api/jobs/${id}`, { method: 'DELETE' })
    .then(() => loadJobs());
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const data = {
    company: document.getElementById('company').value,
    position: document.getElementById('position').value,
    status: document.getElementById('status').value,
    priority: document.getElementById('priority').value,
    notes: document.getElementById('notes').value,
  };

  fetch('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(() => {
    form.reset();
    loadJobs();
  });
});

exportButton.addEventListener('click', () => {
  window.location.href = '/api/jobs/export';
});

loadJobs();
