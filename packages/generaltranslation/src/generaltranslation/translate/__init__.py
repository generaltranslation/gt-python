"""Translation API communication layer."""

from generaltranslation.translate._batch import create_batches, process_batches
from generaltranslation.translate._check_job_status import check_job_status
from generaltranslation.translate._create_branch import create_branch
from generaltranslation.translate._download_file_batch import download_file_batch
from generaltranslation.translate._enqueue_files import enqueue_files
from generaltranslation.translate._get_orphaned_files import get_orphaned_files
from generaltranslation.translate._get_project_data import get_project_data
from generaltranslation.translate._headers import generate_request_headers
from generaltranslation.translate._process_file_moves import process_file_moves
from generaltranslation.translate._query_branch_data import query_branch_data
from generaltranslation.translate._query_file_data import query_file_data
from generaltranslation.translate._query_source_file import query_source_file
from generaltranslation.translate._request import api_request
from generaltranslation.translate._setup_project import setup_project
from generaltranslation.translate._submit_user_edit_diffs import submit_user_edit_diffs
from generaltranslation.translate._translate import translate_many
from generaltranslation.translate._upload_source_files import upload_source_files
from generaltranslation.translate._upload_translations import upload_translations

__all__ = [
    "api_request",
    "check_job_status",
    "create_batches",
    "create_branch",
    "download_file_batch",
    "enqueue_files",
    "generate_request_headers",
    "get_orphaned_files",
    "get_project_data",
    "process_batches",
    "process_file_moves",
    "query_branch_data",
    "query_file_data",
    "query_source_file",
    "setup_project",
    "submit_user_edit_diffs",
    "translate_many",
    "upload_source_files",
    "upload_translations",
]
