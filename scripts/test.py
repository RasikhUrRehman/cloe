from chatbot.utils.xano_client import XanoClient

xc = XanoClient()
try:
    result = xc.create_candidate(
        name="amadfd",
        email="john.dofffghkujkhhkfgdfgd@example.com",
        phone="+92533699",
        job_id="2b951289-6c7e-403c-baf8-9c0d5e803df5",
        company_id="226e9e5b-6773-46e6-9b2d-caa5a14429ff",
        status="Short Listed",
        session_id=29,
    )
    print(result)
except Exception as e:
    print(f"Error creating candidate: {e}")