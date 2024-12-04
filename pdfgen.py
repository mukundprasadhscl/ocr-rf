import io
import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from PIL import Image as PILImage
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import HRFlowable
import streamlit as st



def create_pdf_document(data, profile_picture=None, logo_path=None):
    # Create a BytesIO object to store the PDF
    pdf_buffer = io.BytesIO()

    # Create the PDF document with margins similar to Word document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=72,  # 1 inch
        leftMargin=72,  # 1 inch
        topMargin=65,  # 0.5 inch
        bottomMargin=72  # 1 inch
    )

    pdfmetrics.registerFont(TTFont('Calibri', 'calibri.ttf'))
    pdfmetrics.registerFont(TTFont('CalibriB', 'calibri_bold.ttf'))

    custom_styles = {
        'ResumeName': ParagraphStyle(
            name='ResumeName',
            fontName='CalibriB',
            fontSize=18,
            leading=28,
            spaceAfter=6,
            alignment=TA_LEFT
        ),
        'ResumeContact': ParagraphStyle(
            name='ResumeContact',
            fontName='Calibri',
            fontSize=12,
            leading=14,
            spaceAfter=6,
            alignment=TA_LEFT
        ),
        'ResumeSection': ParagraphStyle(
            name='ResumeSection',
            fontName='CalibriB',
            fontSize=14,
            leading=16,
            spaceBefore=6,
            spaceAfter=3,
            textColor=colors.black,
            alignment=TA_LEFT
        ),
        'ResumeContent': ParagraphStyle(
            name='ResumeContent',
            fontName='Calibri',
            fontSize=12,
            leading=14,
            spaceAfter=3,
            alignment=TA_JUSTIFY
        ),
        'ResumeBullet': ParagraphStyle(
            name='ResumeBullet',
            fontName='Calibri',
            fontSize=12,
            leading=14,
            leftIndent=36,
            firstLineIndent=-18,
            spaceAfter=3,
            alignment=TA_JUSTIFY
        ),
        'ResumeSubheading': ParagraphStyle(
            name='ResumeSubheading',
            fontName='CalibriB',
            fontSize=12,
            leading=14,
            spaceAfter=3,
            alignment=TA_LEFT
        )
    }
    # Build the document content
    story = []

    # Profile picture processing
    profile_pic_temp = None
    if profile_picture:
        try:
            # Convert PIL Image to bytes if needed
            if isinstance(profile_picture, PILImage.Image):
                img_byte_arr = io.BytesIO()
                profile_picture.save(img_byte_arr, format=profile_picture.format or 'PNG')
                profile_picture = img_byte_arr.getvalue()
        except Exception as e:
            st.error(f"Error processing profile picture: {str(e)}")
            profile_picture = None

    # Calculate available width
    available_width = letter[0] - doc.leftMargin - doc.rightMargin
    contact_width = available_width - 120 if profile_picture else available_width

    # Prepare contact information
    contact_info = []
    if data['personal_info']['address']:
        contact_info.append(f"Address: {data['personal_info']['address']}")
    if data['personal_info']['LinkedIn']:
        contact_info.append(f"LinkedIn: {data['personal_info']['LinkedIn']}")
    if data['personal_info']['date_of_birth']:
        contact_info.append(f"DOB: {data['personal_info']['date_of_birth']}")
    if data['personal_info']['nationality']:
        contact_info.append(f"Nationality: {data['personal_info']['nationality']}")
    if data['personal_info']['father_name']:
        contact_info.append(f"Father's Name: {data['personal_info']['father_name']}")

    # Create single paragraph combining name and contact info
    header_text = (
        f"<font size='24'><b>{data['personal_info']['name']}</b></font><br/>"
        f"{'<br/>'.join(contact_info)}"
    )

    header_paragraph = Paragraph(header_text, custom_styles['ResumeContent'])

    if profile_picture:
        # Create a temporary file for profile picture
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            if isinstance(profile_picture, bytes):
                tmp_file.write(profile_picture)
            else:
                PILImage.fromarray(profile_picture).save(tmp_file, format='PNG')
            tmp_file.flush()
            profile_pic_temp = tmp_file.name

            # Create image object for table
            img = Image(profile_pic_temp)
            img.drawHeight = 80
            img.drawWidth = 80

            # Table data with profile picture
            table_data = [[header_paragraph, img]]
    else:
        # Table data without profile picture
        table_data = [[header_paragraph]]

    # Create table with appropriate column widths
    col_widths = [contact_width, 100] if profile_picture else [contact_width]

    # Create and style the table
    header_table = Table(table_data, colWidths=col_widths)
    # Modify the table creation and styling
    if profile_picture:
        col_widths = [contact_width, 100]
        header_table = Table(table_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), -5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        # When no profile picture, use standard padding
        header_table = Table(table_data)
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

    story.append(header_table)
    story.append(Spacer(1, 20))

    # Professional Summary
    if data['professional_summary']:
        story.append(Paragraph('PROFESSIONAL SUMMARY', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        story.append(Paragraph(data['professional_summary'], custom_styles['ResumeContent']))
    if data['career_objective']:
        story.append(Paragraph('CAREER OBJECTIVE', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        story.append(Paragraph(data['career_objective'], custom_styles['ResumeContent']))

    # Education
    story.append(Paragraph('EDUCATION', custom_styles['ResumeSection']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    for edu in data['education']:
        edu_text = f"{edu['degree']} - {edu['institution']}"
        story.append(Paragraph(edu_text, custom_styles['ResumeSubheading']))

        edu_details = []
        if edu['year']:
            edu_details.append(edu['year'])
        if edu['details']:
            edu_details.append(edu['details'])

        if edu_details:
            story.append(Paragraph(' | '.join(edu_details), custom_styles['ResumeContent']))

    # Skills
    story.append(Paragraph('SKILLS', custom_styles['ResumeSection']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    # Technical Skills
    if data['skills']['technical']:
        for category, skills in data['skills']['technical'].items():
            if skills:
                # Create a bold style for just the category
                category_bold_style = ParagraphStyle(
                    'TechnicalSkillCategoryBold',
                    parent=custom_styles['ResumeContent'],
                    fontName='CalibriB'
                )

                # Create a normal style for skills
                skills_normal_style = custom_styles['ResumeContent']

                # Create a composite paragraph with bold category and normal skills
                skills_text = f"<font name='CalibriB'>{category}:</font> {', '.join(skills)}"
                story.append(Paragraph(skills_text, skills_normal_style))
                story.append(Spacer(1, 6))
    # Soft Skills
    if data['skills']['soft']:
        soft_skills_text = f"<font name='CalibriB'>Soft Skills:</font> {', '.join(data['skills']['soft'])}"
        story.append(Paragraph(soft_skills_text, custom_styles['ResumeContent']))
        story.append(Spacer(1, 6))

    # Professional Experience
    story.append(Paragraph('PROFESSIONAL EXPERIENCE', custom_styles['ResumeSection']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    for exp in data['experience']:
        # Job title and company
        story.append(Paragraph(
            f"{exp['title']} - {exp['company']}",
            custom_styles['ResumeSubheading']
        ))

        if exp.get('duration'):
            story.append(Paragraph(exp['duration'], custom_styles['ResumeContent']))

        # Responsibilities
        for resp in exp['responsibilities']:
            story.append(Paragraph(f"• {resp}", custom_styles['ResumeBullet']))

    # Projects
    if data['projects']:
        story.append(Paragraph('PROJECTS', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        for project in data['projects']:
            # Project name
            story.append(Paragraph(project['name'], custom_styles['ResumeSubheading']))

            # Description
            if project['description']:
                story.append(Paragraph(project['description'], custom_styles['ResumeContent']))

            # Technologies
            if project['technologies']:
                story.append(Paragraph(
                    f"Technologies: {project['technologies']}",
                    custom_styles['ResumeContent']
                ))

            story.append(Spacer(1, 6))

    # Certifications
    if data['courses_and_certifications']:
        story.append(Paragraph('COURSES AND CERTIFICATIONS', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        for cert in data['courses_and_certifications']:
            cert_text = f"{cert['name']} - {cert['issuer']} ({cert['year']}) - {cert['type'].capitalize()}"
            story.append(Paragraph(f"• {cert_text}", custom_styles['ResumeBullet']))
        story.append(Spacer(1, 6))

    # Additional Sections
    additional_sections = data.get('additional_sections', {})

    # Achievements
    achievements = additional_sections.get('achievements', [])
    if achievements and achievements[0]['title']:
        story.append(Paragraph('ACHIEVEMENTS', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        for achievement in achievements:
            achievement_text = achievement['title']
            if achievement['year']:
                achievement_text += f" ({achievement['year']})"
            if achievement['description']:
                achievement_text += f" - {achievement['description']}"
            story.append(Paragraph(f"• {achievement_text}", custom_styles['ResumeBullet']))
        story.append(Spacer(1, 6))

    # Volunteer Work
    volunteer_work = additional_sections.get('volunteer_work', [])
    if volunteer_work and volunteer_work[0]['organization']:
        story.append(Paragraph('VOLUNTEER WORK', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        for volunteer in volunteer_work:
            story.append(Paragraph(
                f"{volunteer['role']} - {volunteer['organization']}",
                custom_styles['ResumeSubheading']
            ))

            if volunteer['duration']:
                story.append(Paragraph(volunteer['duration'], custom_styles['ResumeContent']))

            if volunteer['description']:
                story.append(Paragraph(f"• {volunteer['description']}", custom_styles['ResumeBullet']))

        story.append(Spacer(1, 6))

    # Languages
    languages = additional_sections.get('languages', [])
    if languages and languages[0]['language']:
        story.append(Paragraph('LANGUAGES', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        language_text = []
        for lang in languages:
            lang_entry = lang['language']
            if lang['proficiency']:
                lang_entry += f" ({lang['proficiency']})"
            language_text.append(lang_entry)
        story.append(Paragraph(', '.join(language_text), custom_styles['ResumeContent']))
        story.append(Spacer(1, 6))

    # Awards
    awards = additional_sections.get('awards', [])
    if awards and awards[0]['name']:
        story.append(Paragraph('AWARDS', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        for award in awards:
            award_text = award['name']
            if award['issuer']:
                award_text += f" - {award['issuer']}"
            if award['year']:
                award_text += f" ({award['year']})"
            story.append(Paragraph(f"• {award_text}", custom_styles['ResumeBullet']))
        story.append(Spacer(1, 6))

    # Publications
    publications = additional_sections.get('publications', [])
    if publications and publications[0]['title']:
        story.append(Paragraph('PUBLICATIONS', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        for pub in publications:
            pub_text = pub['title']
            if pub['authors']:
                pub_text += f" by {pub['authors']}"
            if pub['publication_venue']:
                pub_text += f" in {pub['publication_venue']}"
            if pub['year']:
                pub_text += f" ({pub['year']})"
            story.append(Paragraph(f"• {pub_text}", custom_styles['ResumeBullet']))
        story.append(Spacer(1, 6))

    # Professional Memberships
    memberships = additional_sections.get('professional_memberships', [])
    if memberships and memberships[0]['organization']:
        story.append(Paragraph('PROFESSIONAL MEMBERSHIPS', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
        for membership in memberships:
            membership_text = membership['organization']
            if membership['role']:
                membership_text += f" - {membership['role']}"
            if membership['year']:
                membership_text += f" ({membership['year']})"
            story.append(Paragraph(f"• {membership_text}", custom_styles['ResumeBullet']))
        story.append(Spacer(1, 6))
    interests_and_hobbies = additional_sections.get('interests_and_hobbies', [])
    if interests_and_hobbies and interests_and_hobbies[0]['name']:
        story.append(Paragraph('INTERESTS AND HOBBIES', custom_styles['ResumeSection']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.black))

        interest_text = []
        for interest in interests_and_hobbies:
            interest_entry = interest['name']
            if interest['description']:
                interest_entry += f" ({interest['description']})"
            interest_text.append(interest_entry)

        story.append(Paragraph(', '.join(interest_text), custom_styles['ResumeContent']))
        story.append(Spacer(1, 6))

    def first_page(canvas, doc):
        """Add logo to the first page."""
        canvas.saveState()
        try:
            # Add logo if provided
            if logo_path and os.path.exists(logo_path):
                # Load and resize logo
                with PILImage.open(logo_path) as logo_img:
                    logo_width = 100
                    aspect = logo_img.height / logo_img.width
                    logo_height = logo_width * aspect

                    # Position logo at top center
                    canvas.drawImage(
                        logo_path,
                        (letter[0] - logo_width) / 2,
                        letter[1] - logo_height - 36,
                        width=logo_width,
                        height=logo_height
                    )
        except Exception as e:
            st.error(f"Error in first_page: {str(e)}")
        finally:
            canvas.restoreState()

    def later_pages(canvas, doc):
        """Add logo to later pages."""
        canvas.saveState()
        try:
            if logo_path and os.path.exists(logo_path):
                with PILImage.open(logo_path) as logo_img:
                    logo_width = 100
                    aspect = logo_img.height / logo_img.width
                    logo_height = logo_width * aspect

                    canvas.drawImage(
                        logo_path,
                        (letter[0] - logo_width) / 2,
                        letter[1] - logo_height - 36,
                        width=logo_width,
                        height=logo_height
                    )
        except Exception as e:
            st.error(f"Error in later_pages: {str(e)}")
        finally:
            canvas.restoreState()

    try:
        # Build the PDF with templates
        doc.build(
            story,
            onFirstPage=first_page,
            onLaterPages=later_pages
        )

        # Get the value of the BytesIO buffer
        pdf_bytes = pdf_buffer.getvalue()
        return pdf_bytes

    except Exception as e:
        st.error(f"Error building PDF: {str(e)}")
        return None

    finally:
        # Clean up resources
        pdf_buffer.close()
        if profile_pic_temp and os.path.exists(profile_pic_temp):
            try:
                os.unlink(profile_pic_temp)
            except Exception as e:
                st.error(f"Error cleaning up temporary file: {str(e)}")