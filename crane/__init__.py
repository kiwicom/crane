settings = {}  # filled with CLI options at launch

import requests
rancher = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=3)
rancher.mount('http://', _adapter)
rancher.mount('https://', _adapter)
