// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    const imageUpload = document.getElementById('imageUpload');
    const preview = document.getElementById('preview');
    const classifyBtn = document.getElementById('classifyBtn');
    const results = document.getElementById('results');
    const predictedClass = document.getElementById('predictedClass');
    const recommendedPesticide = document.getElementById('recommendedPesticide');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const languageSelect = document.getElementById('language');

    // Translations object (same as the Python version)
    const TRANSLATIONS = {
        "Upload": "अपलोड करा",
        "Select": "निवडा",
        // ... (rest of the translations)
    };

    function translateText(text) {
        return languageSelect.value === 'Marathi' ? TRANSLATIONS[text] || text : text;
    }

    // Handle image upload and preview
    imageUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            }
            reader.readAsDataURL(file);
        }
    });

    // Handle classification
    classifyBtn.addEventListener('click', async function() {
        const file = imageUpload.files[0];
        if (!file) {
            alert('Please select an image first');
            return;
        }

        const formData = new FormData();
        formData.append('image', file);
        formData.append('plant_type', document.getElementById('plantType').value);

        try {
            const response = await fetch('/classify', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            // Update results
            results.classList.remove('hidden');
            predictedClass.textContent = translateText(data.predicted_class);
            recommendedPesticide.textContent = translateText(data.pesticide);

            // Update tab contents
            updateDetailedInfo(data.plant_info);
            updateCommercialProducts(data.commercial_products);
            updateAdditionalArticles(data.additional_articles);
        } catch (error) {
            alert('Error during classification: ' + error.message);
        }
    });

    // Tab handling
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Language handling
    languageSelect.addEventListener('change', function() {
        updatePageLanguage();
    });

    function updatePageLanguage() {
        // Update all translatable elements
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.dataset.translate;
            element.textContent = translateText(key);
        });
    }

    function updateDetailedInfo(info) {
        const detailedInfo = document.getElementById('detailedInfo');
        detailedInfo.innerHTML = info.detailed_info ? 
            `<div class="info-content">${translateText(info.detailed_info)}</div>` :
            '<div class="no-info">Detailed information is not available at the moment.</div>';
    }

    // static/js/script.js (continued)

    function updateCommercialProducts(products) {
        const productsContainer = document.getElementById('commercialProducts');
        if (!products || products.length === 0) {
            productsContainer.innerHTML = '<div class="no-info">No commercial product details available.</div>';
            return;
        }

        const productsHTML = products.map(product => `
            <div class="product-card">
                <h4>${translateText(product.title)}</h4>
                <p>${translateText(product.snippet)}</p>
                ${product.link ? `<a href="${product.link}" target="_blank" class="read-more">${translateText('Read More')}</a>` : ''}
            </div>
        `).join('');

        productsContainer.innerHTML = productsHTML;
    }

    function updateAdditionalArticles(articles) {
        const articlesContainer = document.getElementById('moreArticles');
        if (!articles || articles.length === 0) {
            articlesContainer.innerHTML = '<div class="no-info">No additional articles available.</div>';
            return;
        }

        const articlesHTML = articles.map(article => `
            <div class="article-card">
                <h4>${translateText(article.title)}</h4>
                <p>${translateText(article.snippet)}</p>
                ${article.link ? `<a href="${article.link}" target="_blank" class="read-more">${translateText('Read More')}</a>` : ''}
            </div>
        `).join('');

        articlesContainer.innerHTML = articlesHTML;
    }

    // Utility function to show loading state
    function showLoading(element) {
        element.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>${translateText('Loading...')}</p>
            </div>
        `;
    }

    // Utility function to handle errors
    function showError(element, message) {
        element.innerHTML = `
            <div class="error-message">
                <p>${translateText(message)}</p>
            </div>
        `;
    }

    // Function to validate image before upload
    function validateImage(file) {
        // Check file type
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            throw new Error('Please upload a valid image file (JPG or PNG)');
        }

        // Check file size (max 5MB)
        const maxSize = 5 * 1024 * 1024; // 5MB in bytes
        if (file.size > maxSize) {
            throw new Error('Image size should be less than 5MB');
        }

        return true;
    }

    // Initialize the page
    function initializePage() {
        // Set initial language
        updatePageLanguage();

        // Add loading spinner CSS
        const style = document.createElement('style');
        style.textContent = `
            .loading-spinner {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 2rem;
            }

            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .error-message {
                color: #dc3545;
                padding: 1rem;
                border: 1px solid #dc3545;
                border-radius: var(--border-radius);
                margin: 1rem 0;
            }

            .product-card,
            .article-card {
                background-color: white;
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: var(--border-radius);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            .read-more {
                display: inline-block;
                margin-top: 0.5rem;
                color: var(--primary-color);
                text-decoration: none;
                font-weight: 500;
            }

            .read-more:hover {
                text-decoration: underline;
            }

            .no-info {
                text-align: center;
                padding: 2rem;
                color: #666;
            }
        `;
        document.head.appendChild(style);
    }

    // Enhanced classify button click handler
    classifyBtn.addEventListener('click', async function() {
        const file = imageUpload.files[0];
        if (!file) {
            alert(translateText('Please select an image first'));
            return;
        }

        try {
            validateImage(file);
            showLoading(results);
            results.classList.remove('hidden');

            const formData = new FormData();
            formData.append('image', file);
            formData.append('plant_type', document.getElementById('plantType').value);

            const response = await fetch('/classify', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            // Update all results sections
            predictedClass.textContent = translateText(data.predicted_class);
            recommendedPesticide.textContent = translateText(data.pesticide);

            // Show first tab by default
            tabBtns[0].click();

            // Update all tab contents
            updateDetailedInfo(data.plant_info);
            updateCommercialProducts(data.commercial_products);
            updateAdditionalArticles(data.additional_articles);

        } catch (error) {
            showError(results, error.message);
        }
    });

    // Initialize the page when DOM is loaded
    initializePage();
});