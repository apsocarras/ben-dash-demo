import yaml 
import os 
from utils.AzureStorageManager import AzureBlobStorageManager


with open(os.path.join('creds', 'api_info.yaml'), 'r') as file:  
    creds = yaml.full_load(file)

download_dir = 'example_data'

if not os.path.exists(download_dir): 
    print(f'Creating directory {download_dir}/ to store downloads.')

azure_manager = AzureBlobStorageManager(connection_str=creds['azure']['conn-str'], 
                                        container_name=creds['container-name-2'],
                                        download_dir=download_dir)
blob_list = azure_manager.list_blobs()

expected_blobs = ["all-counties_three-profile_example.csv",
"DASH_exports_combined_New-Castle-County_30-adult_5-child_2-child_EDU+CODES.csv",
"GetSkills_Response.json",
"SubmitSkills_example_request.json",
"SubmitSkills_example_response.json", 
"counties.json"]

for blob_name in expected_blobs: 
    if blob_name not in blob_list: 
        print(f'Warning: file {blob_name} expected but not found in azure container {creds["container-name-2"]}')
        print("Container contains: " + "; ".join(blob_list))
    else: 
        if not os.path.isfile(os.path.join('example_data', blob_name)):
            print(f"Downloading {blob_name} to {download_dir}/")
            azure_manager.download_blob(blob_name)
        else: 
            print(f"{blob_name} already downloaded to {download_dir}. Skipping.")