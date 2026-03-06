import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_check_job_status():
    with patch("generaltranslation.translate._check_job_status.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = [{"jobId": "j1", "status": "completed"}]
        from generaltranslation.translate._check_job_status import check_job_status
        result = await check_job_status(["j1"], {"project_id": "p"})
        assert result[0]["status"] == "completed"
        mock.assert_called_once()
        call_args = mock.call_args
        assert call_args[0][1] == "/v2/project/jobs/info"

@pytest.mark.asyncio
async def test_setup_project():
    with patch("generaltranslation.translate._setup_project.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"setupJobId": "s1", "status": "queued"}
        from generaltranslation.translate._setup_project import setup_project
        files = [{"branch_id": "b1", "file_id": "f1", "version_id": "v1"}]
        result = await setup_project(files, {"project_id": "p"})
        assert result["status"] == "queued"
        call_body = mock.call_args[1]["body"]
        assert call_body["files"][0]["branchId"] == "b1"

@pytest.mark.asyncio
async def test_query_branch_data():
    with patch("generaltranslation.translate._query_branch_data.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"branches": [{"id": "b1", "name": "main"}]}
        from generaltranslation.translate._query_branch_data import query_branch_data
        result = await query_branch_data({"branchNames": ["main"]}, {"project_id": "p"})
        assert result["branches"][0]["name"] == "main"

@pytest.mark.asyncio
async def test_create_branch():
    with patch("generaltranslation.translate._create_branch.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"branch": {"id": "b1", "name": "feature"}}
        from generaltranslation.translate._create_branch import create_branch
        result = await create_branch({"branchName": "feature", "defaultBranch": False}, {"project_id": "p"})
        assert result["branch"]["name"] == "feature"

@pytest.mark.asyncio
async def test_query_source_file():
    with patch("generaltranslation.translate._query_source_file.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"sourceFile": {"fileId": "f1"}, "translations": []}
        from generaltranslation.translate._query_source_file import query_source_file
        result = await query_source_file(
            {"file_id": "f1", "branch_id": "b1", "version_id": "v1"},
            {},
            {"project_id": "p"},
        )
        assert result["sourceFile"]["fileId"] == "f1"
        call_args = mock.call_args
        assert "/v2/project/translations/files/status/f1" in call_args[0][1]

@pytest.mark.asyncio
async def test_get_project_data():
    with patch("generaltranslation.translate._get_project_data.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "p1", "name": "My Project", "defaultLocale": "en"}
        from generaltranslation.translate._get_project_data import get_project_data
        result = await get_project_data("p1", {}, {"project_id": "p"})
        assert result["name"] == "My Project"
        call_args = mock.call_args
        assert "p1" in call_args[0][1]

@pytest.mark.asyncio
async def test_submit_user_edit_diffs():
    with patch("generaltranslation.translate._submit_user_edit_diffs.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {}
        from generaltranslation.translate._submit_user_edit_diffs import submit_user_edit_diffs
        result = await submit_user_edit_diffs({"diffs": [{"locale": "es"}]}, {"project_id": "p"})
        assert result["success"] is True

@pytest.mark.asyncio
async def test_process_file_moves_empty():
    from generaltranslation.translate._process_file_moves import process_file_moves
    result = await process_file_moves([], {}, {"project_id": "p"})
    assert result["summary"]["total"] == 0
    assert result["results"] == []

@pytest.mark.asyncio
async def test_get_orphaned_files_empty():
    with patch("generaltranslation.translate._get_orphaned_files.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"orphanedFiles": []}
        from generaltranslation.translate._get_orphaned_files import get_orphaned_files
        result = await get_orphaned_files("b1", [], {}, {"project_id": "p"})
        assert result["orphanedFiles"] == []


# --- Fix 1: enqueue_files should not send None values in body ---

@pytest.mark.asyncio
async def test_enqueue_files_omits_none_values():
    """Body dict passed to api_request must not contain keys whose value is None."""
    with patch("generaltranslation.translate._enqueue_files.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"jobData": {"j1": "queued"}}
        from generaltranslation.translate._enqueue_files import enqueue_files
        files = [{"branch_id": "b1", "file_id": "f1", "version_id": "v1", "file_name": "a.txt"}]
        options = {
            "target_locales": ["es"],
            "source_locale": "en",
            # publish, requireApproval, modelProvider, force are all absent → None
        }
        await enqueue_files(files, options, {"project_id": "p"})
        body = mock.call_args[1]["body"]
        # None-valued keys must be absent
        for key in ("publish", "requireApproval", "modelProvider", "force"):
            assert key not in body, f"key '{key}' should not be in body when value is None"


# --- Fix 4: URL encoding should match JS encodeURIComponent ---

@pytest.mark.asyncio
async def test_query_source_file_preserves_special_chars():
    """Characters !  ' ( ) * should NOT be percent-encoded (matching encodeURIComponent)."""
    with patch("generaltranslation.translate._query_source_file.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"sourceFile": {}}
        from generaltranslation.translate._query_source_file import query_source_file
        await query_source_file(
            {"file_id": "file!'()*"},
            {},
            {"project_id": "p"},
        )
        endpoint = mock.call_args[0][1]
        assert "file!'()*" in endpoint, f"Special chars were percent-encoded in: {endpoint}"


@pytest.mark.asyncio
async def test_get_project_data_preserves_special_chars():
    """Characters ! ' ( ) * should NOT be percent-encoded (matching encodeURIComponent)."""
    with patch("generaltranslation.translate._get_project_data.api_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "p!'()*"}
        from generaltranslation.translate._get_project_data import get_project_data
        await get_project_data("p!'()*", {}, {"project_id": "p"})
        endpoint = mock.call_args[0][1]
        assert "p!'()*" in endpoint, f"Special chars were percent-encoded in: {endpoint}"
