from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.units import inch

def create_pdf(input_file, output_file):
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    with open(input_file, 'r') as file:
        text = file.read()
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                if para.startswith('#'):
                    # Handle headers
                    story.append(Paragraph(para.strip('# '), styles['Heading1']))
                else:
                    story.append(Paragraph(para, styles['Normal']))
    
    doc.build(story)

if __name__ == '__main__':
    create_pdf('sample.txt', 'sample.pdf') 