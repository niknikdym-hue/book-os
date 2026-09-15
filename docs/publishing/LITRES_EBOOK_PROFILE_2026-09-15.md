# LitRes ebook profile — checked 2026-09-15

Status: VERSIONED EXTERNAL REQUIREMENTS PROFILE. Platform acceptance remains a separate event.

Official sources checked:
- https://selfpub.ru/faq/first-step/
- https://selfpub.ru/faq/ebook/
- https://www.litres.ru/cms/selfpub/

BOOK OS target derivative: DOCX. LitRes Authors currently documents DOCX as accepted input; the SelfPub FAQ also lists FB2/PDF. Minimum manuscript length is 4,000 characters with spaces; maximum book file size is 70 MB.

Images: PNG or JPG, RGB. Resize/crop/rotation should happen before insertion into Word because the converter may use the original embedded asset. Official recommendation: 72 px/in, maximum long side 1024 px, width 900 px (or 1024 px), maximum image area 2,000,000 pixels, inline-with-text wrapping. BOOK OS programmatic visuals use RGB PNG at 1024x576 and 72 dpi.

Reflowable ebook formatting: font family/size/line spacing are reader-controlled. Preserve chapter/part structure, footnotes, bold and italic semantics. BOOK OS QA does not claim LitRes acceptance; `platform_acceptance_claimed=false` remains mandatory until the platform actually accepts the file.

Implementation note: BOOK OS preserves native DOCX footnotes and internal cross-references for the supported Markdown-like source markers (`[^id]`, `[^id]: text`, `[label](#anchor)`, and `## Heading {#anchor}`). EPUB receives navigable anchors/footnotes. PDF preserves the same reader-visible meaning and internal anchors where supported by ReportLab.
