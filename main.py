import streamlit as st
import base64
import time
from datetime import datetime

from textpicex import *
from geminiext import *
from pdfgen import *
from wordgen import *



def process_document(file, logo_path, file_extension):
    with tempfile.NamedTemporaryFile(delete=False, suffix="." + file_extension) as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        if file_extension == 'pdf':
            text = get_pdf_text(tmp_file_path)
            images = extract_images_from_pdf(tmp_file_path)
        elif file_extension == 'docx':
            text = get_docx_text(tmp_file_path)
            images = extract_images_from_docx(tmp_file_path)

        if len(text) > 7000:
            extracted_info = extract_info_with_gemini(text)
        else:
            extracted_info = extract_info_with_gemini_mini(text)

        if extracted_info:
            name = extracted_info['personal_info']['name']
            clean_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

            profile_picture = images[0] if images else None

            processed_data = ProcessedData(
                extracted_info=extracted_info,
                profile_picture=profile_picture,
                word_with_pic=create_word_document(extracted_info, profile_picture, logo_path),
                pdf_with_pic=create_pdf_document(extracted_info, profile_picture, logo_path),
                word_without_pic=create_word_document(extracted_info, None, logo_path),
                pdf_without_pic=create_pdf_document(extracted_info, None, logo_path)
            )

            return processed_data

        return None
    finally:
        os.unlink(tmp_file_path)


@st.cache_data
def cached_process_document(file, logo_path, file_extension):
    return process_document(file, logo_path, file_extension)


class ProcessedData:
    def __init__(self, extracted_info=None, profile_picture=None, word_with_pic=None,
                 pdf_with_pic=None, word_without_pic=None, pdf_without_pic=None):
        self.extracted_info = extracted_info
        self.profile_picture = profile_picture
        self.word_with_pic = word_with_pic
        self.pdf_with_pic = pdf_with_pic
        self.word_without_pic = word_without_pic
        self.pdf_without_pic = pdf_without_pic


def initialize_formatting_count():
    """Initialize or load the all-time formatting count."""
    FORMATTING_FILE = 'all_time_resume_formatting.json'

    # Create file if it doesn't exist
    if not os.path.exists(FORMATTING_FILE):
        with open(FORMATTING_FILE, 'w') as f:
            json.dump({
                'total_formats': 0,
                'first_format_timestamp': datetime.now().isoformat()
            }, f)

    # Read current formatting data
    with open(FORMATTING_FILE, 'r') as f:
        formatting_data = json.load(f)

    return formatting_data['total_formats']


def increment_formatting_count():
    """Increment the all-time formatting count."""
    FORMATTING_FILE = 'all_time_resume_formatting.json'

    # Read current formatting data
    with open(FORMATTING_FILE, 'r') as f:
        formatting_data = json.load(f)

    # Increment formatting count
    formatting_data['total_formats'] += 1

    # Write updated data
    with open(FORMATTING_FILE, 'w') as f:
        json.dump(formatting_data, f)

    return formatting_data['total_formats']


