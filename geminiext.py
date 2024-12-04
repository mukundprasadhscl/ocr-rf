from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import re
import json
import os

# Load environment variables
load_dotenv()
genai_api_key = os.getenv("GOOGLE_API_KEY")



def extract_info_with_gemini_mini(text):
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.01)

    # Combined Prompt 1: Personal Info, Education, and Experience
    combined_personal_experience_prompt = f"""
    You are a highly capable resume analysis assistant. Given a resume text, extract and return the following information in JSON format:
    {{
        "personal_info": {{
            "name": "",
            "email": "",
            "phone": "",
            "address": "",
            "LinkedIn": "",
            "date_of_birth": "",
            "nationality": "",
            "father_name": ""
        }},
        "professional_summary": "",
        "career_objective": "",
        "education": [
            {{
                "degree": "",
                "institution": "",
                "year": "",
                "details": ""
            }}
        ],
        "experience": [
            {{
                "title": "",
                "company": "",
                "duration": "",
                "responsibilities": []
            }}
        ]
    }}

    Resume Text: {text}

    Please follow these guidelines:
    1. Place only valid LinkedIn URLs in "LinkedIn".
    2. If name is not present then put name as "Unknown".
    3. If any fields are absent leave it as blank.
    4. Sometimes responsibilities can also be in one sentence or a one line description.


    Return only the JSON object with the extracted information, maintaining the exact structure shown above.
    """

    # Combined Prompt 2: Projects, Skills, and Additional Sections
    combined_projects_skills_other_prompt = f"""
    You are a highly capable resume analysis assistant. Given a resume text, extract and return the following information in JSON format:
    {{
        "projects": [
            {{
                "name": "",
                "description": "",
                "technologies": ""
            }}
        ],
        "skills": {{
            "technical": {{
                "Programming Languages": [],
                "Scripting Languages": [],
                "Databases": [],
                "Monitoring tools": [],
                "Version controllers": [],
                "Operating systems": [],
                "Cloud": [],
                "Devops": [],
                "IAC": [],
                "Automation Tools": [],
                "Data visualization or Report tools ": [],
                "Project Management Tools": [],
                "Full stack": [],
                "App Development": [],
                "IDEs": [],
                "Markup Languages": [],
                "Machine Learning": [],
                "Others": []
            }},
            "soft": []
        }},
        "courses_and_certifications": [
            {{
                "name": "",
                "issuer": "",
                "year": "",
                "type": ""
            }}
        ],
        "additional_sections": {{
            "achievements": [
                {{
                    "title": "",
                    "description": "",
                    "year": ""
                }}
            ],
            "volunteer_work": [
                {{
                    "organization": "",
                    "role": "",
                    "duration": "",
                    "description": ""
                }}
            ],
            "languages": [
                {{
                    "language": "",
                    "proficiency": ""
                }}
            ],
            "awards": [
                {{
                    "name": "",
                    "issuer": "",
                    "year": ""
                }}
            ],
            "publications": [
                {{
                    "title": "",
                    "authors": "",
                    "publication_venue": "",
                    "year": ""
                }}
            ],
            "professional_memberships": [
                {{
                    "organization": "",
                    "role": "",
                    "year": ""
                }}
            ],
            "interests_and_hobbies": [ 
            {{ 
            "name": "", 
            "description": "" 
            }} 
            ]
        }}
    }}

    Resume Text: {text}

    Please follow these guidelines:
    1. Categorize technical skills appropriately. If uncertain, place them in "Others".
    2. Do not combine the skills data with project or professional experience tech stack.
    3. Extract information for all possible sections.
    4. If any fields are absent, leave them blank.
    5. Do not fabricate information.


    Return only the JSON object with the extracted information, maintaining the exact structure shown above.
    """

    def extract_json_from_response(response):
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return None
        return None

    responses = {
        'personal_experience': extract_json_from_response(model.predict(combined_personal_experience_prompt)),
        'projects_skills_other': extract_json_from_response(model.predict(combined_projects_skills_other_prompt))
    }

    # Combine all responses
    combined_data = {
        'personal_info': responses['personal_experience'].get('personal_info', {}) if responses[
            'personal_experience'] else {},
        'professional_summary': responses['personal_experience'].get('professional_summary', '') if responses[
            'personal_experience'] else '',
        'career_objective': responses['personal_experience'].get('career_objective', '') if responses[
            'personal_experience'] else '',
        'education': responses['personal_experience'].get('education', []) if responses['personal_experience'] else [],
        'experience': responses['personal_experience'].get('experience', []) if responses[
            'personal_experience'] else [],
        'projects': responses['projects_skills_other'].get('projects', []) if responses[
            'projects_skills_other'] else [],
        'skills': responses['projects_skills_other'].get('skills', {}) if responses['projects_skills_other'] else {},
        'courses_and_certifications': responses['projects_skills_other'].get('courses_and_certifications', []) if
        responses['projects_skills_other'] else [],
        'additional_sections': responses['projects_skills_other'].get('additional_sections', {}) if responses[
            'projects_skills_other'] else {}
    }

    #return combined_data

    # Update expected_structure
    expected_structure = {
        "personal_info": {
            "name": "Unknown",
            "email": "",
            "phone": "",
            "address": "",
            "LinkedIn": "",
            "date_of_birth": "",
            "nationality": "",
            "father_name": ""

        },
        "professional_summary": "",
        "career_objective": "",
        "education": [
            {
                "degree": "",
                "institution": "",
                "year": "",
                "details": ""
            }
        ],
        "experience": [
            {
                "title": "",
                "company": "",
                "duration": "",
                "responsibilities": []
            }
        ],
        "projects": [
            {
                "name": "",
                "description": "",
                "technologies": ""
            }
        ],
        "skills": {
            "technical": [],
            "soft": []
        },
        "courses_and_certifications": [
            {
                "name": "",
                "issuer": "",
                "year": "",
                "type": ""
            }
        ],
        # New section
        "additional_sections": {
            "achievements": [
                {
                    "title": "",
                    "description": "",
                    "year": ""
                }
            ],
            "volunteer_work": [
                {
                    "organization": "",
                    "role": "",
                    "duration": "",
                    "description": ""
                }
            ],
            "languages": [
                {
                    "language": "",
                    "proficiency": ""
                }
            ],
            "awards": [
                {
                    "name": "",
                    "issuer": "",
                    "year": ""
                }
            ],
            "publications": [
                {
                    "title": "",
                    "authors": "",
                    "publication_venue": "",
                    "year": ""
                }
            ],
            "professional_memberships": [
                {
                    "organization": "",
                    "role": "",
                    "year": ""
                }
            ],
            "interests_and_hobbies": [
                {
                    "name": "",
                    "description": ""
                }
            ]
        }
    }

    # Fill in missing subfields with defaults
    def fill_defaults(data, structure):
        if isinstance(data, list) and isinstance(structure, list):
            default_item = structure[0] if structure else {}
            return [fill_defaults(item, default_item) for item in data]
        elif isinstance(data, dict) and isinstance(structure, dict):
            return {
                key: fill_defaults(data.get(key, ""), structure[key])
                for key in structure
            }
        else:
            return data if data else ""

    filled_data = fill_defaults(combined_data, expected_structure)

    # Validate LinkedIn URL
    linkedin_url = filled_data['personal_info'].get('LinkedIn', '')
    if linkedin_url and not re.match(r'https?://(www\.)?linkedin\.com/', linkedin_url):
        filled_data['personal_info'].setdefault('other_links', []).append(linkedin_url)
        filled_data['personal_info']['LinkedIn'] = ""

    return filled_data


