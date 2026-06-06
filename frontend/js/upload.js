/**
 * SkillBridge AI — Upload Page Logic
 * Handles PDF drag-and-drop and file upload.
 * Scanned PDFs are handled automatically via Gemini Vision OCR on the backend.
 */

const dropZone    = document.getElementById('dropZone');
const fileInput   = document.getElementById('fileInput');
const browseLink  = document.getElementById('browseLink');
const fileInfo    = document.getElementById('fileInfo');
const fileName    = document.getElementById('fileName');
const fileSize    = document.getElementById('fileSize');
const fileRemove  = document.getElementById('fileRemove');
const jobRole     = document.getElementById('jobRole');
const customRole  = document.getElementById('customRole');
const submitBtn   = document.getElementById('submitBtn');
const uploadForm  = document.getElementById('uploadForm');
const errorBanner = document.getElementById('errorBanner');
const overlay     = document.getElementById('analyzingOverlay');

let selectedFile = null;

// ─── File Selection ───────────────────────────────────────────────────────────

browseLink.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('click', (e) => { if (e.target !== browseLink) fileInput.click(); });
fileInput.addEventListener('change', () => { if (fileInput.files.length > 0) handleFile(fileInput.files[0]); });

// ─── Drag & Drop ──────────────────────────────────────────────────────────────

dropZone.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

// ─── File Validation ──────────────────────────────────────────────────────────

function handleFile(file) {
  clearError();

  if (!file.name.toLowerCase().endsWith('.pdf') || file.type !== 'application/pdf') {
    showError('Only PDF files are accepted. Please upload a .pdf file.');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showError('File too large. Maximum size is 10MB.');
    return;
  }

  selectedFile = file;
  fileName.textContent = file.name;
  fileSize.textContent = formatBytes(file.size);
  fileInfo.classList.add('visible');
  dropZone.classList.add('file-selected');
  checkFormReady();
}

fileRemove.addEventListener('click', (e) => {
  e.stopPropagation();
  selectedFile = null;
  fileInput.value = '';
  fileInfo.classList.remove('visible');
  dropZone.classList.remove('file-selected');
  checkFormReady();
});

// ─── Form Validation ──────────────────────────────────────────────────────────

jobRole.addEventListener('change', checkFormReady);
customRole.addEventListener('input', checkFormReady);

function checkFormReady() {
  const roleValue = customRole.value.trim() || jobRole.value;
  submitBtn.disabled = !(selectedFile && roleValue);
}

// ─── Form Submission ──────────────────────────────────────────────────────────

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearError();

  if (!selectedFile) { showError('Please select a PDF file to upload.'); return; }

  const role = customRole.value.trim() || jobRole.value;
  if (!role) { showError('Please select or enter a target job role.'); return; }

  showOverlay();

  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('job_role', role);

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Analysis failed. Please try again.');
    }

    sessionStorage.setItem('analysisResult', JSON.stringify(data));
    window.location.href = '/dashboard';

  } catch (err) {
    hideOverlay();
    showError(err.message || 'Something went wrong. Please try again.');
  }
});

// ─── Overlay Animation ────────────────────────────────────────────────────────

function showOverlay() {
  overlay.classList.add('visible');
  submitBtn.disabled = true;

  const steps  = ['step1', 'step2', 'step3', 'step4'];
  const delays = [0, 3000, 8000, 15000];

  steps.forEach((id, i) => {
    setTimeout(() => {
      if (i > 0) {
        document.getElementById(steps[i - 1]).classList.remove('active');
        document.getElementById(steps[i - 1]).classList.add('done');
      }
      document.getElementById(id).classList.add('active');
    }, delays[i]);
  });
}

function hideOverlay() {
  overlay.classList.remove('visible');
  checkFormReady();
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function showError(msg) {
  errorBanner.textContent = '⚠ ' + msg;
  errorBanner.classList.add('visible');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function clearError() {
  errorBanner.textContent = '';
  errorBanner.classList.remove('visible');
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
