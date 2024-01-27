import requests
import os
import zipfile
import re
import tarfile

def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def download_file(url, filename, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print(f"{filename} has been downloaded to {target_dir}")
    return file_path

def unzip_and_rename_nuclei(zip_path, target_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
        for file in zip_ref.namelist():
            if file.endswith('/'):  # Skip directories
                continue
            if 'nuclei' in file:  # Adjust the condition as per your requirement
                old_file = os.path.join(target_dir, file)
                new_file = os.path.join(target_dir, 'nuclei')
                os.rename(old_file, new_file)
                print(f"Renamed {file} to nuclei")

def unzip_and_rename_subfinder(zip_path, target_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
        for file in zip_ref.namelist():
            if file.endswith('/'):  # Skip directories
                continue
            if 'nuclei' in file:  # Adjust the condition as per your requirement
                old_file = os.path.join(target_dir, file)
                new_file = os.path.join(target_dir, 'subfinder')
                os.rename(old_file, new_file)
                print(f"Renamed {file} to subfinder")

def extract_tgz(tgz_path, target_dir):
    with tarfile.open(tgz_path, 'r:gz') as tar:
        tar.extractall(path=target_dir)
    print(f"Extracted {tgz_path} to {target_dir}")

def check_and_download(repo, asset_name_pattern, target_dir, post_process=None):
    release_data = get_latest_release(repo)
    version = release_data['tag_name']

    for asset in release_data['assets']:
        if re.search(asset_name_pattern, asset['name']):
            download_url = asset['browser_download_url']
            filename = os.path.basename(download_url)
            local_version_file = os.path.join(target_dir, f"{repo.split('/')[1]}.version")

            if os.path.exists(local_version_file):
                with open(local_version_file, 'r') as file:
                    current_version = file.read().strip()
                if current_version == version:
                    print(f"No new version for {filename}. Current version: {version}")
                    return
            file_path = download_file(download_url, filename, target_dir)

            if post_process:
                post_process(file_path, target_dir)

            with open(local_version_file, 'w') as file:
                file.write(version)
            print(f"Updated {filename} to version {version} in {target_dir}")

def main():
    repositories = [
        {"repo": "Stratus-Security/Subdominator", "asset_name_pattern": "Subdominator$", "target_dir": "./thirdparty/subdominator"},
        {"repo": "projectdiscovery/nuclei", "asset_name_pattern": "nuclei_.*_linux_amd64.zip", "target_dir": "./thirdparty/nuclei", "post_process": unzip_and_rename_nuclei},
        {"repo": "d3mondev/puredns", "asset_name_pattern": "puredns-Linux-amd64.tgz", "target_dir": "./thirdparty/puredns", "post_process": extract_tgz},
        {"repo": "projectdiscovery/subfinder", "asset_name_pattern": "subfinder_.*_linux_amd64.zip", "target_dir": "./thirdparty/subfinder", "post_process": unzip_and_rename_subfinder},
        ]

    for repository in repositories:
        check_and_download(repository['repo'], repository['asset_name_pattern'], repository['target_dir'], repository.get('post_process'))

if __name__ == "__main__":
    main()
