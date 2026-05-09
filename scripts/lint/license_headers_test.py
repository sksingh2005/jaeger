# Copyright (c) 2026 The Jaeger Authors.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pathlib
import tempfile
import unittest

import license_headers as lh


class LicenseHeadersTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._root = pathlib.Path(self._tmp_dir.name)
        self._orig_root = lh.ROOT
        lh.ROOT = self._root

    def tearDown(self) -> None:
        lh.ROOT = self._orig_root
        self._tmp_dir.cleanup()

    def _write_file(self, relative: str, content: str) -> pathlib.Path:
        path = self._root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_legacy_jaeger_copyright_is_recognized(self) -> None:
        file_path = self._write_file(
            "pkg/example.go",
            "\n".join(
                [
                    "// Copyright (c) 2019,2020 The Jaeger Authors",
                    "// SPDX-License-Identifier: Apache-2.0",
                    "",
                    "package example",
                    "",
                ]
            ),
        )

        changed = lh._update_file(file_path, check_only=True)

        self.assertFalse(changed)

    def test_fix_missing_spdx_without_duplicating_copyright(self) -> None:
        file_path = self._write_file(
            "pkg/example.go",
            "\n".join(
                [
                    "// Copyright (c) 2019,2020 The Jaeger Authors",
                    "",
                    "package example",
                    "",
                ]
            ),
        )

        changed = lh._update_file(file_path, check_only=False)
        updated = file_path.read_text(encoding="utf-8")
        updated_lines = updated.splitlines()

        self.assertTrue(changed)
        self.assertEqual(updated.count("Copyright (c)"), 1)
        self.assertIn("SPDX-License-Identifier: Apache-2.0", updated)
        self.assertEqual(
            updated_lines[0], "// Copyright (c) 2019,2020 The Jaeger Authors"
        )
        self.assertEqual(updated_lines[1], "// SPDX-License-Identifier: Apache-2.0")

    def test_fix_missing_copyright_when_only_spdx_exists(self) -> None:
        file_path = self._write_file(
            "pkg/example.go",
            "\n".join(
                [
                    "// SPDX-License-Identifier: Apache-2.0",
                    "",
                    "package example",
                    "",
                ]
            ),
        )

        changed = lh._update_file(file_path, check_only=False)
        updated = file_path.read_text(encoding="utf-8")

        self.assertTrue(changed)
        self.assertIn("Copyright (c)", updated)
        self.assertIn("SPDX-License-Identifier: Apache-2.0", updated)

    def test_path_in_scope_ignores_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            outside_path = pathlib.Path(outside) / "external.go"
            outside_path.write_text("package external\n", encoding="utf-8")
            self.assertFalse(lh._path_in_scope(outside_path))

    def test_iter_source_files_prunes_excluded_dirs(self) -> None:
        included = self._write_file("cmd/jaeger/config.yaml", "service:\n")
        self._write_file("vendor/example/config.yaml", "name: vendor\n")
        self._write_file("jaeger-ui/src/index.ts", "const x = 1;\n")
        self._write_file("internal/tools/tool.py", "print('x')\n")
        self._write_file("foo/mocks/bar.go", "package mocks\n")

        paths = lh._iter_source_files()
        rel_paths = {p.relative_to(self._root).as_posix() for p in paths}

        self.assertIn(included.relative_to(self._root).as_posix(), rel_paths)
        self.assertNotIn("vendor/example/config.yaml", rel_paths)
        self.assertNotIn("jaeger-ui/src/index.ts", rel_paths)
        self.assertNotIn("internal/tools/tool.py", rel_paths)
        self.assertNotIn("foo/mocks/bar.go", rel_paths)


if __name__ == "__main__":
    unittest.main()
