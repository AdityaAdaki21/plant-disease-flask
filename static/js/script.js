// DOM Elements
const fileInput = document.getElementById('fileInput');
const imagePreview = document.getElementById('imagePreview');
const submitBtn = document.getElementById('submitBtn');
const result = document.getElementById('result');
const predictedDisease = document.getElementById('predictedDisease');
const recommendedPesticide = document.getElementById('recommendedPesticide');
const detailedInfo = document.getElementById('detailedInfo');

// Image preview functionality
fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
});

// Drag and drop functionality
const dropZone = document.querySelector('.file-input-container');
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.backgroundColor = '#f0f0f0';
});
dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.style.backgroundColor = '';
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.backgroundColor = '';
    
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    }
});

// Form submission
submitBtn.addEventListener('click', async function() {
    const plantType = document.getElementById('plantType').value;
    if (!fileInput.files[0]) {
        alert('Please upload an image first.');
        return;
    }
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('plant_type', plantType);
    try {
        // Update button state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Analyzing...';
        
        // Hide previous results
        result.classList.remove('result-visible');
        const response = await fetch('classify', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            throw new Error('Server response was not ok');
        }
        const data = await response.json();
        
        // Update results
        predictedDisease.textContent = data.predicted_class;
        recommendedPesticide.textContent = data.recommended_pesticide;
        detailedInfo.textContent = data.detailed_info;
        result.classList.add('result-visible');
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while analyzing the image. Please try again.');
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.textContent = 'Analyze Plant';
    }
});