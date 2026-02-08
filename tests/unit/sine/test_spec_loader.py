from __future__ import annotations

from pathlib import Path

from sine.specs import load_rule_specs


def test_load_rule_specs_reads_yaml(tmp_path: Path) -> None:
    rule_path = tmp_path / "ARCH-100.yaml"
    rule_path.write_text(
        """
 schema_version: 1
 rule:
   id: "ARCH-100"
   title: "Avoid direct SQL"
   description: "No raw SQL calls."
   rationale: "Prevents injection."
   tier: 1
   category: "security"
   severity: "error"
   languages: [python]
   check:
     type: "forbidden"
     pattern: "cursor.execute($X)"
   reporting:
     default_message: "Direct SQL forbidden (ARCH-100)"
     confidence: "high"
     documentation_url: null
   examples:
     good:
       - language: python
         code: "safe_query()"
     bad:
       - language: python
         code: "cursor.execute(sql)"
   references: []
        """,
        encoding="utf-8",
    )

    specs = load_rule_specs(tmp_path)
    assert len(specs) == 1
    assert specs[0].rule.id == "ARCH-100"

