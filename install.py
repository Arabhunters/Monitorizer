import sys
import requests
import os
import zipfile
import re
import tarfile
import stat


def get_latest_release(repo):
    """Get the latest release data from GitHub API for a given repository."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 403:
            raise  # Re-raise the exception if it's not a rate limit issue
        print(f"Rate limit exceeded for {repo}. Exiting script.")
        sys.exit(1)  # Exit the script with a non-zero exit code to indicate an error
def download_file(url, filename, target_dir):
    """Download a file from a URL to a target directory."""
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)

    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    print(f"{filename} has been downloaded to {target_dir}")
    return file_path

def set_executable_permission(file_path):
    """Set executable permission for the given file."""
    # Get the current permissions of the file
    current_permissions = os.stat(file_path).st_mode
    # Add the executable permission for the owner, group, and others
    os.chmod(file_path, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def extract_zip(zip_path, target_dir, new_name=None):
    """Extract a zip file to a target directory and optionally rename the extracted file."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
        if new_name:
            for file in zip_ref.namelist():
                if file.endswith('/') or new_name not in file:
                    continue
                old_file = os.path.join(target_dir, file)
                new_file = os.path.join(target_dir, new_name)
                os.rename(old_file, new_file)
                set_executable_permission(new_file)
                print(f"Renamed {file} to {new_name} and set it as executable.")

def extract_tgz(tgz_path, target_dir, new_name=None):
    """Extract a .tgz file to a target directory and optionally rename the extracted file."""
    with tarfile.open(tgz_path, 'r:gz') as tar:
        tar.extractall(path=target_dir)
        if new_name:
            for member in tar.getmembers():
                if member.isfile():
                    old_file = os.path.join(target_dir, member.name)
                    new_file = os.path.join(target_dir, new_name)
                    os.rename(old_file, new_file)
                    set_executable_permission(new_file)
                    print(f"Renamed {member.name} to {new_name} and set it as executable.")
        else:
            # If no renaming is necessary, just set the files as executable
            for member in tar.getmembers():
                if member.isfile():
                    file_path = os.path.join(target_dir, member.name)
                    set_executable_permission(file_path)
    print(f"Extracted {tgz_path} to {target_dir}{f' and renamed to {new_name}' if new_name else ''}.")


def check_and_download(repo, asset_name_pattern, target_dir, post_process=None, rename_to=None):
    """Check for the latest release and download it if it's new, then post-process if needed."""
    release_data = get_latest_release(repo)
    version = release_data['tag_name']
    local_version_file = os.path.join(target_dir, f"{repo.split('/')[1]}.version")

    if os.path.exists(local_version_file):
        with open(local_version_file, 'r') as file:
            if file.read().strip() == version:
                print(f"No new version for {repo}. Current version: {version}")
                return

    for asset in release_data['assets']:
        if re.search(asset_name_pattern, asset['name']):
            download_url = asset['browser_download_url']
            filename = os.path.basename(download_url)
            file_path = download_file(download_url, filename, target_dir)
            if post_process:
                post_process(file_path, target_dir, rename_to)
            with open(local_version_file, 'w') as file:
                file.write(version)
            print(f"Updated {filename} to version {version} in {target_dir}")

def main():
    repositories = [
        {"repo": "Stratus-Security/Subdominator", "asset_name_pattern": r"Subdominator$", "target_dir": "./thirdparty/subdominator"},
        {"repo": "projectdiscovery/nuclei", "asset_name_pattern": r"nuclei_.*_linux_amd64.zip", "target_dir": "./thirdparty/nuclei", "post_process": extract_zip, "rename_to": "nuclei"},
        {"repo": "d3mondev/puredns", "asset_name_pattern": r"puredns-Linux-amd64.tgz", "target_dir": "./thirdparty/puredns", "post_process": extract_tgz},
        {"repo": "projectdiscovery/subfinder", "asset_name_pattern": r"subfinder_.*_linux_amd64.zip", "target_dir": "./thirdparty/subfinder", "post_process": extract_zip, "rename_to": "subfinder"},
        ]

    for repository in repositories:
        try:
            check_and_download(**repository)
        except SystemExit as e:
            # Optionally, you can handle the SystemExit exception here if you need to perform any cleanup
            print("Exiting due to a rate limit error.")
            sys.exit(e.code)  # Exit with the same exit code used in get_latest_release

if __name__ == "__main__":
    main()
