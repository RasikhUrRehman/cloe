from chatbot.utils.xano_client import XanoClient

xc = XanoClient()
try:
    result = xc.create_candidate(
        name="sdfsdfs",
        email="john.dodfsdfse@example.com",
        phone="123456783443434901",
        score=87,
        file_path="reports\\eligibility_report_a2beca3e-65f8-4257-a7d2-549367ec0569.pdf",
        job_id="2b951289-6c7e-403c-baf8-9c0d5e803df5",
        company_id="226e9e5b-6773-46e6-9b2d-caa5a14429ff",
        status="Short Listed",
        session_id=29,
    )
    print(result)
except Exception as e:
    print(f"Error creating candidate: {e}")