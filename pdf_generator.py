import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_supplier_pdfs(output_dir: str = "."):
    """Generates 4 synthetic supplier RFP PDFs matching classroom mini-project requirements."""
    os.makedirs(output_dir, exist_ok=True)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1D4ED8'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#374151')
    )

    pdf_files = {}

    # 1. Apex Systems
    fn1 = os.path.join(output_dir, "RFP_Apex_Systems.pdf")
    doc1 = SimpleDocTemplate(fn1, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story1 = [
        Paragraph("RFP Response: Enterprise Cloud Platform Modernization", title_style),
        Paragraph("<b>Submitted By:</b> Apex Systems Inc. | <b>Date:</b> 2026-08-01", body_style),
        Spacer(1, 10),
        
        Paragraph("1. Executive Summary & Requirement Understanding", h2_style),
        Paragraph("Apex Systems offers a premier, high-security enterprise platform solution. We bring extensive engineering rigor designed for zero-downtime architecture and strict regulatory compliance.", body_style),
        Spacer(1, 8),
        
        Paragraph("2. Technical Capability & Architecture", h2_style),
        Paragraph("Our architecture leverages microservices on Kubernetes (EKS), multi-region disaster recovery, automated CI/CD pipelines, and zero-trust IAM integration. Microsecond latency APIs guarantee high throughput and 99.999% availability.", body_style),
        Spacer(1, 8),

        Paragraph("3. Implementation Plan & Milestones", h2_style),
        Paragraph("Delivery duration is 9 months structured in 4 phases: Discovery & Core Architecture (Months 1-2), System Migration (Months 3-5), Security Auditing & UAT (Months 6-7), and Final Rollout (Months 8-9). Dedicated team of 8 senior architects.", body_style),
        Spacer(1, 8),

        Paragraph("4. Commercial Value & Pricing", h2_style),
        Table([
            ["Component", "Details", "Cost (USD)"],
            ["Core Platform Software", "Enterprise License (3 Years)", "$150,000"],
            ["Implementation & Engineering", "9-Month Professional Services", "$80,000"],
            ["Annual Premium Support", "24/7 Managed Services", "$20,000"],
            ["Total Commercial Price", "Fixed Fee Contract", "$250,000"]
        ], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DBEAFE')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]),
        Spacer(1, 8),

        Paragraph("5. Security, Compliance & Risk Controls", h2_style),
        Paragraph("Certified ISO 27001, SOC 2 Type II, and HIPAA compliant. Includes automated penetration testing, AES-256 encryption at rest, TLS 1.3 in transit, and continuous SIEM monitoring.", body_style),
        Spacer(1, 8),

        Paragraph("6. Support Model & Experience", h2_style),
        Paragraph("10 years of enterprise experience with 15+ Fortune 500 reference projects. 24/7 Dedicated Tier-3 Support with 15-minute emergency SLA.", body_style),
    ]
    doc1.build(story1)
    pdf_files["Apex Systems"] = fn1

    # 2. BrightPath Tech
    fn2 = os.path.join(output_dir, "RFP_BrightPath_Tech.pdf")
    doc2 = SimpleDocTemplate(fn2, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story2 = [
        Paragraph("RFP Proposal: Rapid Modernization Solution", title_style),
        Paragraph("<b>Submitted By:</b> BrightPath Tech | <b>Date:</b> 2026-07-15", body_style),
        Spacer(1, 10),
        
        Paragraph("1. Executive Summary & Requirement Understanding", h2_style),
        Paragraph("BrightPath Tech delivers rapid, low-cost modernization using out-of-the-box templates and lean agile teams. Ideal for fast execution.", body_style),
        Spacer(1, 8),
        
        Paragraph("2. Technical Capability & Architecture", h2_style),
        Paragraph("Standard cloud server deployment with REST endpoints. Suitable for medium traffic workloads. Basic horizontal scaling configured.", body_style),
        Spacer(1, 8),

        Paragraph("3. Implementation Plan & Milestones", h2_style),
        Paragraph("Aggressive 3-month timeline: Setup & Deploy (Month 1), Data Transfer (Month 2), Go-Live (Month 3). Small agile team of 3 developers.", body_style),
        Spacer(1, 8),

        Paragraph("4. Commercial Value & Pricing", h2_style),
        Table([
            ["Component", "Details", "Cost (USD)"],
            ["Platform Subscription", "Yearly License", "$70,000"],
            ["Rapid Deployment", "3-Month Setup", "$35,000"],
            ["Standard Support", "Business Hours Support", "$15,000"],
            ["Total Commercial Price", "Low-Cost Guarantee", "$120,000"]
        ], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DCFCE7')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]),
        Spacer(1, 8),

        Paragraph("5. Security, Compliance & Risk Controls", h2_style),
        Paragraph("Basic SSL encryption enabled. Standard password authentication. Official SOC2 certification is currently pending.", body_style),
        Spacer(1, 8),

        Paragraph("6. Support Model & Experience", h2_style),
        Paragraph("Startup founded 2 years ago. Standard email support during business hours (8am - 5pm). 2 startup client references.", body_style),
    ]
    doc2.build(story2)
    pdf_files["BrightPath Tech"] = fn2

    # 3. NexaWorks
    fn3 = os.path.join(output_dir, "RFP_NexaWorks.pdf")
    doc3 = SimpleDocTemplate(fn3, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story3 = [
        Paragraph("RFP Proposal: NextGen Enterprise Application Suite", title_style),
        Paragraph("<b>Submitted By:</b> NexaWorks | <b>Date:</b> 2026-07-28", body_style),
        Spacer(1, 10),
        
        Paragraph("1. Executive Summary & Requirement Understanding", h2_style),
        Paragraph("NexaWorks proposes a highly balanced enterprise solution emphasizing a flawless implementation roadmap and industry-best support operations.", body_style),
        Spacer(1, 8),
        
        Paragraph("2. Technical Capability & Architecture", h2_style),
        Paragraph("Cloud-native microservices architecture with robust OAuth2/OIDC integration, modular API gateway, automated disaster recovery, and 99.95% SLA guarantees.", body_style),
        Spacer(1, 8),

        Paragraph("3. Implementation Plan & Milestones", h2_style),
        Paragraph("Structured 6-month phased delivery: Requirements & Prototyping (Months 1-2), Core Build & Integration (Months 3-4), Security Testing & Training (Month 5), Seamless Production Cutover (Month 6). Detailed risk mitigation matrix included.", body_style),
        Spacer(1, 8),

        Paragraph("4. Commercial Value & Pricing", h2_style),
        Table([
            ["Component", "Details", "Cost (USD)"],
            ["Enterprise License", "3-Year Multi-Tenant Access", "$100,000"],
            ["Turnkey Implementation", "6-Month Delivery", "$60,000"],
            ["24/7 Dedicated Support", "Tier-3 Escalation SLA", "$20,000"],
            ["Total Commercial Price", "Balanced Enterprise Package", "$180,000"]
        ], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FEF08A')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]),
        Spacer(1, 8),

        Paragraph("5. Security, Compliance & Risk Controls", h2_style),
        Paragraph("Full SOC 2 Type II and ISO 27001 certified. Role-Based Access Control (RBAC), end-to-end data encryption, and quarterly third-party vulnerability audits.", body_style),
        Spacer(1, 8),

        Paragraph("6. Support Model & Experience", h2_style),
        Paragraph("7 years in business with 25+ successful implementations. Dedicated Account Manager, 24/7 Tier-3 technical support with guaranteed 30-minute SLA response time.", body_style),
    ]
    doc3.build(story3)
    pdf_files["NexaWorks"] = fn3

    # 4. Orbit Digital
    fn4 = os.path.join(output_dir, "RFP_Orbit_Digital.pdf")
    doc4 = SimpleDocTemplate(fn4, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story4 = [
        Paragraph("RFP Response: Digital Transformation & Cloud Integration", title_style),
        Paragraph("<b>Submitted By:</b> Orbit Digital | <b>Date:</b> 2026-08-05", body_style),
        Spacer(1, 10),
        
        Paragraph("1. Executive Summary & Requirement Understanding", h2_style),
        Paragraph("Orbit Digital brings over 12 years of industry leadership and a vast portfolio of successful legacy migrations for enterprise clients.", body_style),
        Spacer(1, 8),
        
        Paragraph("2. Technical Capability & Architecture", h2_style),
        Paragraph("Custom legacy framework wrapper with REST integration options. Integration specifications are flexible and handled during customization phase.", body_style),
        Spacer(1, 8),

        Paragraph("3. Implementation Plan & Milestones", h2_style),
        Paragraph("Estimated 7 months implementation timeline. Specific milestone breakdown and team allocation will be determined after project kickoff.", body_style),
        Spacer(1, 8),

        Paragraph("4. Commercial Value & Pricing", h2_style),
        Table([
            ["Component", "Details", "Cost (USD)"],
            ["Software License", "Perpetual License", "$130,000"],
            ["Integration & Customization", "7-Month Services", "$60,000"],
            ["Annual Maintenance", "Standard Support", "$20,000"],
            ["Total Commercial Price", "Competitive Mid-Tier", "$210,000"]
        ], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3E8FF')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]),
        Spacer(1, 8),

        Paragraph("5. Security, Compliance & Risk Controls", h2_style),
        Paragraph("ISO 27001 certified. Standard firewall protection, data backup procedures, and role-based permissions.", body_style),
        Spacer(1, 8),

        Paragraph("6. Support Model & Experience", h2_style),
        Paragraph("12 years market leadership with over 40+ client success stories. Provides client references from top government and financial institutions.", body_style),
    ]
    doc4.build(story4)
    pdf_files["Orbit Digital"] = fn4

    return pdf_files

if __name__ == "__main__":
    generated = generate_supplier_pdfs(".")
    print("Generated PDFs:", generated)
