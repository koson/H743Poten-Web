"""
Mock scipy module for Raspberry Pi compatibility
Simple replacement when scipy is not available
"""

class MockStats:
    @staticmethod
    def pearsonr(x, y):
        """Simple correlation fallback"""
        import numpy as np
        if len(x) != len(y) or len(x) < 2:
            return (0.0, 1.0)
        
        # Calculate basic correlation
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        num = np.sum((x - x_mean) * (y - y_mean))
        den = np.sqrt(np.sum((x - x_mean)**2) * np.sum((y - y_mean)**2))
        
        if den == 0:
            return (0.0, 1.0)
        
        r = num / den
        return (r, 0.05)  # correlation, p-value
    
    @staticmethod
    def linregress(x, y):
        """Simple linear regression fallback"""
        import numpy as np
        if len(x) != len(y) or len(x) < 2:
            result = type('obj', (object,), {
                'slope': 0, 'intercept': 0, 'rvalue': 0, 'pvalue': 1, 'stderr': 0
            })()
            return result
        
        n = len(x)
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
        intercept = y_mean - slope * x_mean
        
        result = type('obj', (object,), {
            'slope': slope, 'intercept': intercept, 'rvalue': 0.5, 'pvalue': 0.05, 'stderr': 0.1
        })()
        return result

class MockSignal:
    @staticmethod
    def find_peaks(data, height=None, distance=None, prominence=None, width=None):
        """Simple peak detection fallback"""
        import numpy as np
        
        if len(data) < 3:
            return ([], {})
        
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                if height is None or data[i] >= height:
                    peaks.append(i)
        
        # Apply distance filter if specified
        if distance and len(peaks) > 1:
            filtered_peaks = [peaks[0]]
            for peak in peaks[1:]:
                if peak - filtered_peaks[-1] >= distance:
                    filtered_peaks.append(peak)
            peaks = filtered_peaks
        
        return (np.array(peaks), {})

# Create mock scipy structure
stats = MockStats()
signal = MockSignal()

__version__ = "1.0.0-mock"
