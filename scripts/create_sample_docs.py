"""
Example script to create sample company information document
This creates a simple PDF for testing the knowledge base
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os


def create_sample_company_handbook():
    """Create a sample company handbook PDF"""
    
    # Ensure data directory exists
    os.makedirs("data/raw", exist_ok=True)
    
    filepath = "data/raw/sample_company_handbook.pdf"
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("Company Handbook - WareHouse Pro Inc.", styles['Title']))
    story.append(Spacer(1, 0.3 * inch))
    
    # About Us
    story.append(Paragraph("About Our Company", styles['Heading1']))
    story.append(Paragraph(
        "WareHouse Pro Inc. is a leading logistics and warehouse management company "
        "with over 20 years of experience. We pride ourselves on our commitment to "
        "excellence, safety, and employee development.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Job Opportunities
    story.append(Paragraph("Available Positions", styles['Heading1']))
    story.append(Paragraph("Warehouse Associate", styles['Heading2']))
    story.append(Paragraph(
        "We are seeking motivated individuals to join our warehouse team. "
        "Responsibilities include order picking, packing, inventory management, "
        "and operating warehouse equipment including forklifts.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Requirements
    story.append(Paragraph("Basic Requirements", styles['Heading2']))
    requirements = [
        "Must be at least 18 years old",
        "Authorized to work in the United States",
        "Ability to lift up to 50 pounds",
        "Available for day, evening, or night shifts",
        "Reliable transportation to and from work",
        "High school diploma or equivalent preferred",
    ]
    for req in requirements:
        story.append(Paragraph(f"• {req}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Shift Information
    story.append(Paragraph("Shift Schedule", styles['Heading2']))
    story.append(Paragraph(
        "We offer flexible shift options to accommodate different schedules:",
        styles['Normal']
    ))
    shifts = [
        "Day Shift: 7:00 AM - 3:30 PM, Monday to Friday",
        "Evening Shift: 3:00 PM - 11:30 PM, Monday to Friday",
        "Night Shift: 11:00 PM - 7:30 AM, Sunday to Thursday",
        "Weekend Shift: Saturday and Sunday, various times with premium pay",
    ]
    for shift in shifts:
        story.append(Paragraph(f"• {shift}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Benefits
    story.append(Paragraph("Benefits Package", styles['Heading1']))
    story.append(Paragraph(
        "We offer a comprehensive benefits package to all full-time employees:",
        styles['Normal']
    ))
    benefits = [
        "Competitive hourly wages starting at $18.50/hour",
        "Health insurance (medical, dental, vision)",
        "401(k) retirement plan with company match",
        "Paid time off (PTO) and holidays",
        "Employee discounts",
        "Career advancement opportunities",
        "On-the-job training and certification programs",
        "Safety equipment provided",
    ]
    for benefit in benefits:
        story.append(Paragraph(f"• {benefit}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Skills and Qualifications
    story.append(Paragraph("Desired Skills", styles['Heading2']))
    skills = [
        "Forklift operation (certification provided if needed)",
        "Inventory management systems experience",
        "Attention to detail and accuracy",
        "Ability to work in a team environment",
        "Good communication skills",
        "Basic computer skills",
        "Previous warehouse experience (preferred but not required)",
    ]
    for skill in skills:
        story.append(Paragraph(f"• {skill}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Application Process
    story.append(Paragraph("Application Process", styles['Heading1']))
    story.append(Paragraph(
        "Our application process is simple and can be completed through our "
        "AI assistant, Cleo. The process includes:",
        styles['Normal']
    ))
    process = [
        "Initial conversation to understand your interest",
        "Basic qualification questions",
        "Application information collection",
        "Identity verification",
        "Background check (if applicable)",
        "Final review and decision (typically within 3-5 business days)",
    ]
    for step in process:
        story.append(Paragraph(f"{process.index(step) + 1}. {step}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Company Culture
    story.append(Paragraph("Our Culture", styles['Heading1']))
    story.append(Paragraph(
        "At WareHouse Pro, we believe in creating a positive work environment "
        "where every team member feels valued and respected. We promote from within "
        "and offer numerous opportunities for career growth. Safety is our top priority, "
        "and we maintain a clean, organized, and modern facility.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Contact Information
    story.append(Paragraph("Contact Us", styles['Heading1']))
    story.append(Paragraph(
        "For questions about employment opportunities, please contact our "
        "Human Resources department:",
        styles['Normal']
    ))
    story.append(Paragraph("Phone: (555) 123-4567", styles['Normal']))
    story.append(Paragraph("Email: careers@warehousepro.com", styles['Normal']))
    story.append(Paragraph("Address: 123 Industrial Parkway, Cityville, ST 12345", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    print(f"Sample company handbook created: {filepath}")
    return filepath


def create_sample_job_description():
    """Create a sample job description PDF"""
    
    os.makedirs("data/raw", exist_ok=True)
    filepath = "data/raw/sample_job_description.pdf"
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("Job Description - Warehouse Associate", styles['Title']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Position Overview
    story.append(Paragraph("Position Overview", styles['Heading1']))
    story.append(Paragraph(
        "The Warehouse Associate plays a critical role in our supply chain operations. "
        "This position involves receiving, storing, picking, packing, and shipping products "
        "while maintaining accurate inventory records and ensuring workplace safety.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Key Responsibilities
    story.append(Paragraph("Key Responsibilities", styles['Heading1']))
    responsibilities = [
        "Receive and process warehouse stock products",
        "Pick and fill orders from stock",
        "Pack and ship orders accurately",
        "Organize and maintain inventory",
        "Operate warehouse equipment (pallet jacks, forklifts) safely",
        "Perform inventory cycle counts",
        "Maintain clean and safe work environment",
        "Follow quality and safety standards",
        "Collaborate with team members",
        "Report any equipment malfunctions",
    ]
    for resp in responsibilities:
        story.append(Paragraph(f"• {resp}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Qualifications
    story.append(Paragraph("Required Qualifications", styles['Heading1']))
    qualifications = [
        "High school diploma or GED equivalent",
        "18 years of age or older",
        "Ability to lift 50 pounds repeatedly",
        "Stand and walk for extended periods",
        "Work in varying temperatures",
        "Basic math and reading skills",
        "Attention to detail",
    ]
    for qual in qualifications:
        story.append(Paragraph(f"• {qual}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Preferred Qualifications
    story.append(Paragraph("Preferred Qualifications", styles['Heading2']))
    preferred = [
        "1+ years warehouse experience",
        "Forklift certification",
        "Experience with warehouse management systems (WMS)",
        "Order picking experience",
        "Shipping and receiving knowledge",
    ]
    for pref in preferred:
        story.append(Paragraph(f"• {pref}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Work Environment
    story.append(Paragraph("Work Environment", styles['Heading1']))
    story.append(Paragraph(
        "This position operates in a warehouse environment. The employee may be exposed "
        "to varying temperatures, moving mechanical parts, and heights. The noise level "
        "is usually moderate. Safety equipment including steel-toed boots, safety vest, "
        "and gloves are required and provided by the company.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Physical Requirements
    story.append(Paragraph("Physical Requirements", styles['Heading1']))
    physical = [
        "Stand and walk for up to 10 hours per day",
        "Lift and carry up to 50 pounds frequently",
        "Bend, stoop, squat, and reach regularly",
        "Climb stairs and ladders occasionally",
        "Use hands and fingers to handle objects",
        "See clearly at close and far distances",
    ]
    for phys in physical:
        story.append(Paragraph(f"• {phys}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Compensation
    story.append(Paragraph("Compensation and Benefits", styles['Heading1']))
    story.append(Paragraph(
        "Starting wage: $18.50 - $22.00 per hour (based on experience)",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Shift differentials available for evening and night shifts",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Full benefits package available after 90 days",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    print(f"Sample job description created: {filepath}")
    return filepath


def main():
    """Create sample documents"""
    print("Creating sample documents for knowledge base...\n")
    
    handbook_path = create_sample_company_handbook()
    job_desc_path = create_sample_job_description()
    
    print("\n" + "="*60)
    print("Sample documents created successfully!")
    print("="*60)
    print(f"\n1. {handbook_path}")
    print(f"2. {job_desc_path}")
    print("\nYou can now ingest these documents into the knowledge base:")
    print("  python setup_knowledge_base.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