def main():
    logo_path = 'logo.png'
    all_time_formats = initialize_formatting_count()
    st.set_page_config(
        page_title="Resume Formatter- CL(V12)",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )

    # Header Section - minimal spacing
    st.markdown("""
        <div class='main-header'>
        <h1>📄 Resume Formatter- CL(V12)</h1>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar for settings and help
    with st.sidebar:
        # Add logo to sidebar
        st.image(logo_path, width=200)
        st.header("⚙️ Settings & Help")
        testing_mode = st.toggle("Testing Mode", value=False)
        if st.button("⚠️ Confirm Clear Session?", key="confirm_clear"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.cache_data.clear()
            st.success("Session has been cleared successfully!")
            st.rerun()
        count_placeholder = st.sidebar.empty()

        # Initial count display
        initial_count = initialize_formatting_count()
        count_placeholder.markdown(f"**Total Resumes Formatted:** {initial_count}")

        st.markdown("---")
        st.subheader("📋 Quick Guide")
        st.markdown("""
            1. Upload a resume (PDF or Word format)
            2. Add an optional profile picture
            3. Sometimes, the system may extract multiple images from the resume. If the extracted profile picture is incorrect, use the Profile Picture Management section to upload a new profile picture.
            4. Download formatted versions
            5. When uploading a new resume, please clear the session by clicking the "Clear Session" button in the section above
            6. If the output is repeating, clear the session and refresh the page
            7. You can edit the content as needed
            8. Recommended: Upload resume in PDF format and download the formatted version in Word document format
            9. Testing mode is only for developers, do not turn it on unless you are a developer 
            10. The updated version also supports the image based resumes but limited to PDF format only \n
            Happy Hiring!!!!
        """)
        st.markdown("---")
        st.subheader("🆘 Need Help?")
        st.markdown("""
            If you encounter any issues, please [upload the resume here](https://cirruslabsio-my.sharepoint.com/:f:/g/personal/mukund_hs_cirruslabs_io/EupXiGkB1dVGn_G6QAORzYoBJ26muiIYDPmviX8KLiGdwA?e=DHQPRC) 
            for assistance.
        """)

    # Main content area
    with st.container():
        # File upload section
        st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
        upload_col1, upload_col2 = st.columns([3, 1])

        with upload_col1:
            uploaded_file = st.file_uploader(
                "📎 Upload a Resume",
                type=["pdf", "docx"],
                help="Supported formats: PDF, Word Document",
                key="document_uploader"
            )

        with upload_col2:
            st.markdown("#### Recommended Format:")
            st.markdown("PDF for uploading, Word format for downloading")
            # st.markdown("- Word format for downloading")

        # Process uploaded file
        if uploaded_file:
            processing_time = None
            st.success("New session has started.")
            st.warning(
                "⚠️ Disclaimer: The formatter may occasionally make errors. Please review the content carefully before downloading the formatted resume.")

            if 'processed_data' not in st.session_state:
                with st.spinner("Processing the resume..."):
                    start_time = time.time()
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    processed_data = cached_process_document(uploaded_file, logo_path, file_extension)
                    st.session_state.processed_data = processed_data
                    end_time = time.time()
                    try:
                        # Only increment count if testing mode is off
                        if not testing_mode:
                            updated_count = increment_formatting_count()
                            count_placeholder.markdown(f"**Total Resumes Formatted:** {updated_count}")
                        else:
                            # When in testing mode, display the initial count
                            count_placeholder.markdown(f"**Total Resumes Formatted:** {initial_count} (Testing Mode)")
                    except Exception as e:
                        st.error(f"Error updating formatting count: {e}")
                        updated_count = initial_count
                processing_time = end_time - start_time

            processed_data = st.session_state.processed_data
            if processed_data and processed_data.extracted_info:
                extracted_info = processed_data.extracted_info
                if processing_time is not None:
                    st.success(f"Resume processed and formatted successfully in {processing_time:.2f} seconds!")
                else:
                    st.success("Resume processed and formatted successfully!")

                st.markdown("# 📝 Resume Content Editor")
                if 'edit_resume' not in st.session_state:
                    st.session_state.edit_resume = False

                    # Edit Resume Button
                if st.button("✏️ Edit Resume Details"):
                    st.session_state.edit_resume = True

                    # Only show editing section if edit mode is active
                if st.session_state.edit_resume:
                    #     #Close Edit Mode Button
                    #     if st.button("❌ Cancel Editing"):
                    #         st.session_state.edit_resume = False
                    #         return
                    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
                        "🧑 Personal Info",
                        "🖥 Professional Summary",
                        "🎯 Career Objective",
                        "🎓 Education",
                        "💼 Experience",
                        "🔃 Projects",
                        "💻 Skills",
                        "🏆 Certifications",
                        "➕ Additional Info"
                    ])

                    # Personal Information Tab (remains the same as previous implementation)
                    with tab1:
                        st.subheader("✏️ Personal Details")
                        col1, col2 = st.columns(2)
                        with col1:
                            extracted_info['personal_info']['name'] = st.text_input(
                                "Full Name", extracted_info['personal_info'].get('name', "")
                            )
                            extracted_info['personal_info']['email'] = st.text_input(
                                "Email", extracted_info['personal_info'].get('email', "")
                            )
                            extracted_info['personal_info']['address'] = st.text_input(
                                "Address", extracted_info['personal_info'].get('address', "")
                            )
                            # Adding Date of Birth input
                            extracted_info['personal_info']['date_of_birth'] = st.text_input(
                                "Date of Birth", extracted_info['personal_info'].get('date_of_birth', "")
                            )

                        with col2:
                            extracted_info['personal_info']['phone'] = st.text_input(
                                "Phone", extracted_info['personal_info'].get('phone', "")
                            )
                            extracted_info['personal_info']['LinkedIn'] = st.text_input(
                                "LinkedIn Profile", extracted_info['personal_info'].get('LinkedIn', "")
                            )
                            # Adding Nationality input
                            extracted_info['personal_info']['nationality'] = st.text_input(
                                "Nationality", extracted_info['personal_info'].get('nationality', "")
                            )
                            # Adding Father's Name input
                            extracted_info['personal_info']['father_name'] = st.text_input(
                                "Father's Name", extracted_info['personal_info'].get('father_name', "")
                            )
                    with tab2:
                        st.subheader("📋 Professional Summary")
                        extracted_info['professional_summary'] = st.text_area(
                            "Professional Summary",
                            value=extracted_info.get('professional_summary', ""),
                            height=200
                        )
                    with tab3:
                        st.subheader("🎯 Career Objective")
                        extracted_info['career_objective'] = st.text_area(
                            "Career Objective",
                            value=extracted_info.get('career_objective', ""),
                            height=150
                        )
                    # Education Tab (from previous implementation)
                    with tab4:
                        st.subheader("🎓 Educational Background")
                        education = extracted_info.get('education', [])

                        for i in range(len(education)):
                            with st.expander(f"Education {i + 1}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    education[i]['degree'] = st.text_input(f"Degree", education[i].get('degree', ""),
                                                                           key=f"edu_degree_{i}")
                                with col2:
                                    education[i]['institution'] = st.text_input(f"Institution",
                                                                                education[i].get('institution', ""),
                                                                                key=f"edu_institution_{i}")
                                with col3:
                                    education[i]['year'] = st.text_input(f"Graduation Year",
                                                                         education[i].get('year', ""),
                                                                         key=f"edu_year_{i}")
                                education[i]['details'] = st.text_area(f"Additional Details",
                                                                       education[i].get('details', ""),
                                                                       key=f"edu_details_{i}")

                                if st.button(f"🗑️ Remove Education {i + 1}", key=f"delete_edu_{i}"):
                                    education.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Education"):
                            education.append({
                                'degree': '',
                                'institution': '',
                                'year': '',
                                'details': ''
                            })
                            st.rerun()

                        extracted_info['education'] = education

                    # Experience Tab (similar to previous implementation)
                    with tab5:
                        st.subheader("💼 Professional Experience")
                        experience = extracted_info.get('experience', [])

                        for i in range(len(experience)):
                            with st.expander(f"Experience {i + 1}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    experience[i]['title'] = st.text_input(f"Job Title", experience[i].get('title', ""),
                                                                           key=f"exp_title_{i}")
                                    experience[i]['company'] = st.text_input(f"Company",
                                                                             experience[i].get('company', ""),
                                                                             key=f"exp_company_{i}")
                                with col2:
                                    experience[i]['duration'] = st.text_input(f"Duration",
                                                                              experience[i].get('duration', ""),
                                                                              key=f"exp_duration_{i}")

                                responsibilities = "\n".join(experience[i].get('responsibilities', []))
                                experience[i]['responsibilities'] = st.text_area(
                                    f"Key Responsibilities", responsibilities, key=f"exp_resp_{i}"
                                ).split("\n")

                                if st.button(f"🗑️ Remove Experience {i + 1}", key=f"delete_exp_{i}"):
                                    experience.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Experience"):
                            experience.append({
                                'title': '',
                                'company': '',
                                'duration': '',
                                'responsibilities': []
                            })
                            st.rerun()

                        extracted_info['experience'] = experience

                    # Projects Tab
                    with tab6:
                        st.subheader("🚀 Projects")
                        projects = extracted_info.get('projects', [])

                        for i in range(len(projects)):
                            with st.expander(f"Project {i + 1}"):
                                projects[i]['name'] = st.text_input(f"Project Name", projects[i].get('name', ""),
                                                                    key=f"proj_name_{i}")
                                projects[i]['description'] = st.text_area(f"Description",
                                                                          projects[i].get('description', ""),
                                                                          key=f"proj_desc_{i}")
                                projects[i]['technologies'] = st.text_input(
                                    f"Technologies Used", projects[i].get('technologies', ""), key=f"proj_tech_{i}"
                                )

                                if st.button(f"🗑️ Remove Project {i + 1}", key=f"delete_proj_{i}"):
                                    projects.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Project"):
                            projects.append({
                                'name': '',
                                'description': '',
                                'technologies': ''
                            })
                            st.rerun()

                        extracted_info['projects'] = projects

                    # Skills Tab
                    with tab7:
                        st.subheader("🛠️ Skills")

                        # Get all skill categories
                        technical_skills = extracted_info['skills'].get('technical', {})

                        # Convert categories to a list for easier row management
                        categories = list(technical_skills.keys())

                        # Iterate through categories in rows of 2
                        for i in range(0, len(categories), 3):
                            # Create a row of 2 columns
                            cols = st.columns(2)

                            # Process first category in the row
                            with cols[0]:
                                category = categories[i]
                                skills = technical_skills[category]
                                skills_str = ", ".join(skills) if skills else ""

                                edited_skills_str = st.text_area(
                                    f"{category} Skills",
                                    skills_str,
                                    key=f"skills_{category}"
                                )

                                # Process edited skills
                                edited_skills = [
                                    skill.strip() for skill in edited_skills_str.split(',')
                                    if skill.strip()
                                ]

                                if edited_skills:
                                    technical_skills[category] = edited_skills

                            # Process second category in the row (if exists)
                            if i + 1 < len(categories):
                                with cols[1]:
                                    category = categories[i + 1]
                                    skills = technical_skills[category]
                                    skills_str = ", ".join(skills) if skills else ""

                                    edited_skills_str = st.text_area(
                                        f"{category} Skills",
                                        skills_str,
                                        key=f"skills_{category}"
                                    )

                                    # Process edited skills
                                    edited_skills = [
                                        skill.strip() for skill in edited_skills_str.split(',')
                                        if skill.strip()
                                    ]

                                    if edited_skills:
                                        technical_skills[category] = edited_skills

                        # Update the skills in extracted_info
                        extracted_info['skills']['technical'] = technical_skills

                        # Soft Skills (Optional: you can adjust placement as needed)
                        st.markdown("#### Soft Skills")
                        soft_skills_str = ", ".join(extracted_info['skills'].get('soft', []))

                        edited_soft_skills_str = st.text_area(
                            "Soft Skills",
                            soft_skills_str,
                            key="soft_skills"
                        )

                        extracted_info['skills']['soft'] = [
                            skill.strip() for skill in edited_soft_skills_str.split(',')
                            if skill.strip()
                        ]
                    # Certifications Tab
                    with tab8:
                        st.subheader("🏆 Certifications")
                        certifications = extracted_info.get('courses_and_certifications', [])

                        for i in range(len(certifications)):
                            with st.expander(f"Certification {i + 1}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    certifications[i]['name'] = st.text_input(f"Certification Name",
                                                                              certifications[i].get('name', ""),
                                                                              key=f"cert_name_{i}")
                                    certifications[i]['issuer'] = st.text_input(f"Issuer",
                                                                                certifications[i].get('issuer', ""),
                                                                                key=f"cert_issuer_{i}")
                                with col2:
                                    certifications[i]['year'] = st.text_input(f"Year",
                                                                              certifications[i].get('year', ""),
                                                                              key=f"cert_year_{i}")
                                    certifications[i]['type'] = st.text_input(f"Type",
                                                                              certifications[i].get('type', ""),
                                                                              key=f"cert_type_{i}")

                                if st.button(f"🗑️ Remove Certification {i + 1}", key=f"delete_cert_{i}"):
                                    certifications.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Certification"):
                            certifications.append({
                                'name': '',
                                'issuer': '',
                                'year': '',
                                'type': ''
                            })
                            st.rerun()

                        extracted_info['courses_and_certifications'] = certifications

                    # Additional Information Tab
                    with tab9:
                        st.subheader("➕ Additional Information")
                        additional_sections = extracted_info.get('additional_sections', {})

                        # Achievements
                        st.markdown("#### 🏅 Achievements")
                        achievements = additional_sections.get('achievements', [])

                        for i in range(len(achievements)):
                            with st.expander(f"Achievement {i + 1}"):
                                achievements[i]['title'] = st.text_input(f"Title", achievements[i].get('title', ""),
                                                                         key=f"ach_title_{i}")
                                achievements[i]['description'] = st.text_area(f"Description",
                                                                              achievements[i].get('description', ""),
                                                                              key=f"ach_desc_{i}")
                                achievements[i]['year'] = st.text_input(f"Year", achievements[i].get('year', ""),
                                                                        key=f"ach_year_{i}")

                                if st.button(f"🗑️ Remove Achievement {i + 1}", key=f"delete_ach_{i}"):
                                    achievements.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Achievement"):
                            achievements.append({
                                'title': '',
                                'description': '',
                                'year': ''
                            })
                            st.rerun()

                        additional_sections['achievements'] = achievements

                        # Volunteer Work
                        st.markdown("#### 🤝 Volunteer Work")
                        volunteer_work = additional_sections.get('volunteer_work', [])

                        for i in range(len(volunteer_work)):
                            with st.expander(f"Volunteer Work {i + 1}"):
                                volunteer_work[i]['organization'] = st.text_input(f"Organization",
                                                                                  volunteer_work[i].get('organization',
                                                                                                        ""),
                                                                                  key=f"vol_org_{i}")
                                volunteer_work[i]['role'] = st.text_input(f"Role", volunteer_work[i].get('role', ""),
                                                                          key=f"vol_role_{i}")
                                volunteer_work[i]['duration'] = st.text_input(f"Duration",
                                                                              volunteer_work[i].get('duration', ""),
                                                                              key=f"vol_duration_{i}")
                                volunteer_work[i]['description'] = st.text_area(f"Description",
                                                                                volunteer_work[i].get('description',
                                                                                                      ""),
                                                                                key=f"vol_desc_{i}")

                                if st.button(f"🗑️ Remove Volunteer Work {i + 1}", key=f"delete_vol_{i}"):
                                    volunteer_work.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Volunteer Work"):
                            volunteer_work.append({
                                'organization': '',
                                'role': '',
                                'duration': '',
                                'description': ''
                            })
                            st.rerun()

                        additional_sections['volunteer_work'] = volunteer_work
                        st.markdown("#### 🌐 Languages")
                        languages = additional_sections.get('languages', [])

                        for i in range(len(languages)):
                            with st.expander(f"Language {i + 1}"):
                                languages[i]['language'] = st.text_input(f"Language", languages[i].get('language', ""),
                                                                         key=f"lang_{i}")
                                languages[i]['proficiency'] = st.text_input(f"Proficiency",
                                                                            languages[i].get('proficiency', ""),
                                                                            key=f"lang_prof_{i}")

                                if st.button(f"🗑️ Remove Language {i + 1}", key=f"delete_lang_{i}"):
                                    languages.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Language"):
                            languages.append({
                                'language': '',
                                'proficiency': ''
                            })
                            st.rerun()

                        additional_sections['languages'] = languages

                        # Awards
                        st.markdown("#### 🏆 Awards")
                        awards = additional_sections.get('awards', [])

                        for i in range(len(awards)):
                            with st.expander(f"Award {i + 1}"):
                                awards[i]['name'] = st.text_input(f"Award Name", awards[i].get('name', ""),
                                                                  key=f"award_name_{i}")
                                awards[i]['issuer'] = st.text_input(f"Issuer", awards[i].get('issuer', ""),
                                                                    key=f"award_issuer_{i}")
                                awards[i]['year'] = st.text_input(f"Year", awards[i].get('year', ""),
                                                                  key=f"award_year_{i}")

                                if st.button(f"🗑️ Remove Award {i + 1}", key=f"delete_award_{i}"):
                                    awards.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Award"):
                            awards.append({
                                'name': '',
                                'issuer': '',
                                'year': ''
                            })
                            st.rerun()

                        additional_sections['awards'] = awards

                        # Publications
                        st.markdown("#### 📚 Publications")
                        publications = additional_sections.get('publications', [])

                        for i in range(len(publications)):
                            with st.expander(f"Publication {i + 1}"):
                                publications[i]['title'] = st.text_input(f"Title", publications[i].get('title', ""),
                                                                         key=f"pub_title_{i}")
                                publications[i]['authors'] = st.text_input(f"Authors",
                                                                           publications[i].get('authors', ""),
                                                                           key=f"pub_authors_{i}")
                                publications[i]['publication_venue'] = st.text_input(f"Publication Venue",
                                                                                     publications[i].get(
                                                                                         'publication_venue', ""),
                                                                                     key=f"pub_venue_{i}")
                                publications[i]['year'] = st.text_input(f"Year", publications[i].get('year', ""),
                                                                        key=f"pub_year_{i}")

                                if st.button(f"🗑️ Remove Publication {i + 1}", key=f"delete_pub_{i}"):
                                    publications.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Publication"):
                            publications.append({
                                'title': '',
                                'authors': '',
                                'publication_venue': '',
                                'year': ''
                            })
                            st.rerun()

                        additional_sections['publications'] = publications

                        # Professional Memberships
                        st.markdown("#### 🤝 Professional Memberships")
                        professional_memberships = additional_sections.get('professional_memberships', [])

                        for i in range(len(professional_memberships)):
                            with st.expander(f"Membership {i + 1}"):
                                professional_memberships[i]['organization'] = st.text_input(f"Organization",
                                                                                            professional_memberships[
                                                                                                i].get(
                                                                                                'organization', ""),
                                                                                            key=f"membership_org_{i}")
                                professional_memberships[i]['role'] = st.text_input(f"Role",
                                                                                    professional_memberships[i].get(
                                                                                        'role',
                                                                                        ""),
                                                                                    key=f"membership_role_{i}")
                                professional_memberships[i]['year'] = st.text_input(f"Year",
                                                                                    professional_memberships[i].get(
                                                                                        'year',
                                                                                        ""),
                                                                                    key=f"membership_year_{i}")

                                if st.button(f"🗑️ Remove Membership {i + 1}", key=f"delete_membership_{i}"):
                                    professional_memberships.pop(i)
                                    st.rerun()

                        if st.button("➕ Add Professional Membership"):
                            professional_memberships.append({
                                'organization': '',
                                'role': '',
                                'year': ''
                            })
                            st.rerun()

                        additional_sections['professional_memberships'] = professional_memberships

                        # Update additional sections in extracted info
                        extracted_info['additional_sections'] = additional_sections
                        # Interests and Hobbies
                        st.markdown("#### 🌟 Interests and Hobbies")
                        interests_and_hobbies = additional_sections.get('interests_and_hobbies', [])

                        # Create a container to manage interests and hobbies
                        for i in range(len(interests_and_hobbies)):
                            with st.expander(f"Interest/Hobby {i + 1}"):
                                # Name input with dynamic key
                                interests_and_hobbies[i]['name'] = st.text_input(
                                    "Name",
                                    interests_and_hobbies[i].get('name', ""),
                                    key=f"interest_hobby_name_{i}"
                                )

                                # Description input with dynamic key
                                interests_and_hobbies[i]['description'] = st.text_input(
                                    "Description",
                                    interests_and_hobbies[i].get('description', ""),
                                    key=f"interest_hobby_description_{i}"
                                )

                                # Remove interest/hobby button
                                if st.button(f"🗑️ Remove Interest/Hobby {i + 1}", key=f"delete_interest_hobby_{i}"):
                                    interests_and_hobbies.pop(i)
                                    st.rerun()

                        # Add new interest/hobby button
                        if st.button("➕ Add Interest or Hobby"):
                            interests_and_hobbies.append({
                                'name': '',
                                'description': ''
                            })
                            st.rerun()

                        # Update additional sections with modified interests and hobbies
                        additional_sections['interests_and_hobbies'] = interests_and_hobbies
                        extracted_info['additional_sections'] = additional_sections

                    # Save Changes Button
                    if st.button("💾 Save Changes and Regenerate", type="primary"):
                        st.session_state.processed_data.extracted_info = extracted_info
                        st.success("✅ Changes saved successfully!")

                        # Regenerate Documents logic
                        with st.spinner("Regenerating documents..."):
                            profile_picture = processed_data.profile_picture
                            processed_data.word_with_pic = create_word_document(extracted_info, profile_picture,
                                                                                logo_path)
                            processed_data.pdf_with_pic = create_pdf_document(extracted_info, profile_picture,
                                                                              logo_path)
                            processed_data.word_without_pic = create_word_document(extracted_info, None, logo_path)
                            processed_data.pdf_without_pic = create_pdf_document(extracted_info, None, logo_path)
                            st.session_state.processed_data = processed_data

                # Profile Picture Management
                st.markdown("### 📸 Profile Picture Management")
                upload_col1, _ = st.columns([3, 1])

                with upload_col1:
                    # Show current profile picture status
                    has_profile_picture = hasattr(processed_data,
                                                  'profile_picture') and processed_data.profile_picture is not None

                    if has_profile_picture:
                        st.success("✅ Profile picture added successfully")
                        if st.button("❌ Remove Profile Picture"):
                            processed_data.profile_picture = None
                            processed_data.word_with_pic = processed_data.word_without_pic
                            processed_data.pdf_with_pic = processed_data.pdf_without_pic
                            st.session_state.processed_data = processed_data
                            st.success("Profile picture removed!")
                            st.rerun()

                    # Profile picture upload
                    uploaded_profile = st.file_uploader(
                        "Upload Profile Picture",
                        type=["png", "jpg", "jpeg"],
                        key="profile_uploader",
                        help="Recommended size: 200x200 pixels"
                    )

                    if uploaded_profile:
                        try:
                            profile_image = PILImage.open(uploaded_profile)
                            st.image(profile_image, caption="Preview", width=200)

                            if st.button("✅ Confirm Picture"):
                                with st.spinner("Updating documents..."):
                                    max_size = (400, 400)
                                    if profile_image.size[0] > max_size[0] or profile_image.size[1] > max_size[1]:
                                        profile_image.thumbnail(max_size, PILImage.LANCZOS)

                                    word_with_pic = create_word_document(extracted_info, profile_image, logo_path)
                                    pdf_with_pic = create_pdf_document(extracted_info, profile_image, logo_path)
                                    processed_data.word_with_pic = word_with_pic
                                    processed_data.pdf_with_pic = pdf_with_pic
                                    processed_data.profile_picture = profile_image
                                    st.session_state.processed_data = processed_data
                                    st.success("✨ Profile picture updated successfully!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ Error processing image: {str(e)}")

                # Download Section
                st.markdown("### 📥 Download Options")
                name = extracted_info['personal_info']['name']
                clean_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

                # Preview and Download columns
                preview_col, download_col = st.columns([4, 1])

                with preview_col:
                    st.subheader("📄 Preview")
                    if processed_data.pdf_with_pic:
                        base64_pdf = base64.b64encode(processed_data.pdf_with_pic).decode('utf-8')
                        pdf_display = f'''
                            <object data="data:application/pdf;base64,{base64_pdf}" 
                                    type="application/pdf" 
                                    width="100%" 
                                    height="800px">
                                <p>Your browser doesn't support PDF viewing. 
                                <a href="data:application/pdf;base64,{base64_pdf}" download>Download PDF</a> instead.</p>
                            </object>
                            '''
                        st.markdown(pdf_display, unsafe_allow_html=True)
                        

                with download_col:
                    st.subheader("💾 Download Files")

                    if processed_data.pdf_with_pic and processed_data.profile_picture is not None:
                        st.markdown("##### With Profile Picture")
                        st.download_button(
                            label="📑 Download PDF (with picture)",
                            data=processed_data.pdf_with_pic,
                            file_name=f"{clean_name}_resume_with_pic.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.download_button(
                            label="📝 Download Word (with picture)",
                            data=processed_data.word_with_pic,
                            file_name=f"{clean_name}_resume_with_pic.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )

                    st.markdown("##### Without Profile Picture")
                    st.download_button(
                        label="📑 Download PDF (no picture)",
                        data=processed_data.pdf_without_pic,
                        file_name=f"{clean_name}_resume_without_pic.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.download_button(
                        label="📝 Download Word (no picture)",
                        data=processed_data.word_without_pic,
                        file_name=f"{clean_name}_resume_without_pic.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            else:
                st.error("⚠️ Failed to process the document. Please try again.")


if __name__ == "__main__":
    main()