# pip install langextract -i https://mirrors.aliyun.com/pypi/simple

import langextract as lx

from langextract.providers.openai import OpenAILanguageModel

# Define extraction task with examples
instructions = """
Extract characters, emotions, and relationships in order of appearance.
Use exact text for extractions. Do not paraphrase or overlap entities.
Provide meaningful attributes for each entity to add context.
"""

examples = [
    lx.data.ExampleData(
        text="ROMEO. But soft! What light through yonder window breaks? It is the east, and Juliet is the sun.",
        extractions=[
            lx.data.Extraction(
                extraction_class="character",
                extraction_text="ROMEO",
                attributes={"emotional_state": "wonder"}
            ),
            lx.data.Extraction(
                extraction_class="emotion",
                extraction_text="But soft!",
                attributes={"feeling": "gentle awe"}
            ),
            lx.data.Extraction(
                extraction_class="relationship",
                extraction_text="Juliet is the sun",
                attributes={"type": "metaphor"}
            ),
        ]
    )
]

# Extract from new text
result = lx.extract(
    text_or_documents="https://www.gutenberg.org/files/1513/1513-0.txt",
    prompt_description=instructions,
    examples=examples,
    model=OpenAILanguageModel(
        model_id='COSMO-Mind',
        base_url='https://gpt.cosmoplat.com/v1',
        api_key=''
    ),
    extraction_passes=3,    # Improves recall through multiple passes
    max_workers=20,         # Parallel processing for speed
    max_char_buffer=1000,    # Smaller contexts for better accuracy
    fence_output=True,
    use_schema_constraints=False
)

# Access structured results with source grounding
for extraction in result.extractions:
    print(f"{extraction.extraction_class}: {extraction.extraction_text}")
    print(f"Attributes: {extraction.attributes}")
    print(f"Source position: {extraction.char_start}-{extraction.char_end}")