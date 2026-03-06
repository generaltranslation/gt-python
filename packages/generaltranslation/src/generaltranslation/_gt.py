"""Main GT class."""

from __future__ import annotations

import os
from typing import Any

from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE
from generaltranslation.errors import (
    invalid_locale_error,
    invalid_locales_error,
    no_api_key_error,
    no_project_id_error,
    no_source_locale_error,
    no_target_locale_error,
)
from generaltranslation.formatting import (
    format_currency,
    format_cutoff,
    format_date_time,
    format_list,
    format_list_to_parts,
    format_message,
    format_num,
    format_relative_time,
)
from generaltranslation.locales import (
    CustomMapping,
    CustomRegionMapping,
    determine_locale,
    get_locale_direction,
    get_locale_emoji,
    get_locale_name,
    get_locale_properties,
    get_region_properties,
    is_same_dialect,
    is_same_language,
    is_superset_locale,
    is_valid_locale,
    requires_translation,
    resolve_alias_locale,
    resolve_canonical_locale,
    standardize_locale,
)
from generaltranslation.translate import (
    check_job_status as _check_job_status,
)
from generaltranslation.translate import (
    create_branch as _create_branch,
)
from generaltranslation.translate import (
    download_file_batch as _download_file_batch,
)
from generaltranslation.translate import (
    enqueue_files as _enqueue_files,
)
from generaltranslation.translate import (
    get_orphaned_files as _get_orphaned_files,
)
from generaltranslation.translate import (
    get_project_data as _get_project_data,
)
from generaltranslation.translate import (
    process_file_moves as _process_file_moves,
)
from generaltranslation.translate import (
    query_branch_data as _query_branch_data,
)
from generaltranslation.translate import (
    query_file_data as _query_file_data,
)
from generaltranslation.translate import (
    query_source_file as _query_source_file,
)
from generaltranslation.translate import (
    setup_project as _setup_project,
)
from generaltranslation.translate import (
    submit_user_edit_diffs as _submit_user_edit_diffs,
)
from generaltranslation.translate import (
    translate_many as _translate_many,
)
from generaltranslation.translate import (
    upload_source_files as _upload_source_files,
)
from generaltranslation.translate import (
    upload_translations as _upload_translations,
)


