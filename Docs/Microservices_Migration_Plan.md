# Microservices Migration Implementation Plan

**Document Version:** 1.0  
**Date:** October 1, 2025  
**Parent Document:** Architecture_Analysis_2025.md  

---

## 🎯 Migration Strategy Overview

This document outlines the detailed implementation plan for migrating from Monolithic to Microservices architecture, with specific timelines, technical specifications, and risk mitigation strategies.

---

## 📅 Detailed Implementation Timeline

### 🚀 Phase 1: Foundation & Infrastructure (Weeks 1-8)

#### Week 1-2: Project Setup & Service Registry
**Objectives:**
- Create new branch structure
- Implement basic service registry
- Set up development environment

**Tasks:**
```bash
# Branch Strategy
git checkout -b feature/microservices-migration
git checkout -b foundation/service-registry
git checkout -b foundation/api-gateway
git checkout -b foundation/docker-setup
```

**Deliverables:**
```python
# service_registry.py
class ServiceRegistry:
    def __init__(self):
        self.services = {}
        self.health_status = {}
    
    def register_service(self, name: str, config: dict):
        self.services[name] = {
            'url': config['url'],
            'health_endpoint': config['health'],
            'version': config['version'],
            'status': 'unknown'
        }
    
    def get_service(self, name: str) -> dict:
        return self.services.get(name)
    
    def health_check_all(self) -> dict:
        # Implementation for service health monitoring
        pass
```

#### Week 3-4: API Gateway Development
**Objectives:**
- Central request routing
- Authentication layer
- Rate limiting
- Request/response logging

**Technical Specifications:**
```python
# api_gateway.py
from flask import Flask, request, jsonify, g
import requests
import time
from functools import wraps

class APIGateway:
    def __init__(self):
        self.app = Flask(__name__)
        self.service_registry = ServiceRegistry()
        self.rate_limiter = RateLimiter()
        self.setup_middleware()
        self.setup_routes()
    
    def rate_limit(self, requests_per_minute=60):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                client_id = request.remote_addr
                if not self.rate_limiter.allow_request(client_id, requests_per_minute):
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    @app.route('/api/<service>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @rate_limit(100)  # 100 requests per minute
    def proxy_request(self, service, endpoint):
        # Service discovery
        service_config = self.service_registry.get_service(service)
        if not service_config:
            return jsonify({'error': f'Service {service} not found'}), 404
        
        # Health check before routing
        if service_config['status'] != 'healthy':
            return jsonify({'error': f'Service {service} unhealthy'}), 503
        
        # Forward request
        target_url = f"{service_config['url']}/api/{endpoint}"
        try:
            response = requests.request(
                method=request.method,
                url=target_url,
                json=request.get_json(),
                params=request.args,
                headers=self._filter_headers(request.headers),
                timeout=30
            )
            return response.json(), response.status_code
        except requests.RequestException as e:
            return jsonify({'error': f'Service communication failed: {str(e)}'}), 502
```

#### Week 5-6: Docker & Container Setup
**Objectives:**
- Containerize existing monolithic app
- Create service templates
- Set up docker-compose development environment

**Docker Configuration:**
```dockerfile
# Dockerfile.template (for each service)
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["python", "app.py"]
```

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  # Existing monolithic app (for comparison)
  monolithic-app:
    build: 
      context: .
      dockerfile: Dockerfile.monolithic
    ports:
      - "5000:5000"
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=development
      - DEBUG=true
    devices:
      - "/dev/ttyUSB0:/dev/ttyUSB0"
    
  # Service registry
  service-registry:
    build:
      context: ./services/registry
    ports:
      - "5001:5000"
    volumes:
      - ./services/registry:/app
    
  # API Gateway
  api-gateway:
    build:
      context: ./services/gateway
    ports:
      - "5002:5000"
    depends_on:
      - service-registry
    environment:
      - SERVICE_REGISTRY_URL=http://service-registry:5000
    volumes:
      - ./services/gateway:/app

networks:
  h743poten:
    driver: bridge
```

#### Week 7-8: Monitoring & Logging Infrastructure
**Objectives:**
- Centralized logging system
- Service health monitoring
- Performance metrics collection

**Implementation:**
```python
# monitoring.py
import logging
import time
from prometheus_client import Counter, Histogram, Gauge, start_http_server

class ServiceMonitor:
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Metrics
        self.request_count = Counter(
            'service_requests_total',
            'Total service requests',
            ['service', 'method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'service_request_duration_seconds',
            'Service request duration',
            ['service', 'method', 'endpoint']
        )
        
        self.active_connections = Gauge(
            'service_active_connections',
            'Active connections to service',
            ['service']
        )
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        self.request_count.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.request_duration.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint
        ).observe(duration)
