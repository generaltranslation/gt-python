"""Tests for the GT class."""

import pytest
from generaltranslation._gt import GT
from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE


class TestGTConstructor:
    def test_defaults(self):
        gt = GT()
        assert gt.source_locale is None
        assert gt.target_locale is None
        assert gt.base_url is None
        assert gt.api_key is None
        assert gt.project_id is None
        assert gt.locales is None
        assert LIBRARY_DEFAULT_LOCALE in gt._rendering_locales

    def test_explicit_params(self):
        gt = GT(
            api_key="key-123",
            dev_api_key="dev-456",
            project_id="proj-789",
            base_url="https://custom.api.com",
            source_locale="en-US",
            target_locale="es-ES",
        )
        assert gt.api_key == "key-123"
        assert gt.dev_api_key == "dev-456"
        assert gt.project_id == "proj-789"
        assert gt.base_url == "https://custom.api.com"
        assert gt.source_locale == "en-US"
        assert gt.target_locale == "es-ES"

    def test_env_vars(self, monkeypatch):
        monkeypatch.setenv("GT_API_KEY", "env-key")
        monkeypatch.setenv("GT_DEV_API_KEY", "env-dev-key")
        monkeypatch.setenv("GT_PROJECT_ID", "env-proj")
        gt = GT()
        assert gt.api_key == "env-key"
        assert gt.dev_api_key == "env-dev-key"
        assert gt.project_id == "env-proj"

    def test_explicit_overrides_env(self, monkeypatch):
        monkeypatch.setenv("GT_API_KEY", "env-key")
        gt = GT(api_key="explicit-key")
        assert gt.api_key == "explicit-key"

    def test_invalid_source_locale_raises(self):
        with pytest.raises(ValueError, match="Invalid locale"):
            GT(source_locale="not-a-locale-xxxx")

    def test_invalid_target_locale_raises(self):
        with pytest.raises(ValueError, match="Invalid locale"):
            GT(target_locale="not-a-locale-xxxx")

    def test_invalid_locales_raises(self):
        with pytest.raises(ValueError, match="Invalid locales"):
            GT(locales=["en", "not-valid-xxxx"])

    def test_valid_locales(self):
        gt = GT(locales=["en", "es", "fr"])
        assert gt.locales is not None
        assert len(gt.locales) == 3

    def test_rendering_locales(self):
        gt = GT(source_locale="en-US", target_locale="fr-FR")
        assert "en-US" in gt._rendering_locales
        assert "fr-FR" in gt._rendering_locales
        assert LIBRARY_DEFAULT_LOCALE in gt._rendering_locales

    def test_custom_mapping(self):
        mapping = {"my-locale": {"code": "en-US", "name": "My English"}}
        gt = GT(custom_mapping=mapping)
        assert gt.custom_mapping is not None
        assert gt.reverse_custom_mapping is not None
        assert gt.reverse_custom_mapping.get("en-US") == "my-locale"


class TestSetConfig:
    def test_update_api_key(self):
        gt = GT()
        gt.set_config(api_key="new-key")
        assert gt.api_key == "new-key"

    def test_update_source_locale(self):
        gt = GT()
        gt.set_config(source_locale="fr")
        assert gt.source_locale == "fr"

    def test_update_target_locale(self):
        gt = GT()
        gt.set_config(target_locale="de")
        assert gt.target_locale == "de"


class TestValidateAuth:
    def test_no_auth_raises(self):
        gt = GT()
        with pytest.raises(ValueError, match="API key"):
            gt._validate_auth("test_fn")

    def test_no_project_id_raises(self):
        gt = GT(api_key="key-123")
        with pytest.raises(ValueError, match="project ID"):
            gt._validate_auth("test_fn")

    def test_both_set_passes(self):
        gt = GT(api_key="key-123", project_id="proj-456")
        gt._validate_auth("test_fn")  # should not raise

    def test_dev_api_key_counts(self):
        gt = GT(dev_api_key="dev-key", project_id="proj-456")
        gt._validate_auth("test_fn")  # should not raise


class TestTranslationConfig:
    def test_config_with_api_key(self):
        gt = GT(api_key="key", project_id="proj", base_url="https://example.com")
        config = gt._get_translation_config()
        assert config["api_key"] == "key"
        assert config["project_id"] == "proj"
        assert config["base_url"] == "https://example.com"

    def test_config_with_dev_key(self):
        gt = GT(dev_api_key="dev-key", project_id="proj")
        config = gt._get_translation_config()
        assert config["api_key"] == "dev-key"

    def test_config_prefers_api_key(self):
        gt = GT(api_key="main", dev_api_key="dev", project_id="proj")
        config = gt._get_translation_config()
        assert config["api_key"] == "main"