def extract_info_with_gemini(text):
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1)

    # Prompt 1: Personal Info and Education
    personal_info_prompt = f"""
    You are a highly capable resume analysis assistant. Given a resume text, extract and return the following information in JSON format:
    {{
        "personal_info": {{
            "name": "",
            "email": "",
            "phone": "",
            "address": "",
            "LinkedIn": "",
            "date_of_birth": "",
            "nationality": "",
            "father_name": ""

        }},
        "professional_summary": "",
        "career_objective": "",
        "education": [
            {{
                "degree": "",
                "institution": "",
                "year": "",
                "details": ""
            }}
        ]
    }}

    Resume Text: {text}

    Please follow these guidelines:
    1. Place only valid LinkedIn URLs in "LinkedIn".
    2. If name is not present then put name as "Unknown".
    3. If any fields are absent, leave it as blank.


    Return only the JSON object with the extracted information, maintaining the exact structure shown above.
    """

    # Prompt 2: Experience
    experience_prompt = f"""
    You are a highly capable resume analysis assistant. Given a resume text, extract and return the following information in JSON format:
    {{
        "experience": [
            {{
                "title": "",
                "company": "",
                "duration": "",
                "responsibilities": []
            }}
        ]
    }}

    Resume Text: {text}
    Return only the JSON object with the extracted information, maintaining the exact structure shown above.
    """

    # Prompt 3: Projects
    projects_prompt = f"""
    You are a highly capable document analysis assistant. Given a resume text, extract and return the following information in JSON format:
    {{
        "projects": [
            {{
                "name": "",
                "description": "",
                "technologies": ""
            }}
        ]
    }}

    Resume Text: {text}
    Please follow these guidelines:
    1. If any fields are absent, leave it as blank.

    Return only the JSON object with the extracted information, maintaining the exact structure shown above.
    """

    # Prompt 4: Skills and Certifications
    skills_cert_prompt = f"""
    You are a highly capable resume analysis assistant. Given a resume text, extract and group technical skills into appropriate categories in JSON format:
    {{
        "skills": {{
            "technical": {{
                "Programming Languages": [],
                "Scripting Languages": [],
                "Databases": [],
                "Monitoring tools": [],
                "Version controllers": [],
                "Operating systems": [],
                "Cloud": [],
                "Devops": [],
                "IAC": [],
                "Automation Tools": [],
                "Data visualization or Report tools ": [],
                "Project Management Tools": [],
                "Full stack": [],
                "App Development": [],
                "IDEs": [],
                "Markup Languages": [],
                "Machine Learning": [],
                "Others": []
            }},
            "soft": []
        }},
        "courses_and_certifications": [
            {{
                "name": "",
                "issuer": "",
                "year": "",
                "type": ""
            }}
        ]
    }}

    Resume Text: {text}

    Please follow these guidelines:
    1. Categorize technical skills appropriately. If uncertain, place them in "Others".
    2. Do not combine the skills data with project or professional experience tech stack.
    3. If any fields are absent, leave them blank.

    Return only the JSON object with the extracted information, maintaining the exact structure shown above.
    """
    other_sections_prompt = f"""
    You are a highly capable resume analysis assistant. Given a resume text, extract and return additional important sections not covered in previous prompts in JSON format:
    {{
        "additional_sections": {{
            "achievements": [
                {{
                    "title": "",
                    "description": "",
                    "year": ""
                }}
            ],
            "volunteer_work": [
                {{
                    "organization": "",
                    "role": "",
                    "duration": "",
                    "description": ""
                }}
            ],
            "languages": [
                {{
                    "language": "",
                    "proficiency": ""
                }}
            ],
            "awards": [
                {{
                    "name": "",
                    "issuer": "",
                    "year": ""
                }}
            ],
            "publications": [
                {{
                    "title": "",
                    "authors": "",
                    "publication_venue": "",
                    "year": ""
                }}
            ],
            "professional_memberships": [
                {{
                    "organization": "",
                    "role": "",
                    "year": ""
                }}
            ],
            "interests_and_hobbies": [ 
            {{ 
            "name": "", 
            "description": "" 
            }} 
            ]
        }}
    }}

    Resume Text: {text}

    Please follow these guidelines:
    1. Extract information for sections that are present in the resume.
    2. If any fields are not present, leave them blank.
    3. Do not fabricate information.

    Return only the JSON object with the extracted information, maintaining the exact structure shown above.
    """

    def extract_json_from_response(response):
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return None
        return None

    responses = {
        'personal': extract_json_from_response(model.predict(personal_info_prompt)),
        'experience': extract_json_from_response(model.predict(experience_prompt)),
        'projects': extract_json_from_response(model.predict(projects_prompt)),
        'skills_cert': extract_json_from_response(model.predict(skills_cert_prompt)),
        'other_sections': extract_json_from_response(model.predict(other_sections_prompt))  # New line
    }

    # Combine all responses
    combined_data = {
        'personal_info': responses['personal'].get('personal_info', {}) if responses['personal'] else {},
        'professional_summary': responses['personal'].get('professional_summary', '') if responses['personal'] else '',
        'career_objective': responses['personal'].get('career_objective', '') if responses['personal'] else '',
        'education': responses['personal'].get('education', []) if responses['personal'] else [],
        'experience': responses['experience'].get('experience', []) if responses['experience'] else [],
        'projects': responses['projects'].get('projects', []) if responses['projects'] else [],
        'skills': responses['skills_cert'].get('skills', {}) if responses['skills_cert'] else {},
        'courses_and_certifications': responses['skills_cert'].get('courses_and_certifications', []) if responses[
            'skills_cert'] else [],
        'additional_sections': responses['other_sections'].get('additional_sections', {}) if responses[
            'other_sections'] else {}  # New line
    }

    # Update expected_structure
    expected_structure = {
        "personal_info": {
            "name": "Unknown",
            "email": "",
            "phone": "",
            "address": "",
            "LinkedIn": "",
            "date_of_birth": "",
            "nationality": "",
            "father_name": "",
        },
        "professional_summary": "",
        "career_objective": "",
        "education": [
            {
                "degree": "",
                "institution": "",
                "year": "",
                "details": ""
            }
        ],
        "experience": [
            {
                "title": "",
                "company": "",
                "duration": "",
                "responsibilities": []
            }
        ],
        "projects": [
            {
                "name": "",
                "description": "",
                "technologies": ""
            }
        ],
        "skills": {
            "technical": [],
            "soft": []
        },
        "courses_and_certifications": [
            {
                "name": "",
                "issuer": "",
                "year": "",
                "type": ""
            }
        ],
        # New section
        "additional_sections": {
            "achievements": [
                {
                    "title": "",
                    "description": "",
                    "year": ""
                }
            ],
            "volunteer_work": [
                {
                    "organization": "",
                    "role": "",
                    "duration": "",
                    "description": ""
                }
            ],
            "languages": [
                {
                    "language": "",
                    "proficiency": ""
                }
            ],
            "awards": [
                {
                    "name": "",
                    "issuer": "",
                    "year": ""
                }
            ],
            "publications": [
                {
                    "title": "",
                    "authors": "",
                    "publication_venue": "",
                    "year": ""
                }
            ],
            "professional_memberships": [
                {
                    "organization": "",
                    "role": "",
                    "year": ""
                }
            ],
            "interests_and_hobbies": [
                {
                    "name": "",
                    "description": ""
                }
            ]
        }
    }

    # Fill in missing subfields with defaults
    def fill_defaults(data, structure):
        if isinstance(data, list) and isinstance(structure, list):
            default_item = structure[0] if structure else {}
            return [fill_defaults(item, default_item) for item in data]
        elif isinstance(data, dict) and isinstance(structure, dict):
            return {
                key: fill_defaults(data.get(key, ""), structure[key])
                for key in structure
            }
        else:
            return data if data else ""

    filled_data = fill_defaults(combined_data, expected_structure)

    # Validate LinkedIn URL
    linkedin_url = filled_data['personal_info'].get('LinkedIn', '')
    if linkedin_url and not re.match(r'https?://(www\.)?linkedin\.com/', linkedin_url):
        filled_data['personal_info']['other_links'].append(linkedin_url)
        filled_data['personal_info']['LinkedIn'] = ""

    return filled_data


