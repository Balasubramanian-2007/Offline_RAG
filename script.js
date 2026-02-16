// API base URL - adjust if backend is on different port
const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', function() {
    loadDocuments();

    // Upload form handler
    document.getElementById('uploadForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('fileInput');
        const statusDiv = document.getElementById('uploadStatus');

        if (!fileInput.files[0]) {
            showStatus('Please select a file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        showStatus('Uploading...', 'loading');

        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                showStatus('File uploaded successfully!', 'success');
                fileInput.value = '';
                loadDocuments(); // Refresh document list
            } else {
                showStatus(result.detail || 'Upload failed', 'error');
            }
        } catch (error) {
            showStatus('Network error: ' + error.message, 'error');
        }
    });

    // Query form handler
    document.getElementById('queryForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const queryInput = document.getElementById('queryInput');
        const resultDiv = document.getElementById('queryResult');

        const query = queryInput.value.trim();
        if (!query) {
            showQueryResult('Please enter a question', 'error');
            return;
        }

        showQueryResult('Thinking...', 'loading');

        try {
            const response = await fetch(`${API_BASE}/result`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });

            const result = await response.json();

            if (response.ok) {
                showQueryResult(`<strong>Question:</strong> ${result['Question:']}<br><br><strong>Answer:</strong> ${result['Response:']}`, 'success');
            } else {
                showQueryResult(result.detail || 'Query failed', 'error');
            }
        } catch (error) {
            showQueryResult('Network error: ' + error.message, 'error');
        }
    });
});

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/documents`);
        const result = await response.json();

        const documentsList = document.getElementById('documentsList');
        documentsList.innerHTML = '';

        if (result.documents && result.documents.length > 0) {
            result.documents.forEach(doc => {
                const docElement = document.createElement('div');
                docElement.className = 'document-item';
                docElement.innerHTML = `
                    <span>${doc}</span>
                    <button onclick="deleteDocument('${doc}')">Delete</button>
                `;
                documentsList.appendChild(docElement);
            });
        } else {
            documentsList.innerHTML = '<p>No documents uploaded yet.</p>';
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        document.getElementById('documentsList').innerHTML = '<p>Error loading documents.</p>';
    }
}

async function deleteDocument(docName) {
    if (!confirm(`Are you sure you want to delete "${docName}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/deleteDocuments?query=${encodeURIComponent(docName)}`);
        if (response.ok) {
            loadDocuments(); // Refresh list
            showStatus('Document deleted successfully', 'success');
        } else {
            showStatus('Failed to delete document', 'error');
        }
    } catch (error) {
        showStatus('Network error: ' + error.message, 'error');
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.textContent = message;
    statusDiv.className = type;
}

function showQueryResult(message, type) {
    const resultDiv = document.getElementById('queryResult');
    resultDiv.innerHTML = message;
    resultDiv.className = type;
}