class TestLocaleMethodsDelegation:
    """Test that locale methods properly delegate to standalone functions."""

    def test_get_locale_name(self):
        gt = GT(source_locale="en", target_locale="es")
        name = gt.get_locale_name("fr")
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_locale_name_default(self):
        gt = GT(target_locale="fr")
        name = gt.get_locale_name()
        assert isinstance(name, str)

    def test_get_locale_name_no_locale_raises(self):
        gt = GT()
        with pytest.raises(ValueError):
            gt.get_locale_name()

    def test_get_locale_emoji(self):
        gt = GT(target_locale="en-US")
        emoji = gt.get_locale_emoji()
        assert isinstance(emoji, str)

    def test_get_locale_direction(self):
        gt = GT(target_locale="ar")
        assert gt.get_locale_direction() == "rtl"
        gt2 = GT(target_locale="en")
        assert gt2.get_locale_direction() == "ltr"

    def test_is_valid_locale(self):
        gt = GT(target_locale="en")
        assert gt.is_valid_locale() is True

    def test_requires_translation(self):
        gt = GT(source_locale="en", target_locale="es")
        assert gt.requires_translation() is True

    def test_requires_translation_same(self):
        gt = GT(source_locale="en", target_locale="en")
        assert gt.requires_translation() is False

    def test_determine_locale(self):
        gt = GT(locales=["en", "fr", "es"])
        result = gt.determine_locale("fr-FR")
        assert result == "fr"

    def test_is_same_language(self):
        gt = GT()
        assert gt.is_same_language("en-US", "en-GB") is True

    def test_is_same_dialect(self):
        gt = GT()
        assert gt.is_same_dialect("en-US", "en-GB") is False

    def test_is_superset_locale(self):
        gt = GT()
        assert gt.is_superset_locale("en", "en-US") is True

    def test_standardize_locale(self):
        gt = GT(target_locale="en")
        result = gt.standardize_locale("EN-US")
        assert result == "en-US"

    def test_resolve_canonical_locale(self):
        gt = GT(target_locale="en")
        result = gt.resolve_canonical_locale("en")
        assert result == "en"

    def test_resolve_alias_locale(self):
        gt = GT()
        result = gt.resolve_alias_locale("en")
        assert result == "en"

    def test_get_locale_properties(self):
        gt = GT(target_locale="en-US")
        props = gt.get_locale_properties()
        assert props is not None


class TestFormattingDelegation:
    """Test formatting methods delegate correctly."""

    def test_format_num(self):
        gt = GT(source_locale="en-US")
        result = gt.format_num(1234.5)
        assert isinstance(result, str)
        assert "1" in result

    def test_format_message(self):
        gt = GT(source_locale="en")
        result = gt.format_message("Hello {name}", variables={"name": "World"})
        assert result == "Hello World"

    def test_format_cutoff(self):
        gt = GT(source_locale="en")
        result = gt.format_cutoff("Hello, world!", options={"max_chars": 5})
        assert isinstance(result, str)


class TestAPIMethodsAuth:
    """Test that API methods enforce auth."""

    @pytest.mark.asyncio
    async def test_translate_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError, match="API key"):
            await gt.translate("Hello", "es")

    @pytest.mark.asyncio
    async def test_translate_requires_target(self):
        gt = GT(api_key="key", project_id="proj")
        with pytest.raises(ValueError, match="locale"):
            await gt.translate("Hello", {})

    @pytest.mark.asyncio
    async def test_query_branch_data_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError):
            await gt.query_branch_data({"branchNames": ["main"]})

    @pytest.mark.asyncio
    async def test_setup_project_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError):
            await gt.setup_project([])

    @pytest.mark.asyncio
    async def test_check_job_status_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError):
            await gt.check_job_status(["job-1"])

    @pytest.mark.asyncio
    async def test_enqueue_files_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError):
            await gt.enqueue_files([], {"target_locales": ["es"]})

    @pytest.mark.asyncio
    async def test_upload_source_files_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError):
            await gt.upload_source_files([], {"source_locale": "en"})

    @pytest.mark.asyncio
    async def test_download_file_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError):
            await gt.download_file({"file_id": "f1"})

    @pytest.mark.asyncio
    async def test_get_project_data_requires_auth(self):
        gt = GT()
        with pytest.raises(ValueError):
            await gt.get_project_data("proj-1")
