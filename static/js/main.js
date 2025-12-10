/**
 * AI Animal Type Classification - Main JavaScript
 * Handles image upload, analysis, and results display
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const removeImageBtn = document.getElementById('removeImage');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('resultsSection');
    const loadingState = document.getElementById('loadingState');
    const resultsContent = document.getElementById('resultsContent');

    let selectedFile = null;
    let currentReportId = null;

    // ========== Upload Handling ==========
    
    // Click to upload
    if (uploadArea) {
        uploadArea.addEventListener('click', () => imageInput.click());
    }

    // Drag and drop
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
    }

    // File input change
    if (imageInput) {
        imageInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    // Remove image
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', () => {
            resetUpload();
        });
    }

    // Handle file selection
    function handleFileSelect(file) {
        // Validate file type
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Invalid file type. Please use PNG, JPG, JPEG, or WebP.');
            return;
        }

        // Validate file size (16MB max)
        if (file.size > 16 * 1024 * 1024) {
            alert('File too large. Maximum size is 16MB.');
            return;
        }

        selectedFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            uploadArea.style.display = 'none';
            previewContainer.style.display = 'block';
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    // Reset upload
    function resetUpload() {
        selectedFile = null;
        imageInput.value = '';
        previewImage.src = '';
        uploadArea.style.display = 'block';
        previewContainer.style.display = 'none';
        analyzeBtn.disabled = true;
        resultsSection.style.display = 'none';
    }

    // ========== Analysis ==========

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            if (!selectedFile) return;

            // Show loading state
            resultsSection.style.display = 'block';
            loadingState.style.display = 'block';
            resultsContent.style.display = 'none';
            analyzeBtn.disabled = true;

            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth' });

            try {
                // Upload and analyze
                const formData = new FormData();
                formData.append('image', selectedFile);

                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // Store report ID
                currentReportId = data.report_id;

                // Display results
                displayResults(data.report);

            } catch (error) {
                alert('Analysis failed: ' + error.message);
                loadingState.style.display = 'none';
            } finally {
                analyzeBtn.disabled = false;
            }
        });
    }

    // Display results
    function displayResults(report) {
        loadingState.style.display = 'none';
        resultsContent.style.display = 'block';

        // Animal info
        const animalInfo = document.getElementById('animalInfo');
        if (animalInfo) {
            animalInfo.innerHTML = `
                <div class="info-badge">
                    <strong>Type:</strong> ${capitalize(report.animal_info.type)}
                </div>
                <div class="info-badge">
                    <strong>Breed:</strong> ${capitalize(report.animal_info.breed)}
                </div>
                <div class="info-badge">
                    <strong>Sex:</strong> ${capitalize(report.animal_info.sex)}
                </div>
                <div class="info-badge">
                    <strong>Grade:</strong> ${report.overall_grade}
                </div>
            `;
        }

        // Structural scores
        const structuralScores = document.getElementById('structuralScores');
        if (structuralScores) {
            structuralScores.innerHTML = report.scores.structural.map(score => `
                <div class="score-item">
                    <span class="score-name">${score.trait_name}</span>
                    <div class="score-value">
                        ${score.score !== null ? `<span class="score-number">${score.score}</span>` : '<span class="text-muted">N/A</span>'}
                    </div>
                </div>
            `).join('');
        }

        // Udder scores
        const udderScores = document.getElementById('udderScores');
        if (udderScores) {
            const udderData = report.scores.udder || [];
            if (udderData.length > 0) {
                udderScores.innerHTML = udderData.map(score => `
                    <div class="score-item">
                        <span class="score-name">${score.trait_name}</span>
                        <div class="score-value">
                            ${score.score !== null ? `<span class="score-number">${score.score}</span>` : '<span class="text-muted">N/A</span>'}
                        </div>
                    </div>
                `).join('');
            } else {
                udderScores.innerHTML = '<p class="text-muted">No udder traits assessed</p>';
            }
        }

        // Composite scores
        const compositeScores = document.getElementById('compositeScores');
        if (compositeScores && report.composites) {
            compositeScores.innerHTML = `
                <div class="composite-item">
                    <div class="composite-label">Structural</div>
                    <div class="composite-value">${report.composites.structural_composite || '-'}</div>
                </div>
                <div class="composite-item">
                    <div class="composite-label">Udder</div>
                    <div class="composite-value">${report.composites.udder_composite || '-'}</div>
                </div>
                <div class="composite-item">
                    <div class="composite-label">Final</div>
                    <div class="composite-value">${report.composites.final_composite || '-'}</div>
                </div>
            `;
        }

        // Assessment
        const assessmentSection = document.getElementById('assessmentSection');
        if (assessmentSection) {
            let html = `<h3 class="section-title">Assessment</h3>`;
            html += `<p>${report.assessment || 'No assessment available.'}</p>`;
            
            if (report.recommendations && report.recommendations.length > 0) {
                html += `<h4>Recommendations</h4><ul>`;
                report.recommendations.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                html += `</ul>`;
            }
            
            assessmentSection.innerHTML = html;
        }
    }

    // ========== Export & BPA ==========

    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            if (!currentReportId) return;

            try {
                const response = await fetch(`/export/${currentReportId}`);
                const data = await response.json();

                // Download as JSON
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `atc_report_${currentReportId}.json`;
                a.click();
                URL.revokeObjectURL(url);
            } catch (error) {
                alert('Export failed: ' + error.message);
            }
        });
    }

    const bpaBtn = document.getElementById('bpaBtn');
    if (bpaBtn) {
        bpaBtn.addEventListener('click', async () => {
            if (!currentReportId) return;

            try {
                const response = await fetch(`/submit-bpa/${currentReportId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });

                const result = await response.json();
                alert(result.message);
            } catch (error) {
                alert('BPA submission failed: ' + error.message);
            }
        });
    }

    // ========== Utilities ==========

    function capitalize(str) {
        if (!str) return 'Unknown';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }
});
