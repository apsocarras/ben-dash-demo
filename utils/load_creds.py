import yaml 
import os 

def load_creds() -> dict: 
    """Load credentials from YAML in ./creds/ as dict"""

    creds_path = os.path.join( 'creds', 'api_info.yaml')
    with open(creds_path, 'r') as file: 
        creds = yaml.safe_load(file)

    return creds
    