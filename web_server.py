#!/usr/bin/env python3
"""
Web server runner for separate workflow execution
"""

import os
from main import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting @mraprguildbot web interface on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)