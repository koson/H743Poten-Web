// Simple image loading fix for data browser
function loadPlotImage(sessionId, plotImgElement, plotLoadingElement) {
    const imgUrl = `/api/data-logging/sessions/${sessionId}/view/png?t=${Date.now()}`;
    console.log('🖼️ Loading plot image:', imgUrl);
    
    // Show loading
    plotLoadingElement.style.display = 'block';
    plotImgElement.style.display = 'none';
    
    // Simple timeout approach
    const timeout = setTimeout(() => {
        console.warn('⏰ Image load timeout');
        plotLoadingElement.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="fas fa-clock fa-2x mb-2 text-warning"></i><br>
                Loading timeout<br>
                <small>Please try refreshing the page</small>
            </div>
        `;
    }, 8000);
    
    plotImgElement.onload = () => {
        clearTimeout(timeout);
        console.log('✅ Image loaded');
        plotLoadingElement.style.display = 'none';
        plotImgElement.style.display = 'block';
    };
    
    plotImgElement.onerror = () => {
        clearTimeout(timeout);
        console.error('❌ Image failed');
        plotLoadingElement.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="fas fa-times-circle fa-2x mb-2 text-danger"></i><br>
                Image not available<br>
                <small>Please try again</small>
            </div>
        `;
    };
    
    // Set the source to start loading
    plotImgElement.src = imgUrl;
}

// Export for use in main script
window.loadPlotImage = loadPlotImage;