```

---

### 🔧 Phase 2: Hardware Service Extraction (Weeks 9-16)

#### Week 9-10: Hardware Service Design
**Objectives:**
- Define hardware service API contract
- Implement connection management
- Create hardware abstraction layer

**Service API Contract:**
```yaml
# hardware_service_api.yaml
openapi: 3.0.0
info:
  title: H743Poten Hardware Service
  version: 1.0.0
paths:
  /api/hardware/connect:
    post:
      summary: Connect to H743 device
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                port:
                  type: string
                  example: "/dev/ttyUSB0"
                baud_rate:
                  type: integer
                  example: 115200
      responses:
        200:
          description: Connection successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  connection_id:
                    type: string
                  device_info:
                    type: object
        400:
          description: Connection failed
  
  /api/hardware/command:
    post:
      summary: Send SCPI command to device
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                connection_id:
                  type: string
                command:
                  type: string
                  example: "POTEn:CV:Start:ALL 0.0,1.0,-1.0,0.1,1"
                timeout:
                  type: integer
                  default: 30
      responses:
        200:
          description: Command executed successfully
        500:
          description: Hardware communication error
          
  /api/hardware/stream:
    get:
      summary: WebSocket endpoint for real-time data
      description: Establishes WebSocket connection for streaming measurement data
```

#### Week 11-12: Hardware Service Implementation
**Implementation:**
```python
# hardware_service/app.py
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import uuid
import threading
import time
from scpi_handler import SCPIHandler

