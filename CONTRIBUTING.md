# Contributing to elemental-ui

Software, original shaders, generated recipes and UI components are licensed under **GPL-3.0-only**. By contributing, you agree to distribute your contributions under that license. Do not copy proprietary source assets into this repository.

## Submit a material

1. Cite real-world reference photographs or scans in the recipe's `references` with **creator name, URL, license, and acquisition date**. References should stay as metadata until redistribution permission is verified.
2. Declare physical scale, morphology, reproducible seed, and the renderer/generator version.
3. Preserve names and credit of the people who discovered, designed, measured or tested the material.
4. Include an under-neutral-light swatch, a grazing-light view, map seams, and performance measurements.
5. Run `python3 tools/elemental.py validate` and `python3 -m unittest discover -s tests -v`.
6. Do not label a material physically measured or photorealistic unless the relevant validation is documented.

For UI contributions, support keyboard operation, touch, contrast and reduced motion. No bitmap text in interactive controls.

## Source policy

- Reference designs credited to **@jimiplouffe** were supplied as inspiration only; original images are not committed or redistributed.
- External CC0/CC-BY scans are allowed only after source and license audit; use separate provenance documents. Do not silently change third-party license terms.
- Report suspected attribution or license problems in an issue.
