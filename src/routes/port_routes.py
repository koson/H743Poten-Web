"""
Routes for port scanning and connection management
"""
from flask import Blueprint, jsonify
from hardware.port_scanner import get_available_ports, find_stm32_ports, test_port_connection

port_bp = Blueprint('ports', __name__)

@port_bp.route('/api/ports', methods=['GET'])
def list_ports():
    """Get list of available ports"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Port list requested")
    
    try:
        # Get all STM32 ports first
        logger.debug("Searching for STM32 ports...")
        stm32_ports = find_stm32_ports()
        logger.info(f"Found {len(stm32_ports) if stm32_ports else 0} STM32 ports")
        
        # If no STM32 ports found, return all available ports
        if not stm32_ports:
            logger.debug("No STM32 ports found, getting all available ports")
            all_ports = get_available_ports()
            logger.info(f"Found {len(all_ports)} total available ports")
            response = {
                'ports': [{'device': p['device'], 'description': p['description']} for p in all_ports],
                'status': 'success'
            }
            logger.debug(f"Returning port list: {response}")
            return jsonify(response)
            
        return jsonify({
            'ports': [{'device': p['device'], 'description': p['description']} for p in stm32_ports],
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@port_bp.route('/api/ports/test/<port>', methods=['GET'])
def test_port(port):
    """Test connection to specified port"""
    try:
        success = test_port_connection(port)
        return jsonify({
            'status': 'success' if success else 'error',
            'message': f'Port {port} {"is" if success else "is not"} available'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500