class HardwareService:
    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.connections = {}  # connection_id -> SCPIHandler
        self.data_streams = {}  # connection_id -> threading.Thread
        self.setup_routes()
        self.setup_websocket_handlers()
    
    def setup_routes(self):
        @self.app.route('/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'service': 'hardware',
                'active_connections': len(self.connections),
                'timestamp': time.time()
            })
        
        @self.app.route('/api/hardware/connect', methods=['POST'])
        def connect_device():
            data = request.get_json()
            port = data.get('port')
            baud_rate = data.get('baud_rate', 115200)
            
            try:
                # Create new SCPI handler
                scpi_handler = SCPIHandler(port, baud_rate)
                success = scpi_handler.connect()
                
                if success:
                    connection_id = str(uuid.uuid4())
                    self.connections[connection_id] = scpi_handler
                    
                    # Get device information
                    device_info = scpi_handler.query("*IDN?")
                    
                    return jsonify({
                        'success': True,
                        'connection_id': connection_id,
                        'device_info': device_info,
                        'port': port,
                        'baud_rate': baud_rate
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to connect to device'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/hardware/command', methods=['POST'])
        def send_command():
            data = request.get_json()
            connection_id = data.get('connection_id')
            command = data.get('command')
            timeout = data.get('timeout', 30)
            
            if connection_id not in self.connections:
                return jsonify({
                    'success': False,
                    'error': 'Invalid connection ID'
                }), 400
            
            try:
                scpi_handler = self.connections[connection_id]
                result = scpi_handler.send_custom_command(command)
                
                # Start data streaming if it's a measurement command
                if any(cmd in command.lower() for cmd in ['start', 'begin']):
                    self._start_data_stream(connection_id)
                
                return jsonify(result)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def _start_data_stream(self, connection_id):
        """Start streaming measurement data via WebSocket"""
        if connection_id in self.data_streams:
            return  # Already streaming
        
        def stream_data():
            scpi_handler = self.connections[connection_id]
            while connection_id in self.connections:
                try:
                    data = scpi_handler.get_buffered_data()
                    if data:
                        self.socketio.emit('measurement_data', {
                            'connection_id': connection_id,
                            'data': data,
                            'timestamp': time.time()
                        })
                    time.sleep(0.1)  # 10Hz sampling
                except Exception as e:
                    self.socketio.emit('error', {
                        'connection_id': connection_id,
                        'error': str(e)
                    })
                    break
        
        thread = threading.Thread(target=stream_data, daemon=True)
        thread.start()
        self.data_streams[connection_id] = thread

if __name__ == '__main__':
    service = HardwareService()
    service.socketio.run(service.app, host='0.0.0.0', port=5000, debug=True)
```

#### Week 13-14: Integration Testing
**Test Implementation:**
```python
# tests/test_hardware_service.py
import unittest
import requests
import json
from unittest.mock import patch, MagicMock

class TestHardwareService(unittest.TestCase):
    def setUp(self):
        self.base_url = 'http://localhost:5001'
        self.headers = {'Content-Type': 'application/json'}
    
    def test_health_check(self):
        response = requests.get(f'{self.base_url}/health')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'hardware')
    
    @patch('hardware_service.SCPIHandler')
    def test_device_connection(self, mock_scpi):
        # Mock successful connection
        mock_handler = MagicMock()
        mock_handler.connect.return_value = True
        mock_handler.query.return_value = "H743Poten,v1.0"
        mock_scpi.return_value = mock_handler
        
        # Test connection
        payload = {
            'port': '/dev/ttyUSB0',
            'baud_rate': 115200
        }
        response = requests.post(
            f'{self.base_url}/api/hardware/connect',
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('connection_id', data)
        self.assertIn('device_info', data)
    
    def test_invalid_connection(self):
        payload = {
            'port': '/dev/nonexistent',
            'baud_rate': 115200
        }
        response = requests.post(
            f'{self.base_url}/api/hardware/connect',
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
```

#### Week 15-16: Performance Optimization
**Objectives:**
- Connection pooling
- Command queuing
- Error recovery mechanisms
- Load testing

---

### 📊 Phase 3: Measurement Services Extraction (Weeks 17-32)

#### Week 17-20: CV Service Migration
**CV Service Implementation:**
```python
# cv_service/app.py
from flask import Flask, request, jsonify
import requests
import threading
import time
from cv_measurement_logic import CVMeasurementLogic

class CVService:
    def __init__(self):
        self.app = Flask(__name__)
        self.hardware_service_url = os.getenv('HARDWARE_SERVICE_URL', 'http://localhost:5001')
        self.cv_logic = CVMeasurementLogic()
        self.active_measurements = {}
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'service': 'cv',
                'measurements': len(self.active_measurements)
            })
        
        @self.app.route('/api/cv/setup', methods=['POST'])
        def setup_measurement():
            data = request.get_json()
            params = data.get('params', {})
            connection_id = data.get('connection_id')
            
            # Validate parameters
            is_valid, message = self.cv_logic.validate_parameters(params)
            if not is_valid:
                return jsonify({'success': False, 'error': message}), 400
            
            # Store measurement configuration
            measurement_id = str(uuid.uuid4())
            self.active_measurements[measurement_id] = {
                'connection_id': connection_id,
                'params': params,
                'status': 'configured',
                'data': []
            }
            
            return jsonify({
                'success': True,
                'measurement_id': measurement_id
            })
        
        @self.app.route('/api/cv/start', methods=['POST'])
        def start_measurement():
            data = request.get_json()
            measurement_id = data.get('measurement_id')
            
            if measurement_id not in self.active_measurements:
                return jsonify({'success': False, 'error': 'Invalid measurement ID'}), 400
            
            measurement = self.active_measurements[measurement_id]
            
            # Generate SCPI command
            command = self.cv_logic.generate_scpi_command(measurement['params'])
            
            # Send command to hardware service
            try:
                response = requests.post(
                    f'{self.hardware_service_url}/api/hardware/command',
                    json={
                        'connection_id': measurement['connection_id'],
                        'command': command
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    measurement['status'] = 'running'
                    measurement['start_time'] = time.time()
                    
                    # Start data collection thread
                    self._start_data_collection(measurement_id)
                    
                    return jsonify({'success': True})
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Hardware command failed'
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
```

#### Week 21-24: DPV Service Migration
Similar implementation pattern as CV service but with DPV-specific logic.

#### Week 25-28: SWV Service Migration
Similar implementation pattern with SWV-specific parameters and processing.

#### Week 29-32: CA Service Migration
Final measurement service with CA-specific functionality.

---

### 🎨 Phase 4: Frontend & Data Services (Weeks 33-40)

#### Week 33-36: Data Service Implementation
**Objectives:**
- Centralized data storage
- Multiple export formats
- Data analysis endpoints
- Historical data management

#### Week 37-40: Frontend Modernization
**Objectives:**
- Convert to Single Page Application
- Real-time WebSocket communication
- Modern JavaScript framework (Vue.js/React)
- Responsive design improvements

---

## 🧪 Testing Strategy

### Unit Testing
```python
# Each service will have comprehensive unit tests
# Example: tests/cv_service/test_measurement_logic.py

class TestCVMeasurementLogic(unittest.TestCase):
    def setUp(self):
        self.cv_logic = CVMeasurementLogic()
    
    def test_parameter_validation(self):
        valid_params = {
            'begin': 0.0,
            'upper': 1.0,
            'lower': -1.0,
            'rate': 0.1,
            'cycles': 1
        }
        is_valid, message = self.cv_logic.validate_parameters(valid_params)
        self.assertTrue(is_valid)
    
    def test_scpi_command_generation(self):
        params = {'begin': 0.0, 'upper': 1.0, 'lower': -1.0, 'rate': 0.1, 'cycles': 1}
        command = self.cv_logic.generate_scpi_command(params)
        expected = "POTEn:CV:Start:ALL 0.0,1.0,-1.0,0.1,1"
        self.assertEqual(command, expected)
```

### Integration Testing
```python
# Test service-to-service communication
class TestServiceIntegration(unittest.TestCase):
    def test_cv_hardware_integration(self):
        # Test CV service -> Hardware service communication
        pass
    
    def test_api_gateway_routing(self):
        # Test API gateway routing to services
        pass
```

### Load Testing
```python
# locustfile.py
from locust import HttpUser, task, between

class H743PotenUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        # Connect to hardware service
        response = self.client.post("/api/hardware/connect", json={
            "port": "/dev/ttyUSB0",
            "baud_rate": 115200
        })
        self.connection_id = response.json().get("connection_id")
    
    @task(3)
    def setup_cv_measurement(self):
        self.client.post("/api/cv/setup", json={
            "connection_id": self.connection_id,
            "params": {
                "begin": 0.0,
                "upper": 1.0,
                "lower": -1.0,
                "rate": 0.1,
                "cycles": 1
            }
        })
    
    @task(1)
    def start_cv_measurement(self):
        # Start measurement
        pass
```

---

## 🔍 Monitoring & Observability

### Service Health Monitoring
```python
# health_monitor.py
import requests
import time
import logging
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ServiceHealth:
    name: str
    url: str
    status: str
    response_time: float
    last_check: float

class HealthMonitor:
    def __init__(self, services: Dict[str, str]):
        self.services = services
        self.health_status = {}
        self.logger = logging.getLogger(__name__)
    
    def check_all_services(self) -> Dict[str, ServiceHealth]:
        results = {}
        for name, url in self.services.items():
            results[name] = self.check_service(name, url)
        return results
    
    def check_service(self, name: str, url: str) -> ServiceHealth:
        start_time = time.time()
        try:
            response = requests.get(f"{url}/health", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = "healthy"
            else:
                status = "unhealthy"
                
        except Exception as e:
            response_time = time.time() - start_time
            status = "unreachable"
            self.logger.error(f"Service {name} health check failed: {e}")
        
        return ServiceHealth(
            name=name,
            url=url,
            status=status,
            response_time=response_time,
            last_check=time.time()
        )
```

### Logging Configuration
```yaml
# logging.yaml
version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    format: '{"timestamp": "%(asctime)s", "service": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: json
    filename: /app/logs/service.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  '':
    level: INFO
    handlers: [console, file]
```

---

## 🚨 Risk Mitigation Strategies

### Technical Risks
1. **Service Communication Failures**
   - **Risk:** Network latency, service downtime
   - **Mitigation:** Circuit breaker pattern, retry logic, fallback mechanisms

2. **Data Consistency Issues**
   - **Risk:** Distributed data synchronization
   - **Mitigation:** Event sourcing, eventual consistency, conflict resolution

3. **Performance Degradation**
   - **Risk:** Network overhead, increased complexity
   - **Mitigation:** Caching, connection pooling, performance monitoring

### Operational Risks
1. **Deployment Complexity**
   - **Risk:** Multiple service coordination
   - **Mitigation:** Docker orchestration, automated deployment pipelines

2. **Monitoring & Debugging**
   - **Risk:** Distributed system observability
   - **Mitigation:** Centralized logging, distributed tracing, comprehensive monitoring

---

## 📊 Success Criteria

### Technical KPIs
- [ ] Service independence: Each service deployable separately
- [ ] API response time: < 100ms (excluding measurement execution)
- [ ] System uptime: > 99.5%
- [ ] Error rate: < 1%
- [ ] Test coverage: > 80% per service

### Business KPIs
- [ ] Development velocity: 50% increase in feature delivery
- [ ] Deployment frequency: Multiple deploys per week
- [ ] Mean time to recovery: < 5 minutes
- [ ] Developer satisfaction: Improved development experience

---

## 📝 Next Steps

### Immediate Actions (This Week)
1. **Create Migration Branch**
   ```bash
   git checkout -b feature/microservices-migration
   git push -u origin feature/microservices-migration
   ```

2. **Set Up Project Structure**
   ```bash
   mkdir -p microservices/{api-gateway,hardware-service,cv-service,data-service}
   mkdir -p microservices/shared/{utils,schemas,testing}
   ```

3. **Create Initial Docker Setup**
   - Base Dockerfile template
   - docker-compose.dev.yml
   - Environment configuration

4. **Team Preparation**
   - Schedule architecture review meeting
   - Plan development team assignments
   - Set up development environment guidelines

### Following Weeks
1. **Week 1:** Start Phase 1 implementation
2. **Week 2:** Service registry development
3. **Week 3:** API gateway implementation
4. **Week 4:** Phase 1 testing and validation

---

**Document Status:** ✅ Ready for Implementation  
**Review Date:** October 8, 2025  
**Implementation Start:** October 8, 2025