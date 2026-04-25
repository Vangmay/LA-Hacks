import sys
sys.path.append('.')
from core.job_store import job_store
print("Exists:", job_store.exists('b44c7df7-c70e-41f5-a9cb-8696df969ec5'))
