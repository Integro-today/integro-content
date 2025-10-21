# Python-DOCX API Mapping & Reference

Comprehensive API reference for working with Microsoft Word (.docx) files using python-docx v1.2.0.

**Installation:**
```bash
pip install python-docx
```

**Repository:** https://github.com/python-openxml/python-docx
**Documentation:** https://python-docx.readthedocs.io/

---

## Table of Contents

1. [Document Operations](#document-operations)
2. [Paragraph Operations](#paragraph-operations)
3. [Run Operations (Character Formatting)](#run-operations-character-formatting)
4. [Table Operations](#table-operations)
5. [Font & Styling](#font--styling)
6. [Hyperlinks](#hyperlinks)
7. [Images & Pictures](#images--pictures)
8. [Sections & Page Layout](#sections--page-layout)
9. [Comments](#comments)
10. [Common Patterns](#common-patterns)

---

## Document Operations

### Opening/Creating Documents

```python
from docx import Document

# Create new blank document (uses default template)
doc = Document()

# Open existing document
doc = Document('/path/to/document.docx')

# Open from file-like object (e.g., BytesIO)
with open('document.docx', 'rb') as f:
    doc = Document(f)
```

### Document Properties

```python
# Core properties (metadata)
doc.core_properties.author = "Your Name"
doc.core_properties.title = "Document Title"
doc.core_properties.subject = "Subject"
doc.core_properties.keywords = "keyword1, keyword2"
doc.core_properties.comments = "Description"
doc.core_properties.category = "Report"
doc.core_properties.created  # datetime
doc.core_properties.modified  # datetime
doc.core_properties.last_modified_by = "Editor Name"
doc.core_properties.revision  # int - revision number
doc.core_properties.version = "1.0"

# Document structure access
doc.paragraphs  # List of all Paragraph objects
doc.tables      # List of all Table objects
doc.sections    # Sections object (page layout)
doc.styles      # Styles object (document styles)
doc.settings    # Settings object (document settings)
doc.inline_shapes  # InlineShapes collection (images, etc.)
```

### Document Content Iteration

```python
# Iterate through all paragraphs and tables in document order
for item in doc.iter_inner_content():
    if isinstance(item, Paragraph):
        print(f"Paragraph: {item.text}")
    elif isinstance(item, Table):
        print(f"Table: {len(item.rows)} rows x {len(item.columns)} cols")
```

### Saving Documents

```python
# Save to file path
doc.save('output.docx')

# Save to file-like object
from io import BytesIO
doc_stream = BytesIO()
doc.save(doc_stream)
doc_stream.seek(0)  # Reset to beginning for reading
```

---

## Paragraph Operations

### Adding Paragraphs

```python
# Add paragraph with text
p = doc.add_paragraph('This is a paragraph.')

# Add empty paragraph
p = doc.add_paragraph()

# Add paragraph with style
p = doc.add_paragraph('Bullet point', style='List Bullet')
p = doc.add_paragraph('Numbered item', style='List Number')
p = doc.add_paragraph('Quote text', style='Intense Quote')

# Insert paragraph before another
new_p = existing_paragraph.insert_paragraph_before('New text')
```

### Adding Headings

```python
# Add heading (level 1-9, or 0 for Title)
doc.add_heading('Document Title', level=0)  # Title style
doc.add_heading('Main Heading', level=1)    # Heading 1
doc.add_heading('Sub Heading', level=2)     # Heading 2
```

### Paragraph Properties

```python
# Text content
p.text  # Get full text (read/write)
p.text = "New text"  # Replaces all content with single run

# Style
p.style = 'Heading 1'
p.style = None  # Remove direct style (use default)

# Runs (formatted text segments)
p.runs  # List of Run objects
p.add_run('text', style='Emphasis')  # Add run with style

# Hyperlinks
p.hyperlinks  # List of Hyperlink objects in paragraph

# Clear content but preserve formatting
p.clear()

# Page breaks
p.contains_page_break  # bool - has rendered page breaks
p.rendered_page_breaks  # List of all rendered page breaks
```

### Paragraph Formatting

```python
pf = p.paragraph_format

# Alignment
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
pf.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
pf.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

# Indentation
from docx.shared import Inches, Pt, Cm
pf.left_indent = Inches(0.5)
pf.right_indent = Cm(1.0)
pf.first_line_indent = Inches(0.25)  # Positive = indent, negative = hanging

# Spacing
pf.space_before = Pt(12)
pf.space_after = Pt(6)

# Line spacing
pf.line_spacing = 1.5  # Multiple of single spacing
pf.line_spacing = Pt(18)  # Fixed height
from docx.enum.text import WD_LINE_SPACING
pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE

# Page breaks
pf.page_break_before = True  # Start on new page
pf.keep_together = True      # Don't split across pages
pf.keep_with_next = True     # Keep with next paragraph

# Widow/orphan control
pf.widow_control = True
```

---

## Run Operations (Character Formatting)

Runs are segments of text within a paragraph with consistent character formatting.

### Adding & Accessing Runs

```python
# Add run to paragraph
run = p.add_run('text')
run = p.add_run('styled text', style='Emphasis')

# Access runs
for run in p.runs:
    print(run.text)

# Run text (read/write)
run.text  # Get text
run.text = "New text"  # Replace text
run.add_text('more text')  # Append text

# Clear content but preserve formatting
run.clear()
```

### Character Formatting

```python
# Bold, italic, underline
run.bold = True
run.italic = True
run.underline = True

# Underline styles
from docx.enum.text import WD_UNDERLINE
run.underline = WD_UNDERLINE.DOUBLE
run.underline = WD_UNDERLINE.WAVY
run.underline = WD_UNDERLINE.DOTTED

# Font properties
run.font.name = 'Arial'
run.font.size = Pt(12)

# Font effects
run.font.all_caps = True
run.font.small_caps = True
run.font.strike = True
run.font.double_strike = True
run.font.superscript = True
run.font.subscript = True
run.font.shadow = True
run.font.outline = True
run.font.emboss = True
run.font.imprint = True
run.font.hidden = True

# Color
from docx.shared import RGBColor
run.font.color.rgb = RGBColor(255, 0, 0)  # Red

# Highlight
from docx.enum.text import WD_COLOR_INDEX
run.font.highlight_color = WD_COLOR_INDEX.YELLOW

# Character style
run.style = 'Emphasis'
run.style = 'Strong'
```

### Special Characters in Runs

```python
# Tabs
run.add_tab()
# Or in text: "text\twith\ttabs"

# Line breaks
from docx.enum.text import WD_BREAK_TYPE
run.add_break()  # Line break (default)
run.add_break(WD_BREAK_TYPE.LINE)
run.add_break(WD_BREAK_TYPE.PAGE)
run.add_break(WD_BREAK_TYPE.COLUMN)

# Text with special characters
p.add_run('Line 1\nLine 2')  # \n becomes line break
p.add_run('Tab\there')        # \t becomes tab
```

---

## Table Operations

### Creating Tables

```python
# Add table with specified rows and columns
table = doc.add_table(rows=3, cols=3)

# Add table with style
table = doc.add_table(rows=3, cols=3, style='Light Grid Accent 1')

# Add table inside a cell (nested table)
nested_table = cell.add_table(rows=2, cols=2)
```

### Table Properties

```python
# Access rows and columns
table.rows     # _Rows collection
table.columns  # _Columns collection

# Counts
len(table.rows)
len(table.columns)

# Table style
table.style = 'Light Shading Accent 1'
# Note: Remove spaces from style name as shown in Word UI

# Table alignment
from docx.enum.table import WD_TABLE_ALIGNMENT
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# Autofit behavior
table.autofit = True   # Auto-adjust column widths
table.autofit = False  # Fixed layout

# Table direction (for RTL languages)
from docx.enum.table import WD_TABLE_DIRECTION
table.table_direction = WD_TABLE_DIRECTION.RTL
```

### Accessing Cells

```python
# By row and column index (0-based)
cell = table.cell(0, 1)  # Row 0, Column 1

# Via rows
row = table.rows[0]
cell = row.cells[0]

# Via columns
col = table.columns[0]
cell = col.cells[0]

# Get all cells in specific row
cells = table.row_cells(0)  # DEPRECATED: use table.rows[0].cells

# Get all cells in specific column
cells = table.column_cells(0)
```

### Adding Rows and Columns

```python
# Add row at bottom
new_row = table.add_row()

# Add column at right
new_col = table.add_column(width=Inches(1.5))

# Access new row's cells
cells = new_row.cells
cells[0].text = 'Data 1'
cells[1].text = 'Data 2'
```

### Row Properties

```python
row = table.rows[0]

# Access cells
row.cells  # List of _Cell objects

# Row height
row.height = Inches(0.5)
from docx.enum.table import WD_ROW_HEIGHT_RULE
row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
row.height_rule = WD_ROW_HEIGHT_RULE.AUTO

# Parent table reference
row.table

# Grid positioning (for complex table layouts)
row.grid_cols_before  # Empty columns before first cell
row.grid_cols_after   # Empty columns after last cell
```

### Column Properties

```python
col = table.columns[0]

# Access cells
col.cells  # List of _Cell objects

# Column width
col.width = Inches(2.0)

# Parent table reference
col.table
```

### Cell Operations

```python
cell = table.cell(0, 0)

# Text content
cell.text  # Get text (concatenates all paragraphs)
cell.text = "New text"  # Replaces all content

# Paragraphs and tables inside cell
cell.paragraphs  # List of Paragraph objects
cell.tables      # List of nested Table objects

# Add content to cell
p = cell.add_paragraph('Additional text')
nested_table = cell.add_table(rows=2, cols=2)

# Iterate cell content
for item in cell.iter_inner_content():
    if isinstance(item, Paragraph):
        print(item.text)

# Merge cells
cell1 = table.cell(0, 0)
cell2 = table.cell(0, 1)
cell1.merge(cell2)  # Merge horizontally

# Vertical alignment
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.BOTTOM

# Cell width
cell.width = Inches(2.0)

# Grid span (for merged cells)
cell.grid_span  # Number of columns spanned
```

### Iterating Tables

```python
# Iterate all rows
for row in table.rows:
    for cell in row.cells:
        print(cell.text)

# Iterate specific column
for cell in table.columns[0].cells:
    print(cell.text)

# Access with indices
for i, row in enumerate(table.rows):
    for j, cell in enumerate(row.cells):
        print(f"Cell [{i}][{j}]: {cell.text}")
```

---

## Font & Styling

### Font Properties

```python
font = run.font

# Typeface and size
font.name = 'Calibri'
font.size = Pt(12)

# Style attributes
font.bold = True
font.italic = True
font.underline = True
font.strike = True
font.double_strike = True

# Effects
font.all_caps = True
font.small_caps = True
font.shadow = True
font.outline = True
font.emboss = True
font.imprint = True
font.hidden = True

# Superscript/subscript
font.superscript = True
font.subscript = True

# Color
from docx.shared import RGBColor
font.color.rgb = RGBColor(255, 0, 0)

# Highlighting
from docx.enum.text import WD_COLOR_INDEX
font.highlight_color = WD_COLOR_INDEX.YELLOW
font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN
font.highlight_color = None  # Remove highlight

# Complex script support
font.complex_script = True
font.cs_bold = True
font.cs_italic = True

# Advanced typography
font.rtl = True  # Right-to-left
font.math = True  # Math formatting
font.no_proof = True  # Skip spell check
```

### Paragraph Styles

Common built-in paragraph styles:
- `'Normal'` - Default body text
- `'Heading 1'` through `'Heading 9'`
- `'Title'`, `'Subtitle'`
- `'List Bullet'`, `'List Number'`
- `'List Bullet 2'`, `'List Number 2'` (indented)
- `'Quote'`, `'Intense Quote'`
- `'Body Text'`, `'Body Text 2'`, `'Body Text 3'`
- `'No Spacing'`

```python
# Apply style when creating
p = doc.add_paragraph('Text', style='Body Text')

# Apply style after creation
p.style = 'Heading 2'

# Access styles
doc.styles  # All styles in document
```

### Character Styles

Common built-in character styles:
- `'Default Paragraph Font'`
- `'Emphasis'` (italic)
- `'Strong'` (bold)
- `'Subtle Emphasis'`
- `'Intense Emphasis'`

```python
# Apply character style
run = p.add_run('emphasized text', style='Emphasis')
run.style = 'Strong'
```

---

## Hyperlinks

### Accessing Hyperlinks

```python
# Get all hyperlinks in paragraph
for hyperlink in paragraph.hyperlinks:
    print(hyperlink.text)
    print(hyperlink.url)

# Iterate through runs and hyperlinks
for item in paragraph.iter_inner_content():
    if isinstance(item, Hyperlink):
        print(f"Link: {item.text} -> {item.url}")
    elif isinstance(item, Run):
        print(f"Text: {item.text}")
```

### Hyperlink Properties

```python
hyperlink = paragraph.hyperlinks[0]

# URL components
hyperlink.address   # Base URL (e.g., "https://example.com")
hyperlink.fragment  # Anchor/bookmark (e.g., "section1")
hyperlink.url       # Full URL (address + "#" + fragment)

# Display text
hyperlink.text  # Concatenated text from all runs

# Runs within hyperlink
hyperlink.runs  # List of Run objects

# Page breaks
hyperlink.contains_page_break  # bool
```

---

## Images & Pictures

### Adding Pictures

```python
# Add picture from file path
doc.add_picture('image.png')

# Add picture with specific size
doc.add_picture('image.png', width=Inches(2.0))
doc.add_picture('image.png', height=Cm(5.0))

# Add picture maintaining aspect ratio (specify width OR height)
doc.add_picture('image.png', width=Inches(3.0))  # Height auto-calculated

# Add picture from file-like object
from io import BytesIO
image_stream = BytesIO(image_bytes)
doc.add_picture(image_stream, width=Inches(2.0))

# Add picture in a run (inline with text)
run = p.add_run()
inline_shape = run.add_picture('image.png', width=Inches(1.0))
```

### Working with InlineShapes

```python
# Access inline shapes (images)
doc.inline_shapes  # InlineShapes collection

# Images appear in document order within runs
```

---

## Sections & Page Layout

### Working with Sections

```python
# Access sections
doc.sections  # Sections object
section = doc.sections[0]  # First section

# Add new section
from docx.enum.section import WD_SECTION_START
new_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
new_section = doc.add_section(WD_SECTION_START.CONTINUOUS)
new_section = doc.add_section(WD_SECTION_START.ODD_PAGE)
new_section = doc.add_section(WD_SECTION_START.EVEN_PAGE)
```

### Section Properties

```python
section = doc.sections[0]

# Page dimensions
section.page_height = Inches(11)  # Letter: 11 inches
section.page_width = Inches(8.5)   # Letter: 8.5 inches

# Margins
section.top_margin = Inches(1.0)
section.bottom_margin = Inches(1.0)
section.left_margin = Inches(1.0)
section.right_margin = Inches(1.0)

# Orientation
from docx.enum.section import WD_ORIENTATION
section.orientation = WD_ORIENTATION.PORTRAIT
section.orientation = WD_ORIENTATION.LANDSCAPE

# Headers and footers
section.header  # Header object
section.footer  # Footer object
section.first_page_header
section.first_page_footer
section.even_page_header
section.even_page_footer
```

### Page Breaks

```python
# Add hard page break (creates new paragraph)
doc.add_page_break()

# Add page break in existing run
from docx.enum.text import WD_BREAK_TYPE
run.add_break(WD_BREAK_TYPE.PAGE)

# Paragraph starts on new page
p.paragraph_format.page_break_before = True
```

---

## Comments

### Adding Comments

```python
# Add comment to single run
run = p.add_run('important text')
comment = doc.add_comment(
    run,
    text='This needs review',
    author='Reviewer Name',
    initials='RN'
)

# Add comment to multiple runs
comment = doc.add_comment(
    runs=p.runs,  # All runs in paragraph
    text='Review this entire paragraph',
    author='Editor',
    initials='ED'
)

# Add comment to range of runs
start_run = p.runs[0]
end_run = p.runs[2]
comment = doc.add_comment(
    runs=[start_run, end_run],
    text='Check runs 0-2',
    author='QA'
)
```

### Comment Properties

```python
# Add complex comment content
comment = doc.add_comment(paragraph.runs, text='', author='Editor')
comment.add_paragraph('First point to review')
comment.add_paragraph('Second point to review')

# Access all comments
doc.comments  # Comments collection
```

---

## Common Patterns

### Pattern: Read Document Structure

```python
from docx import Document

doc = Document('document.docx')

# Print all headings
for para in doc.paragraphs:
    if para.style.name.startswith('Heading'):
        print(f"{para.style.name}: {para.text}")

# Print all text
for para in doc.paragraphs:
    print(para.text)

# Find tables
for i, table in enumerate(doc.tables):
    print(f"Table {i}: {len(table.rows)} rows x {len(table.columns)} cols")
```

### Pattern: Extract Table Data

```python
def extract_table_data(table):
    """Extract table as list of lists."""
    data = []
    for row in table.rows:
        row_data = [cell.text for cell in row.cells]
        data.append(row_data)
    return data

# Usage
doc = Document('data.docx')
for table in doc.tables:
    data = extract_table_data(table)
    # Process data...
```

### Pattern: Build Document from Data

```python
from docx import Document
from docx.shared import Inches, Pt

doc = Document()

# Add title
doc.add_heading('Report Title', 0)

# Add section with content
doc.add_heading('Section 1', 1)
doc.add_paragraph('Introduction text...')

# Add data table
records = [
    ('Item 1', 100, 5.99),
    ('Item 2', 50, 12.99),
]

table = doc.add_table(rows=1, cols=3)
table.style = 'Light Grid Accent 1'

# Header row
hdr_cells = table.rows[0].cells
hdr_cells[0].text = 'Product'
hdr_cells[1].text = 'Quantity'
hdr_cells[2].text = 'Price'

# Data rows
for product, qty, price in records:
    row_cells = table.add_row().cells
    row_cells[0].text = product
    row_cells[1].text = str(qty)
    row_cells[2].text = f'${price:.2f}'

# Save
doc.save('report.docx')
```

### Pattern: Find and Extract Specific Content

```python
def find_paragraphs_with_style(doc, style_name):
    """Find all paragraphs with specific style."""
    return [p for p in doc.paragraphs if p.style.name == style_name]

def find_text_in_document(doc, search_text):
    """Find paragraphs containing specific text."""
    matches = []
    for para in doc.paragraphs:
        if search_text.lower() in para.text.lower():
            matches.append(para)
    return matches

# Usage
doc = Document('document.docx')
headings = find_paragraphs_with_style(doc, 'Heading 1')
intro_paragraphs = find_text_in_document(doc, 'introduction')
```

### Pattern: Clone Paragraph with Formatting

```python
def duplicate_paragraph(paragraph):
    """Create new paragraph with same style and formatting."""
    new_p = paragraph.insert_paragraph_before('')
    new_p.style = paragraph.style
    new_p.paragraph_format.alignment = paragraph.paragraph_format.alignment
    # Copy other formatting as needed
    return new_p
```

### Pattern: Extract All Text with Structure

```python
def extract_full_document_text(doc):
    """Extract text with structure markers."""
    content = []

    for item in doc.iter_inner_content():
        if isinstance(item, Paragraph):
            style = item.style.name
            text = item.text
            content.append({
                'type': 'paragraph',
                'style': style,
                'text': text
            })
        elif isinstance(item, Table):
            table_data = extract_table_data(item)
            content.append({
                'type': 'table',
                'data': table_data
            })

    return content
```

### Pattern: Apply Formatting to Search Results

```python
def highlight_text(doc, search_term, color=WD_COLOR_INDEX.YELLOW):
    """Find and highlight all instances of search term."""
    from docx.enum.text import WD_COLOR_INDEX

    for para in doc.paragraphs:
        if search_term.lower() in para.text.lower():
            # Clear and rebuild paragraph with highlighting
            full_text = para.text
            para.clear()

            # Split by search term (case insensitive)
            import re
            parts = re.split(f'({re.escape(search_term)})', full_text, flags=re.IGNORECASE)

            for part in parts:
                run = para.add_run(part)
                if part.lower() == search_term.lower():
                    run.font.highlight_color = color
```

---

## Units and Measurements

```python
from docx.shared import Inches, Cm, Mm, Pt, Emu

# Length units
width = Inches(1.5)
height = Cm(5)
margin = Mm(25.4)
font_size = Pt(12)

# Conversion
inches_value = Inches(2)
cm_value = inches_value.cm  # Convert to cm
pt_value = inches_value.pt  # Convert to points

# EMU (English Metric Units) - internal unit
# 914,400 EMU = 1 inch
emu_value = Emu(914400)  # 1 inch
```

---

## Error Handling

```python
from docx import Document
from docx.opc.exceptions import PackageNotFoundError

try:
    doc = Document('nonexistent.docx')
except PackageNotFoundError:
    print("Document not found")
    doc = Document()  # Create new

# Handle invalid cell access
try:
    cell = table.cell(100, 100)
except IndexError:
    print("Cell out of range")

# Handle merge errors
from docx.opc.exceptions import InvalidSpanError
try:
    cell1.merge(cell2)
except InvalidSpanError:
    print("Cells don't form valid merge region")
```

---

## Best Practices

1. **Always use context managers for file operations:**
   ```python
   with open('document.docx', 'rb') as f:
       doc = Document(f)
   ```

2. **Use unit helpers for measurements:**
   ```python
   # Good
   width = Inches(2.0)

   # Bad (uses EMU - 914400 = 1 inch)
   width = 1828800
   ```

3. **Check for None values:**
   ```python
   if para.style is not None:
       style_name = para.style.name
   ```

4. **Preserve formatting when possible:**
   ```python
   # Clear content but keep formatting
   para.clear()

   # Add runs to preserve character formatting
   run = para.add_run('new text')
   run.bold = True
   ```

5. **Handle special characters properly:**
   ```python
   # Tabs and newlines in strings are auto-converted
   para.add_run('Line 1\nLine 2\tTabbed')
   ```

6. **Use iter_inner_content() for proper document order:**
   ```python
   # Good - respects actual document structure
   for item in doc.iter_inner_content():
       # Process paragraphs and tables in order

   # Limited - misses nested content
   for para in doc.paragraphs:
       # Only top-level paragraphs
   ```

---

## For Integro Content Parsing

### Specific Use Cases

**Extract Weekly Content Structure:**
```python
from docx import Document

def parse_week_content(docx_path):
    doc = Document(docx_path)

    week_data = {
        'title': None,
        'days': []
    }

    current_day = None

    for para in doc.paragraphs:
        style = para.style.name
        text = para.text.strip()

        if style == 'Title' or style == 'Heading 1':
            week_data['title'] = text

        elif style == 'Heading 2' and text.startswith('Day'):
            if current_day:
                week_data['days'].append(current_day)
            current_day = {
                'day': text,
                'passages': [],
                'activities': []
            }

        elif style == 'Heading 3':
            # Activity or section heading
            current_day['activities'].append({
                'title': text,
                'content': []
            })

        elif style == 'Normal' and current_day:
            # Content paragraph
            if current_day['activities']:
                current_day['activities'][-1]['content'].append(text)
            else:
                current_day['passages'].append(text)

    if current_day:
        week_data['days'].append(current_day)

    return week_data
```

**Extract Tables (for structured activities):**
```python
def extract_activity_tables(doc):
    activities = []

    for table in doc.tables:
        activity = {}
        for i, row in enumerate(table.rows):
            if i == 0:
                # Header row
                continue
            key = row.cells[0].text.strip()
            value = row.cells[1].text.strip()
            activity[key] = value
        activities.append(activity)

    return activities
```

---

## References

- **Official Docs:** https://python-docx.readthedocs.io/
- **GitHub:** https://github.com/python-openxml/python-docx
- **PyPI:** https://pypi.org/project/python-docx/
- **API Reference:** https://python-docx.readthedocs.io/en/latest/api/

---

**Version:** 1.2.0
**Created:** 2025-10-20
**For:** Integro Content Management System
