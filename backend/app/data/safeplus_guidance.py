from __future__ import annotations


SAFEPLUS_GUIDANCE_SOURCES: list[
    dict[str, object]
] = [
    {
        "source_id": "WS-SP-OVERVIEW",
        "title": "SafePlus",
        "url": (
            "https://www.worksafe.govt.nz/"
            "managing-health-and-safety/"
            "businesses/safeplus/"
        ),
        "guidance": [
            (
                "SafePlus is a voluntary workplace health "
                "and safety performance improvement toolkit."
            ),
            (
                "SafePlus is intended to support continuous "
                "improvement rather than operate only as a "
                "minimum-compliance checklist."
            ),
            (
                "Organisations can use SafePlus resources, "
                "self-assessments, case studies, and onsite "
                "assessment services to understand current "
                "performance and identify improvements."
            ),
        ],
    },
    {
        "source_id": "WS-SP-ABOUT",
        "title": "About SafePlus",
        "url": (
            "https://www.worksafe.govt.nz/"
            "managing-health-and-safety/"
            "businesses/safeplus/about-safeplus/"
        ),
        "guidance": [
            (
                "SafePlus provides a model of what good "
                "health and safety practices and performance "
                "look like."
            ),
            (
                "SafePlus supports organisations in "
                "understanding current practices and starting "
                "positive, ongoing change."
            ),
            (
                "The framework was developed by WorkSafe "
                "New Zealand, ACC, and the Ministry of "
                "Business, Innovation and Employment."
            ),
        ],
    },
    {
        "source_id": "WS-SP-SELF-ASSESSMENT",
        "title": (
            "SafePlus self-assessment resources"
        ),
        "url": (
            "https://www.worksafe.govt.nz/"
            "managing-health-and-safety/"
            "businesses/safeplus/"
            "safeplus-self-assessment-resources/"
        ),
        "guidance": [
            (
                "A SafePlus self-assessment gathers feedback "
                "from people throughout a business, including "
                "owners, senior managers, and frontline "
                "workers."
            ),
            (
                "The purpose of the survey is to help an "
                "organisation understand whether its health "
                "and safety practices are working well and "
                "where improvement is needed."
            ),
            (
                "The SafePlus framework focuses on three key "
                "areas: Leadership, Worker Engagement, and "
                "Risk Management."
            ),
            (
                "Differences between worker and management "
                "perspectives can provide useful evidence of "
                "areas requiring further discussion and "
                "investigation."
            ),
        ],
    },
    {
        "source_id": "WS-SP-ONSITE",
        "title": "SafePlus onsite assessment",
        "url": (
            "https://www.worksafe.govt.nz/"
            "managing-health-and-safety/"
            "businesses/safeplus/"
            "onsite-assessment-and-advisory-service/"
        ),
        "guidance": [
            (
                "An onsite assessment examines health and "
                "safety Leadership, Worker Engagement, and "
                "Risk Management."
            ),
            (
                "Assessment should look beyond documented "
                "plans and procedures by observing how people "
                "work and talking with people across different "
                "levels of the organisation."
            ),
            (
                "Assessments should consider how beliefs, "
                "attitudes, relationships, and decision-making "
                "influence health and safety practice."
            ),
            (
                "Results should identify what is working well, "
                "barriers to safer work, and areas where "
                "investment and improvement are needed."
            ),
            (
                "Assessment results should be converted into "
                "practical improvement actions and reviewed as "
                "the organisation and its risks change."
            ),
        ],
    },
    {
        "source_id": "WS-SP-METHODOLOGY",
        "title": (
            "SafePlus onsite assessment methodology"
        ),
        "url": (
            "https://www.worksafe.govt.nz/"
            "managing-health-and-safety/"
            "businesses/safeplus/"
            "resources-and-guidance/"
            "safeplus-onsite-assessment-methodology/"
        ),
        "guidance": [
            (
                "The SafePlus assessment method is intended "
                "to help businesses understand their health "
                "and safety performance and identify ways to "
                "improve."
            ),
            (
                "Recommendations should be linked to observed "
                "performance evidence rather than based only "
                "on the existence of policies or documents."
            ),
            (
                "Improvement advice should consider the "
                "organisation's context, risks, people, and "
                "current level of maturity."
            ),
        ],
    },
    {
        "source_id": "WS-SP-RESOURCES",
        "title": "SafePlus resources and guidance",
        "url": (
            "https://www.worksafe.govt.nz/"
            "managing-health-and-safety/"
            "businesses/safeplus/"
            "resources-and-guidance/"
        ),
        "guidance": [
            (
                "WorkSafe provides resources to help "
                "businesses understand and use SafePlus."
            ),
            (
                "SafePlus analysis should direct users toward "
                "ongoing learning and improvement rather than "
                "presenting the result as a final audit verdict."
            ),
        ],
    },
    {
        "source_id": "WS-SP-ASSESSOR",
        "title": "Find a SafePlus assessor",
        "url": (
            "https://www.worksafe.govt.nz/"
            "managing-health-and-safety/"
            "businesses/safeplus/"
            "find-a-safeplus-assessor/"
        ),
        "guidance": [
            (
                "Recognised SafePlus onsite assessors are "
                "independent, HASANZ-registered health and "
                "safety professionals trained to carry out "
                "SafePlus assessments."
            ),
            (
                "An AI-generated self-assessment analysis "
                "must not claim to replace a qualified "
                "SafePlus onsite assessor."
            ),
            (
                "Where significant uncertainty or serious "
                "risk is identified, organisations should "
                "consider seeking qualified professional "
                "health and safety advice."
            ),
        ],
    },
]


SAFEPLUS_AI_LIMITATIONS: list[str] = [
    (
        "The AI analysis is a decision-support summary based "
        "on supplied survey data and curated WorkSafe SafePlus "
        "guidance."
    ),
    (
        "It is not legal advice and must not determine whether "
        "an organisation is legally compliant or non-compliant."
    ),
    (
        "It does not replace a qualified SafePlus onsite "
        "assessment or professional health and safety advice."
    ),
    (
        "Recommendations must not invent incidents, policies, "
        "legal duties, workplace conditions, or organisation "
        "details that are absent from the supplied evidence."
    ),
]