class GT:
    """General Translation core driver class.

    A comprehensive toolkit for handling internationalisation and localisation.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        dev_api_key: str | None = None,
        project_id: str | None = None,
        base_url: str | None = None,
        source_locale: str | None = None,
        target_locale: str | None = None,
        locales: list[str] | None = None,
        custom_mapping: CustomMapping | None = None,
    ) -> None:
        # Read environment variables first
        self.api_key: str | None = api_key or os.environ.get("GT_API_KEY") or None
        self.dev_api_key: str | None = dev_api_key or os.environ.get("GT_DEV_API_KEY") or None
        self.project_id: str | None = project_id or os.environ.get("GT_PROJECT_ID") or None

        self.base_url: str | None = None
        self.source_locale: str | None = None
        self.target_locale: str | None = None
        self.locales: list[str] | None = None
        self.custom_mapping: CustomMapping | None = None
        self.reverse_custom_mapping: dict[str, str] | None = None
        self.custom_region_mapping: CustomRegionMapping | None = None
        self._rendering_locales: list[str] = []

        self.set_config(
            api_key=api_key,
            dev_api_key=dev_api_key,
            project_id=project_id,
            base_url=base_url,
            source_locale=source_locale,
            target_locale=target_locale,
            locales=locales,
            custom_mapping=custom_mapping,
        )

    def set_config(
        self,
        *,
        api_key: str | None = None,
        dev_api_key: str | None = None,
        project_id: str | None = None,
        base_url: str | None = None,
        source_locale: str | None = None,
        target_locale: str | None = None,
        locales: list[str] | None = None,
        custom_mapping: CustomMapping | None = None,
    ) -> None:
        """Update instance configuration."""
        if api_key:
            self.api_key = api_key
        if dev_api_key:
            self.dev_api_key = dev_api_key
        if project_id:
            self.project_id = project_id

        # Standardise locales
        if source_locale:
            self.source_locale = standardize_locale(source_locale)
            if not is_valid_locale(self.source_locale, custom_mapping):
                raise ValueError(invalid_locale_error(self.source_locale))

        if target_locale:
            self.target_locale = standardize_locale(target_locale)
            if not is_valid_locale(self.target_locale, custom_mapping):
                raise ValueError(invalid_locale_error(self.target_locale))

        # Rendering locales
        self._rendering_locales = []
        if self.source_locale:
            self._rendering_locales.append(self.source_locale)
        if self.target_locale:
            self._rendering_locales.append(self.target_locale)
        self._rendering_locales.append(LIBRARY_DEFAULT_LOCALE)

        # Validate locales list
        if locales is not None:
            result: list[str] = []
            invalid: list[str] = []
            for loc in locales:
                std = standardize_locale(loc)
                if is_valid_locale(std):
                    result.append(std)
                else:
                    invalid.append(loc)
            if invalid:
                raise ValueError(invalid_locales_error(invalid))
            self.locales = result

        if base_url:
            self.base_url = base_url
        if custom_mapping:
            self.custom_mapping = custom_mapping
            self.reverse_custom_mapping = {
                v["code"]: k for k, v in custom_mapping.items() if v and isinstance(v, dict) and "code" in v
            }

    # -------------- Private Methods -------------- #

    def _get_translation_config(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "api_key": self.api_key or self.dev_api_key or "",
            "project_id": self.project_id or "",
        }

    def _validate_auth(self, fn_name: str) -> None:
        errors: list[str] = []
        if not self.api_key and not self.dev_api_key:
            errors.append(no_api_key_error(fn_name))
        if not self.project_id:
            errors.append(no_project_id_error(fn_name))
        if errors:
            raise ValueError("\n".join(errors))

    # -------------- Branch Methods -------------- #

    async def query_branch_data(self, query: dict[str, Any]) -> dict[str, Any]:
        """Query branch information from the API."""
        self._validate_auth("query_branch_data")
        return await _query_branch_data(query, self._get_translation_config())

    async def create_branch(self, query: dict[str, Any]) -> dict[str, Any]:
        """Create a new branch in the API."""
        self._validate_auth("create_branch")
        return await _create_branch(query, self._get_translation_config())

    async def process_file_moves(
        self,
        moves: list[dict[str, Any]],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process file moves by cloning source files and translations."""
        self._validate_auth("process_file_moves")
        return await _process_file_moves(moves, options or {}, self._get_translation_config())

    async def get_orphaned_files(
        self,
        branch_id: str,
        file_ids: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get orphaned files for a branch."""
        self._validate_auth("get_orphaned_files")
        return await _get_orphaned_files(branch_id, file_ids, options or {}, self._get_translation_config())

    # -------------- Translation Methods -------------- #

    async def setup_project(
        self,
        files: list[dict[str, Any]],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Enqueue files for project setup."""
        self._validate_auth("setup_project")
        opts = dict(options) if options else {}
        if opts.get("locales"):
            opts["locales"] = [self.resolve_canonical_locale(loc) for loc in opts["locales"]]
        return await _setup_project(files, self._get_translation_config(), opts)

    async def check_job_status(
        self,
        job_ids: list[str],
        timeout_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        """Check job statuses."""
        self._validate_auth("check_job_status")
        return await _check_job_status(job_ids, self._get_translation_config(), timeout_ms)

    async def enqueue_files(
        self,
        files: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Enqueue translation jobs for previously uploaded source files."""
        self._validate_auth("enqueue_files")
        merged = dict(options)
        merged.setdefault("source_locale", self.source_locale)
        merged.setdefault("sourceLocale", self.source_locale)
        if not merged.get("target_locales") and not merged.get("targetLocales"):
            if self.target_locale:
                merged["target_locales"] = [self.target_locale]

        src = merged.get("source_locale") or merged.get("sourceLocale")
        if not src:
            raise ValueError(no_source_locale_error("enqueue_files"))
        tgts = merged.get("target_locales") or merged.get("targetLocales") or []
        if not tgts:
            raise ValueError(no_target_locale_error("enqueue_files"))

        # Resolve canonical locales
        resolved_targets = [self.resolve_canonical_locale(loc) for loc in tgts]
        merged["target_locales"] = resolved_targets
        merged["targetLocales"] = resolved_targets

        return await _enqueue_files(files, merged, self._get_translation_config())

    async def submit_user_edit_diffs(self, payload: dict[str, Any]) -> None:
        """Submit user edit diffs."""
        self._validate_auth("submit_user_edit_diffs")
        normalized = dict(payload)
        if normalized.get("diffs"):
            normalized["diffs"] = [
                {**d, "locale": self.resolve_canonical_locale(d.get("locale"))} for d in normalized["diffs"]
            ]
        await _submit_user_edit_diffs(normalized, self._get_translation_config())

    async def query_file_data(
        self,
        data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query data about one or more source or translation files."""
        self._validate_auth("query_file_data")
        data = dict(data)
        tf_key = "translated_files" if "translated_files" in data else "translatedFiles"
        if data.get(tf_key):
            data[tf_key] = [
                {**item, "locale": self.resolve_canonical_locale(item.get("locale"))} for item in data[tf_key]
            ]

        result = await _query_file_data(data, options or {}, self._get_translation_config())

        # Resolve alias locales in response
        if result.get("translatedFiles"):
            result["translatedFiles"] = [
                {
                    **item,
                    **({"locale": self.resolve_alias_locale(item["locale"])} if item.get("locale") else {}),
                }
                for item in result["translatedFiles"]
            ]
        if result.get("sourceFiles"):
            result["sourceFiles"] = [
                {
                    **item,
                    **(
                        {"sourceLocale": self.resolve_alias_locale(item["sourceLocale"])}
                        if item.get("sourceLocale")
                        else {}
                    ),
                    "locales": [self.resolve_alias_locale(loc) for loc in item.get("locales", [])],
                }
                for item in result["sourceFiles"]
            ]
        return result

    async def query_source_file(
        self,
        data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get source file and translation information."""
        self._validate_auth("query_source_file")
        result = await _query_source_file(data, options or {}, self._get_translation_config())
        if result.get("translations"):
            result["translations"] = [
                {
                    **item,
                    **({"locale": self.resolve_alias_locale(item["locale"])} if item.get("locale") else {}),
                }
                for item in result["translations"]
            ]
        sf = result.get("sourceFile", {})
        if sf.get("locales"):
            sf["locales"] = [self.resolve_alias_locale(loc) for loc in sf["locales"]]
        if sf.get("sourceLocale"):
            sf["sourceLocale"] = self.resolve_alias_locale(sf["sourceLocale"])
        return result

    async def get_project_data(
        self,
        project_id: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get project data for a given project ID."""
        self._validate_auth("get_project_data")
        result = await _get_project_data(project_id, options or {}, self._get_translation_config())
        if result.get("currentLocales"):
            result["currentLocales"] = [self.resolve_alias_locale(loc) for loc in result["currentLocales"]]
        if result.get("defaultLocale"):
            result["defaultLocale"] = self.resolve_alias_locale(result["defaultLocale"])
        return result

    async def download_file(
        self,
        file: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> str:
        """Download a single file."""
        self._validate_auth("download_file")
        request = {
            "fileId": file.get("file_id", file.get("fileId", "")),
            "branchId": file.get("branch_id", file.get("branchId")),
            "locale": self.resolve_canonical_locale(file.get("locale")),
            "versionId": file.get("version_id", file.get("versionId")),
        }
        result = await _download_file_batch([request], options or {}, self._get_translation_config())
        return result["data"][0]["data"]

    async def download_file_batch(
        self,
        requests: list[dict[str, Any]],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Download multiple files in a batch."""
        self._validate_auth("download_file_batch")
        mapped_requests = [{**r, "locale": self.resolve_canonical_locale(r.get("locale"))} for r in requests]
        result = await _download_file_batch(mapped_requests, options or {}, self._get_translation_config())
        files = [
            {
                **f,
                **({"locale": self.resolve_alias_locale(f["locale"])} if f.get("locale") else {}),
            }
            for f in result["data"]
        ]
        return {"files": files, "count": result["count"]}

    async def translate(
        self,
        source: Any,
        options: str | dict[str, Any],
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Translate a single source string."""
        if isinstance(options, str):
            options = {"target_locale": options}
        self._validate_auth("translate")

        target_locale = options.get("target_locale") or options.get("targetLocale") or self.target_locale
        if not target_locale:
            raise ValueError(no_target_locale_error("translate"))
        target_locale = self.resolve_canonical_locale(target_locale)

        source_locale = self.resolve_canonical_locale(
            options.get("source_locale") or options.get("sourceLocale") or self.source_locale or LIBRARY_DEFAULT_LOCALE
        )

        results = await _translate_many(
            [source],
            {**options, "target_locale": target_locale, "source_locale": source_locale},
            self._get_translation_config(),
            timeout,
        )
        assert isinstance(results, list)
        return results[0]

    async def translate_many(
        self,
        sources: list[Any] | dict[str, Any],
        options: str | dict[str, Any],
        timeout: int | None = None,
    ) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
        """Translate multiple source strings."""
        if isinstance(options, str):
            options = {"target_locale": options}
        self._validate_auth("translate_many")

        target_locale = options.get("target_locale") or options.get("targetLocale") or self.target_locale
        if not target_locale:
            raise ValueError(no_target_locale_error("translate_many"))
        target_locale = self.resolve_canonical_locale(target_locale)

        source_locale = self.resolve_canonical_locale(
            options.get("source_locale") or options.get("sourceLocale") or self.source_locale or LIBRARY_DEFAULT_LOCALE
        )

        return await _translate_many(
            sources,
            {**options, "target_locale": target_locale, "source_locale": source_locale},
            self._get_translation_config(),
            timeout,
        )

    async def upload_source_files(
        self,
        files: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Upload source files to the translation service."""
        self._validate_auth("upload_source_files")
        merged = dict(options)
        merged["source_locale"] = self.resolve_canonical_locale(
            options.get("source_locale") or options.get("sourceLocale") or self.source_locale or LIBRARY_DEFAULT_LOCALE
        )
        mapped_files = [
            {
                **f,
                "source": {
                    **f["source"],
                    "locale": self.resolve_canonical_locale(f["source"].get("locale")),
                },
            }
            for f in files
        ]
        result = await _upload_source_files(mapped_files, merged, self._get_translation_config())
        return {
            "uploadedFiles": result["data"],
            "count": result["count"],
            "message": f"Successfully uploaded {result['count']} files in {result['batch_count']} batch(es)",
        }

    async def upload_translations(
        self,
        files: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Upload translation files."""
        self._validate_auth("upload_translations")
        merged = dict(options)
        merged.setdefault("source_locale", self.source_locale)
        if not merged.get("source_locale"):
            raise ValueError(no_source_locale_error("upload_translations"))

        mapped_files = [
            {
                **f,
                "translations": [
                    {**t, "locale": self.resolve_canonical_locale(t.get("locale"))} for t in f.get("translations", [])
                ],
            }
            for f in files
        ]
        result = await _upload_translations(mapped_files, merged, self._get_translation_config())
        return {
            "uploadedFiles": result["data"],
            "count": result["count"],
            "message": f"Successfully uploaded {result['count']} files in {result['batch_count']} batch(es)",
        }

    # -------------- Formatting -------------- #

    def format_cutoff(
        self,
        value: str,
        *,
        locales: str | list[str] | None = None,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Format a string with cutoff behaviour."""
        opts = dict(options or {})
        opts.update(kwargs)
        return format_cutoff(value, locales=locales or self._rendering_locales, options=opts)

    def format_message(
        self,
        message: str,
        *,
        locales: str | list[str] | None = None,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """Format a message with variables."""
        return format_message(
            message,
            locales=locales or self._rendering_locales,
            variables=variables,
        )

    def format_num(self, number: float | int, **kwargs: Any) -> str:
        """Format a number."""
        kwargs.setdefault("locales", self._rendering_locales)
        return format_num(number, **kwargs)

    def format_date_time(self, date: Any, **kwargs: Any) -> str:
        """Format a datetime."""
        kwargs.setdefault("locales", self._rendering_locales)
        return format_date_time(date, **kwargs)

    def format_currency(self, value: float | int, currency: str, **kwargs: Any) -> str:
        """Format a currency value."""
        kwargs.setdefault("locales", self._rendering_locales)
        return format_currency(value, currency, **kwargs)

    def format_list(self, array: list[Any], **kwargs: Any) -> str:
        """Format a list of items."""
        kwargs.setdefault("locales", self._rendering_locales)
        return format_list(array, **kwargs)

    def format_list_to_parts(self, array: list[Any], **kwargs: Any) -> list[Any]:
        """Format a list of items to parts."""
        kwargs.setdefault("locales", self._rendering_locales)
        return format_list_to_parts(array, **kwargs)

    def format_relative_time(self, value: float | int, unit: str, **kwargs: Any) -> str:
        """Format a relative time value."""
        kwargs.setdefault("locales", self._rendering_locales)
        return format_relative_time(value, unit, **kwargs)

    # -------------- Locale Properties -------------- #

    def get_locale_name(self, locale: str | None = None) -> str:
        """Get the display name of a locale code."""
        locale = locale or self.target_locale
        if not locale:
            raise ValueError(no_target_locale_error("get_locale_name"))
        return get_locale_name(locale, self.source_locale, self.custom_mapping)

    def get_locale_emoji(self, locale: str | None = None) -> str:
        """Get emoji for a locale."""
        locale = locale or self.target_locale
        if not locale:
            raise ValueError(no_target_locale_error("get_locale_emoji"))
        return get_locale_emoji(locale, self.custom_mapping)

    def get_locale_properties(self, locale: str | None = None) -> Any:
        """Get detailed locale properties."""
        locale = locale or self.target_locale
        if not locale:
            raise ValueError(no_target_locale_error("get_locale_properties"))
        return get_locale_properties(locale, self.source_locale, self.custom_mapping)

    def get_region_properties(
        self,
        region: str | None = None,
        custom_mapping: CustomRegionMapping | None = None,
    ) -> dict[str, str]:
        """Get region properties."""
        if region is None:
            region = self.get_locale_properties().get("region_code", "")
        if custom_mapping is None:
            if self.custom_mapping and not self.custom_region_mapping:
                crm: CustomRegionMapping = {}
                for loc, lp in self.custom_mapping.items():
                    if lp and isinstance(lp, dict) and lp.get("regionCode") and lp["regionCode"] not in crm:
                        entry: dict[str, Any] = {"locale": loc}
                        if lp.get("regionName"):
                            entry["name"] = lp["regionName"]
                        if lp.get("emoji"):
                            entry["emoji"] = lp["emoji"]
                        crm[lp["regionCode"]] = entry
                self.custom_region_mapping = crm
            custom_mapping = self.custom_region_mapping
        return get_region_properties(region, self.target_locale, custom_mapping)

    def requires_translation(
        self,
        source_locale: str | None = None,
        target_locale: str | None = None,
        approved_locales: list[str] | None = None,
        custom_mapping: CustomMapping | None = None,
    ) -> bool:
        """Check if translation is required."""
        source_locale = source_locale or self.source_locale
        target_locale = target_locale or self.target_locale
        if approved_locales is None:
            approved_locales = self.locales
        if custom_mapping is None:
            custom_mapping = self.custom_mapping
        if not source_locale:
            raise ValueError(no_source_locale_error("requires_translation"))
        if not target_locale:
            raise ValueError(no_target_locale_error("requires_translation"))
        return requires_translation(source_locale, target_locale, approved_locales, custom_mapping)

    def determine_locale(
        self,
        locales: str | list[str],
        approved_locales: list[str] | None = None,
        custom_mapping: CustomMapping | None = None,
    ) -> str | None:
        """Determine the best matching locale."""
        if approved_locales is None:
            approved_locales = self.locales or []
        if custom_mapping is None:
            custom_mapping = self.custom_mapping
        return determine_locale(locales, approved_locales, custom_mapping)

    def get_locale_direction(self, locale: str | None = None) -> str:
        """Get text direction for a locale."""
        locale = locale or self.target_locale
        if not locale:
            raise ValueError(no_target_locale_error("get_locale_direction"))
        return get_locale_direction(locale)

    def is_valid_locale(
        self,
        locale: str | None = None,
        custom_mapping: CustomMapping | None = None,
    ) -> bool:
        """Check if a locale code is valid."""
        locale = locale or self.target_locale
        if custom_mapping is None:
            custom_mapping = self.custom_mapping
        if not locale:
            raise ValueError(no_target_locale_error("is_valid_locale"))
        return is_valid_locale(locale, custom_mapping)

    def resolve_canonical_locale(
        self,
        locale: str | None = None,
        custom_mapping: CustomMapping | None = None,
    ) -> str:
        """Resolve the canonical locale for a given locale."""
        locale = locale or self.target_locale
        if custom_mapping is None:
            custom_mapping = self.custom_mapping
        if not locale:
            raise ValueError(no_target_locale_error("resolve_canonical_locale"))
        return resolve_canonical_locale(locale, custom_mapping)

    def resolve_alias_locale(
        self,
        locale: str,
        custom_mapping: CustomMapping | None = None,
    ) -> str:
        """Resolve the alias locale for a given locale."""
        if custom_mapping is None:
            custom_mapping = self.custom_mapping
        if not locale:
            raise ValueError(no_target_locale_error("resolve_alias_locale"))
        return resolve_alias_locale(locale, custom_mapping)

    def standardize_locale(self, locale: str | None = None) -> str:
        """Standardise a BCP 47 locale code."""
        locale = locale or self.target_locale
        if not locale:
            raise ValueError(no_target_locale_error("standardize_locale"))
        return standardize_locale(locale)

    def is_same_dialect(self, *locales: str | list[str]) -> bool:
        """Check if locale codes represent the same dialect."""
        return is_same_dialect(*locales)

    def is_same_language(self, *locales: str | list[str]) -> bool:
        """Check if locale codes represent the same language."""
        return is_same_language(*locales)

    def is_superset_locale(self, super_locale: str, sub_locale: str) -> bool:
        """Check if a locale is a superset of another locale."""
        return is_superset_locale(super_locale, sub_locale)
