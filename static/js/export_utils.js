// Flag to prevent multiple simultaneous exports
let isExporting = false;

// Function to export graph data as CSV
function exportGraphData() {
    // Prevent multiple simultaneous exports
    if (isExporting) {
        console.log('Export already in progress');
        return;
    }
    
    isExporting = true;
    fetch('/api/workflow_api/get-graph-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.data && data.data.voltage && data.data.current) {
                // Verify data arrays are same length
                if (data.data.voltage.length !== data.data.current.length) {
                    throw new Error('Voltage and current data arrays have different lengths');
                }
                
                // Create CSV content with filename as first line
                let csvContent = `FileName: ${data.data.fileName}\n`;
                csvContent += "Voltage (V),Current (μA)\n";
                
                for (let i = 0; i < data.data.voltage.length; i++) {
                    csvContent += `${data.data.voltage[i]},${data.data.current[i]}\n`;
                }

                // Create blob and download
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.setAttribute("href", url);
                link.setAttribute("download", `cv_data_${new Date().toISOString().slice(0,19)}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);  // Clean up
            } else {
                console.error('Invalid data format:', data);
                if (data.error) {
                    alert(`Failed to fetch graph data: ${data.error}`);
                } else {
                    alert('Failed to fetch graph data: Invalid data format');
                }
            }
        })
        .catch(error => {
            console.error('Error exporting data:', error);
            alert(`Error exporting data: ${error.message}`);
        })
        .finally(() => {
            // Reset export flag
            isExporting = false;
        });
}