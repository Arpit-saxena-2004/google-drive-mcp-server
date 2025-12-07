from fastmcp import FastMCP
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os.path
import pickle
import sys
import io

# Full access to Google Drive (read, write, delete)
SCOPES = [
    "https://www.googleapis.com/auth/drive",  # Full access
    "https://www.googleapis.com/auth/drive.file"  # Access to files created by this app
]

mcp = FastMCP("google-drive-connector")

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.pickle")


def get_drive():
    try:
        print("Starting authentication process...", file=sys.stderr)
        creds = None
        
        # Check if credentials.json exists
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"ERROR: credentials.json not found at {CREDENTIALS_FILE}!", file=sys.stderr)
            raise FileNotFoundError(f"credentials.json not found at {CREDENTIALS_FILE}")
        
        print(f"credentials.json found at {CREDENTIALS_FILE}", file=sys.stderr)
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists(TOKEN_FILE):
            print("Loading existing token...", file=sys.stderr)
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired token...", file=sys.stderr)
                creds.refresh(Request())
            else:
                print("Starting OAuth flow...", file=sys.stderr)
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("OAuth flow completed", file=sys.stderr)
            
            # Save the credentials for the next run
            print("Saving token...", file=sys.stderr)
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
        
        print("Building Drive service...", file=sys.stderr)
        service = build("drive", "v3", credentials=creds)
        print("Drive service ready!", file=sys.stderr)
        return service
        
    except Exception as e:
        print(f"ERROR in get_drive: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def list_drive_files(max_results: int = 10, query: str = "") -> list[dict]:
    """
    List files from Google Drive.
    
    Args:
        max_results: Maximum number of files to return (default 10)
        query: Search query (e.g., "name contains 'report'" or "mimeType='application/pdf'")
    """
    try:
        service = get_drive()
        params = {
            'pageSize': max_results,
            'fields': 'files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)'
        }
        if query:
            params['q'] = query
            
        results = service.files().list(**params).execute()
        files = results.get('files', [])
        print(f"Found {len(files)} files", file=sys.stderr)
        return files
    except Exception as e:
        print(f"ERROR in list_drive_files: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def search_drive_files(search_term: str, max_results: int = 10) -> list[dict]:
    """
    Search for files in Google Drive by name.
    
    Args:
        search_term: The term to search for in file names
        max_results: Maximum number of results to return
    """
    try:
        service = get_drive()
        query = f"name contains '{search_term}'"
        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields='files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)'
        ).execute()
        files = results.get('files', [])
        print(f"Found {len(files)} files matching '{search_term}'", file=sys.stderr)
        return files
    except Exception as e:
        print(f"ERROR in search_drive_files: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def create_folder(folder_name: str, parent_folder_id: str = None) -> dict:
    """
    Create a new folder in Google Drive.
    
    Args:
        folder_name: Name of the folder to create
        parent_folder_id: ID of parent folder (optional, creates in root if not specified)
    """
    try:
        service = get_drive()
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
            
        folder = service.files().create(body=file_metadata, fields='id, name, webViewLink').execute()
        print(f"Created folder: {folder.get('name')}", file=sys.stderr)
        return folder
    except Exception as e:
        print(f"ERROR in create_folder: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def upload_file(file_path: str, file_name: str = None, parent_folder_id: str = None) -> dict:
    """
    Upload a file to Google Drive.
    
    Args:
        file_path: Local path to the file to upload
        file_name: Name for the file in Drive (uses original name if not specified)
        parent_folder_id: ID of parent folder (optional, uploads to root if not specified)
    """
    try:
        service = get_drive()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_metadata = {
            'name': file_name or os.path.basename(file_path)
        }
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        print(f"Uploaded file: {file.get('name')}", file=sys.stderr)
        return file
    except Exception as e:
        print(f"ERROR in upload_file: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def delete_file(file_id: str) -> dict:
    """
    Delete a file from Google Drive.
    
    Args:
        file_id: ID of the file to delete
    """
    try:
        service = get_drive()
        service.files().delete(fileId=file_id).execute()
        print(f"Deleted file with ID: {file_id}", file=sys.stderr)
        return {"success": True, "message": f"File {file_id} deleted successfully"}
    except Exception as e:
        print(f"ERROR in delete_file: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def download_file(file_id: str, destination_path: str) -> dict:
    """
    Download a file from Google Drive.
    
    Args:
        file_id: ID of the file to download
        destination_path: Local path where the file should be saved
    """
    try:
        service = get_drive()
        request = service.files().get_media(fileId=file_id)
        
        fh = io.FileIO(destination_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%", file=sys.stderr)
        
        print(f"Downloaded file to: {destination_path}", file=sys.stderr)
        return {"success": True, "path": destination_path}
    except Exception as e:
        print(f"ERROR in download_file: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def rename_file(file_id: str, new_name: str) -> dict:
    """
    Rename a file in Google Drive.
    
    Args:
        file_id: ID of the file to rename
        new_name: New name for the file
    """
    try:
        service = get_drive()
        file = service.files().update(
            fileId=file_id,
            body={'name': new_name},
            fields='id, name, webViewLink'
        ).execute()
        print(f"Renamed file to: {file.get('name')}", file=sys.stderr)
        return file
    except Exception as e:
        print(f"ERROR in rename_file: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def move_file(file_id: str, new_parent_folder_id: str) -> dict:
    """
    Move a file to a different folder in Google Drive.
    
    Args:
        file_id: ID of the file to move
        new_parent_folder_id: ID of the destination folder
    """
    try:
        service = get_drive()
        # Get current parents
        file = service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))
        
        # Move the file
        file = service.files().update(
            fileId=file_id,
            addParents=new_parent_folder_id,
            removeParents=previous_parents,
            fields='id, name, parents, webViewLink'
        ).execute()
        
        print(f"Moved file to new folder", file=sys.stderr)
        return file
    except Exception as e:
        print(f"ERROR in move_file: {str(e)}", file=sys.stderr)
        raise


@mcp.tool
def get_file_info(file_id: str) -> dict:
    """
    Get detailed information about a file.
    
    Args:
        file_id: ID of the file
    """
    try:
        service = get_drive()
        file = service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink, owners, permissions'
        ).execute()
        return file
    except Exception as e:
        print(f"ERROR in get_file_info: {str(e)}", file=sys.stderr)
        raise


if __name__ == "__main__":
    print(f"Starting MCP server... Script dir: {SCRIPT_DIR}", file=sys.stderr)
    mcp.run()