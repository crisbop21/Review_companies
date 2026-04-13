"""Audio assembler. Concatenates ElevenLabs segments with gap rules.

Implementation lands in Phase 6 Task 2.2. Rules:
- 300ms silence between turns within an act
- 800ms silence between acts
"""


def assemble(segments: list, output_path: str) -> str:
    raise NotImplementedError("Implemented in Phase 6 Task 2.2.")
