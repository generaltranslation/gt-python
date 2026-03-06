"""TypedDicts for all translate request/response shapes."""

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict


# --- Config ---

class TranslationRequestConfig(TypedDict, total=False):
    project_id: str
    base_url: str
    api_key: str


# --- File types ---

FileFormat = Literal["GTJSON", "JSON", "YAML", "MDX", "MD", "TS", "JS", "HTML", "TXT"]
DataFormat = Literal["JSX", "ICU", "I18NEXT", "STRING"]


class FileReference(TypedDict, total=False):
    file_id: str
    version_id: str
    branch_id: str
    file_name: str
    file_format: FileFormat
    data_format: DataFormat


class FileUpload(TypedDict, total=False):
    branch_id: str
    incoming_branch_id: str
    checked_out_branch_id: str
    content: str
    file_name: str
    file_format: FileFormat
    data_format: DataFormat
    locale: str
    format_metadata: dict[str, Any]
    version_id: str
    file_id: str


# --- Translate ---

ActionType = Literal["fast"]


class EntryMetadata(TypedDict, total=False):
    id: str
    hash: str
    context: str
    max_chars: int
    data_format: DataFormat
    action_type: ActionType


class TranslateOptions(TypedDict, total=False):
    target_locale: str
    source_locale: str
    model_provider: str


class TranslationResult(TypedDict, total=False):
    success: bool
    translation: Any
    locale: str
    error: str
    code: int
    reference: dict[str, str]


class TranslationError(TypedDict):
    success: bool
    error: str
    code: int


# --- Batch ---

class BatchList(TypedDict):
    data: list[Any]
    count: int
    batch_count: int


# --- Enqueue ---

class EnqueueOptions(TypedDict, total=False):
    source_locale: str
    target_locales: list[str]
    publish: bool
    require_approval: bool
    model_provider: str
    force: bool
    timeout: int


class EnqueueFilesResult(TypedDict, total=False):
    job_data: dict[str, Any]
    locales: list[str]
    message: str


# --- Setup ---

class SetupProjectOptions(TypedDict, total=False):
    force: bool
    locales: list[str]
    timeout_ms: int


class SetupProjectResult(TypedDict, total=False):
    setup_job_id: str
    status: str


# --- Job Status ---

JobStatus = Literal["queued", "processing", "completed", "failed", "unknown"]


class JobStatusEntry(TypedDict, total=False):
    job_id: str
    status: JobStatus
    error: dict[str, str]


CheckJobStatusResult = list[JobStatusEntry]


# --- Branch ---

class BranchQuery(TypedDict):
    branch_names: list[str]


class BranchInfo(TypedDict):
    id: str
    name: str


class BranchDataResult(TypedDict, total=False):
    branches: list[BranchInfo]
    default_branch: Optional[BranchInfo]


class CreateBranchQuery(TypedDict):
    branch_name: str
    default_branch: bool


class CreateBranchResult(TypedDict):
    branch: BranchInfo


# --- File Data ---

class FileDataQuery(TypedDict, total=False):
    source_files: list[dict[str, str]]
    translated_files: list[dict[str, str]]


class FileDataResult(TypedDict, total=False):
    source_files: list[dict[str, Any]]
    translated_files: list[dict[str, Any]]


class FileQuery(TypedDict, total=False):
    file_id: str
    branch_id: str
    version_id: str


class FileQueryResult(TypedDict, total=False):
    source_file: dict[str, Any]
    translations: list[dict[str, Any]]


class CheckFileTranslationsOptions(TypedDict, total=False):
    timeout: int


# --- Download ---

class DownloadFileBatchOptions(TypedDict, total=False):
    timeout: int


class DownloadedFile(TypedDict, total=False):
    id: str
    branch_id: str
    file_id: str
    version_id: str
    locale: str
    file_name: str
    data: str
    metadata: dict[str, Any]
    file_format: FileFormat


class DownloadFileBatchResult(TypedDict):
    files: list[DownloadedFile]
    count: int


# --- Upload ---

class UploadFilesOptions(TypedDict, total=False):
    source_locale: str
    model_provider: str
    timeout: int


class UploadFilesResponse(TypedDict, total=False):
    uploaded_files: list[FileReference]
    count: int
    message: str


# --- Orphaned Files ---

class OrphanedFile(TypedDict):
    file_id: str
    version_id: str
    file_name: str


class GetOrphanedFilesResult(TypedDict):
    orphaned_files: list[OrphanedFile]


# --- Process Moves ---

class MoveMapping(TypedDict):
    old_file_id: str
    new_file_id: str
    new_file_name: str


class MoveResult(TypedDict, total=False):
    old_file_id: str
    new_file_id: str
    success: bool
    new_source_file_id: str
    cloned_translations_count: int
    error: str


class ProcessMovesResponse(TypedDict):
    results: list[MoveResult]
    summary: dict[str, int]


class ProcessMovesOptions(TypedDict, total=False):
    timeout: int
    branch_id: str


# --- Submit User Edit Diffs ---

class SubmitUserEditDiff(TypedDict):
    file_name: str
    locale: str
    diff: str
    branch_id: str
    version_id: str
    file_id: str
    local_content: str


class SubmitUserEditDiffsPayload(TypedDict):
    diffs: list[SubmitUserEditDiff]


# --- Project Data ---

class ProjectData(TypedDict):
    id: str
    name: str
    org_id: str
    default_locale: str
    current_locales: list[str]
