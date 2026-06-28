# section_splitter.py

from typing import List
from docx.oxml.ns import qn


def split_body_by_sections(body) -> List[List]:
    """
    Split doc.element.body into separate sections.

    A DOCX section ends when a paragraph contains <w:sectPr>.
    
    Returns:
        [
            [elements belonging to section 1],
            [elements belonging to section 2],
            ...
        ]
    """

    sections = []
    current_section = []

    for element in body:

        # Add current XML element
        current_section.append(element)

        # Check for section break
        # <w:p>
        #    <w:pPr>
        #        <w:sectPr/>
        #    </w:pPr>
        # </w:p>
        if element.tag == qn("w:p"):

            paragraph_properties = element.find(qn("w:pPr"))

            if paragraph_properties is not None:
                section_properties = paragraph_properties.find(
                    qn("w:sectPr")
                )

                if section_properties is not None:
                    sections.append(current_section)
                    current_section = []

    # Remaining elements belong to the last section
    if current_section:
        sections.append(current_section)

    return sections