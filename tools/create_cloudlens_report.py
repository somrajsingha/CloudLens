from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether, HRFlowable, Flowable, ListFlowable,
    ListItem,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "CloudLens_AWS_Project_Report.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = A4
NAVY = colors.HexColor("#14213D")
BLUE = colors.HexColor("#2563EB")
SKY = colors.HexColor("#EAF2FF")
TEAL = colors.HexColor("#0F766E")
GREEN = colors.HexColor("#DCFCE7")
ORANGE = colors.HexColor("#F59E0B")
AMBER = colors.HexColor("#FFF4D6")
RED = colors.HexColor("#B42318")
INK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#5B6472")
LINE = colors.HexColor("#D5DBE5")
PAPER = colors.HexColor("#F7F9FC")

font_regular = "Helvetica"
font_bold = "Helvetica-Bold"
for candidate in [Path("C:/Windows/Fonts/aptos.ttf"), Path("C:/Windows/Fonts/calibri.ttf")]:
    if candidate.exists():
        pdfmetrics.registerFont(TTFont("BodyFont", str(candidate)))
        font_regular = "BodyFont"
        bold_candidate = candidate.with_name("aptosbd.ttf" if "aptos" in candidate.name else "calibrib.ttf")
        if bold_candidate.exists():
            pdfmetrics.registerFont(TTFont("BodyBold", str(bold_candidate)))
            font_bold = "BodyBold"
        break

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="ReportTitle", fontName=font_bold, fontSize=28, leading=31,
    textColor=NAVY, alignment=TA_LEFT, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="Subtitle", fontName=font_regular, fontSize=12.5, leading=18,
    textColor=MUTED, spaceAfter=18,
))
styles.add(ParagraphStyle(
    name="H1x", fontName=font_bold, fontSize=19, leading=23,
    textColor=NAVY, spaceBefore=4, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="H2x", fontName=font_bold, fontSize=12.5, leading=16,
    textColor=BLUE, spaceBefore=8, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="Bodyx", fontName=font_regular, fontSize=9.4, leading=13.6,
    textColor=INK, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Smallx", fontName=font_regular, fontSize=7.6, leading=10.5,
    textColor=MUTED,
))
styles.add(ParagraphStyle(
    name="Callout", fontName=font_regular, fontSize=9.2, leading=13.5,
    textColor=NAVY, backColor=SKY, borderColor=colors.HexColor("#B9D1FF"),
    borderWidth=0.7, borderPadding=9, spaceBefore=5, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CodexCode", fontName="Courier", fontSize=7.4, leading=10.2,
    textColor=colors.HexColor("#E5E7EB"), backColor=colors.HexColor("#111827"),
    borderPadding=8, leftIndent=0, rightIndent=0, spaceBefore=4, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="TableHead", fontName=font_bold, fontSize=7.6, leading=9.5,
    textColor=colors.white,
))
styles.add(ParagraphStyle(
    name="TableBody", fontName=font_regular, fontSize=7.4, leading=9.8,
    textColor=INK,
))
styles.add(ParagraphStyle(
    name="Quote", fontName=font_regular, fontSize=10.4, leading=15,
    textColor=NAVY, leftIndent=12, borderColor=BLUE, borderWidth=2,
    borderPadding=7, spaceBefore=5, spaceAfter=8,
))


def p(text, style="Bodyx"):
    return Paragraph(text, styles[style])


def bullets(items, level=0):
    return ListFlowable(
        [ListItem(p(item), leftIndent=8) for item in items],
        bulletType="bullet", start="circle", leftIndent=16 + level * 10,
        bulletFontName=font_regular, bulletFontSize=6, bulletColor=BLUE,
        spaceAfter=6,
    )


def table(rows, widths, header=True):
    converted = []
    for r_index, row in enumerate(rows):
        converted.append([
            p(str(cell), "TableHead" if header and r_index == 0 else "TableBody")
            for cell in row
        ])
    t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER]),
        ]
    else:
        commands.append(("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, PAPER]))
    t.setStyle(TableStyle(commands))
    return t


class ArchitectureFlow(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 168 * mm
        self.height = 78 * mm

    def draw_box(self, c, x, y, w, h, title, detail, fill):
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.roundRect(x, y, w, h, 5, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont(font_bold, 8.3)
        c.drawCentredString(x + w / 2, y + h - 12, title)
        c.setFillColor(MUTED)
        c.setFont(font_regular, 6.7)
        for i, line in enumerate(detail.split("|")):
            c.drawCentredString(x + w / 2, y + h - 23 - i * 9, line)

    def arrow(self, c, x1, y1, x2, y2, label=""):
        c.setStrokeColor(BLUE)
        c.setFillColor(BLUE)
        c.setLineWidth(1.2)
        c.line(x1, y1, x2, y2)
        angle = 4
        c.line(x2, y2, x2 - angle, y2 + angle / 2)
        c.line(x2, y2, x2 - angle, y2 - angle / 2)
        if label:
            c.setFont(font_regular, 5.8)
            c.drawCentredString((x1 + x2) / 2, y1 + 4, label)

    def draw(self):
        c = self.canv
        w, h, gap = 31 * mm, 23 * mm, 4 * mm
        top_y = 49 * mm
        xs = [0, w + gap, 2 * (w + gap), 3 * (w + gap), 4 * (w + gap)]
        self.draw_box(c, xs[0], top_y, w, h, "Browser", "React + Vite|Amplify Hosting", SKY)
        self.draw_box(c, xs[1], top_y, w, h, "Cognito", "OAuth 2.0 PKCE|ID token", GREEN)
        self.draw_box(c, xs[2], top_y, w, h, "API Gateway", "Cognito authorizer|REST endpoints", AMBER)
        self.draw_box(c, xs[3], top_y, w, h, "API Lambda", "Signed URLs|File operations", SKY)
        self.draw_box(c, xs[4], top_y, w, h, "DynamoDB", "Owner + fileId|Status metadata", GREEN)
        for i, label in enumerate(["authenticate", "Bearer token", "invoke", "read/write"]):
            self.arrow(c, xs[i] + w, top_y + h / 2, xs[i + 1], top_y + h / 2, label)
        low_y = 5 * mm
        self.draw_box(c, 24 * mm, low_y, 36 * mm, h, "Raw S3", "Private uploads|S3 event", AMBER)
        self.draw_box(c, 68 * mm, low_y, 36 * mm, h, "Processor Lambda", "Image WebP|PDF text / OCR", SKY)
        self.draw_box(c, 112 * mm, low_y, 36 * mm, h, "Processed S3", "Private outputs|Signed downloads", GREEN)
        self.arrow(c, 60 * mm, low_y + h / 2, 68 * mm, low_y + h / 2, "event")
        self.arrow(c, 104 * mm, low_y + h / 2, 112 * mm, low_y + h / 2, "write")
        c.setStrokeColor(TEAL)
        c.setDash(2, 2)
        c.line(xs[3] + w / 2, top_y, 42 * mm, low_y + h)
        c.line(86 * mm, low_y + h, xs[4] + w / 2, top_y)
        c.setDash()


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 14 * mm, PAGE_W - 20 * mm, 14 * mm)
    canvas.setFont(font_regular, 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 9 * mm, "CloudLens - AWS Serverless Project Report")
    canvas.drawRightString(PAGE_W - 20 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
    topMargin=18 * mm, bottomMargin=19 * mm, title="CloudLens AWS Project Report",
    author="Somraj Singha with Codex",
)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=header_footer))

story = []

# Cover
story += [Spacer(1, 24 * mm), p("CLOUDLENS", "ReportTitle")]
story += [p("A serverless image and document processing platform on AWS", "Subtitle")]
story += [HRFlowable(width="100%", thickness=2.2, color=BLUE, spaceAfter=16)]
story += [p("Complete implementation, deployment, debugging, security, and verification report", "H2x")]
cover = [
    ["Prepared for", "Academic project explanation and viva"],
    ["Student", "Somraj Singha"],
    ["AWS account", "465247576490 (AWS Free Plan)"],
    ["Region", "ap-southeast-2 (Sydney)"],
    ["Live application", "https://main.d328vlvqzb3w2y.amplifyapp.com/"],
    ["CloudFormation stack", "cloudlens"],
    ["Report date", "25 November 2026"],
]
story += [table(cover, [42 * mm, 115 * mm], header=False), Spacer(1, 13 * mm)]
story += [p("Project in one sentence", "H2x")]
story += [p("CloudLens securely accepts JPG, PNG, and PDF uploads, processes them asynchronously in AWS Lambda, stores private inputs and outputs in Amazon S3, tracks status in DynamoDB, authenticates users with Cognito, and presents results through a React application hosted by AWS Amplify.", "Quote")]
story += [Spacer(1, 18 * mm), p("Prepared from the actual repository, deployed AWS configuration, observed deployment outputs, and end-to-end production tests. No passwords, access keys, or secret tokens are included.", "Smallx")]
story.append(PageBreak())

# Executive summary
story += [p("1. Executive summary", "H1x")]
story += [p("The goal was to turn an existing React interface into a complete cloud application while keeping the deployment inside the user's AWS Free Plan. Codex inspected the repository, completed the backend and infrastructure, validated the design locally, deployed the backend with AWS SAM and CloudFormation, published the frontend through Amplify Hosting, diagnosed a production S3 upload failure, applied a regional signing fix, and verified both image and PDF processing in the live system.")]
story += [p("Final capabilities", "H2x"), bullets([
    "Email-based sign-up and sign-in through Amazon Cognito using OAuth 2.0 Authorization Code with PKCE.",
    "Private direct-to-S3 uploads using 15-minute presigned PUT URLs; supported files are JPG, PNG, and PDF up to 10 MB.",
    "Automatic image resize, EXIF correction, CloudLens watermark, WebP conversion, and compression.",
    "PDF text extraction with PDFium; scanned pages fall back to English Tesseract OCR inside a Lambda container.",
    "Per-user file history, processing state, signed downloads, and deletion.",
    "Admin-only operational dashboard with totals, failure rate, processing latency, and storage savings.",
    "SNS completion and failure events, with email subscription available as an optional feature.",
])]
story += [p("Verified production result", "H2x")]
verified = [
    ["Test", "Observed result"],
    ["Sample photo", "Completed; 0.03 MB original became a 0.01 MB WebP output."],
    ["Sample PDF", "Completed; extracted invoice number, customer, service, amount, and paid status."],
    ["Authentication", "Cognito managed login opened and returned a usable application session."],
    ["Admin access", "Existing user was added to the Cognito admins group and membership was verified."],
    ["Stack", "CloudFormation reached UPDATE_COMPLETE after the final S3 signing fix."],
]
story += [table(verified, [42 * mm, 115 * mm])]
story.append(PageBreak())

# Architecture
story += [p("2. System architecture", "H1x")]
story += [p("CloudLens follows an event-driven serverless architecture. The browser never receives AWS credentials. It authenticates with Cognito, calls a protected API, receives a short-lived signed S3 URL, and uploads directly to private storage. The upload event then starts background processing.")]
story += [Spacer(1, 3 * mm), ArchitectureFlow(), Spacer(1, 4 * mm)]
story += [p("Why this architecture was chosen", "H2x")]
story += [table([
    ["Decision", "Reason"],
    ["Direct browser-to-S3 upload", "Avoids sending binary files through API Gateway and the API Lambda; reduces latency and Lambda cost."],
    ["S3 event-driven processing", "Separates upload responsiveness from potentially slow image conversion or OCR."],
    ["DynamoDB status record", "Provides a durable state machine: pending, processing, completed, or failed."],
    ["Container Lambda for OCR", "Packages Tesseract and native PDF/image dependencies that do not fit a simple source-only Lambda."],
    ["Managed Cognito login", "Provides secure registration, email verification, hosted login, token issuance, and group claims."],
    ["SAM and CloudFormation", "Keeps infrastructure reproducible and reviewable as code."],
], [43 * mm, 114 * mm])]
story.append(PageBreak())

# AWS inventory
story += [p("3. AWS resources and their responsibilities", "H1x")]
resources = [
    ["Service / resource", "Purpose", "Security / configuration"],
    ["Amplify Hosting", "Hosts the production React/Vite static site on branch main.", "HTTPS URL; manual zip deployment with index.html at zip root."],
    ["Cognito User Pool", "Registers users, verifies email, signs users in, and issues ID/refresh tokens.", "OAuth code flow with PKCE; exact callback URL; 12-character strong password policy."],
    ["Cognito admins group", "Marks users who may view system-wide metrics.", "Group is carried in the cognito:groups token claim; API checks the claim server-side."],
    ["API Gateway REST API", "Exposes upload, file history, download, delete, and admin endpoints.", "Cognito authorizer protects every route; CORS restricted to the Amplify origin."],
    ["API Lambda", "Validates file requests, writes metadata, creates signed URLs, lists files, and deletes records/objects.", "Python 3.13; owner derived from the authenticated sub claim."],
    ["Processor Lambda", "Transforms images and extracts/OCRs PDF text.", "Python 3.12 container; 2 GB memory; 15-minute timeout; least-privilege access to project data."],
    ["Admin Lambda", "Calculates dashboard metrics from retained file records.", "Python 3.13; read-only DynamoDB policy; explicit admins claim check."],
    ["Raw S3 bucket", "Stores original uploads and emits object-created events.", "Private, encrypted with AES-256, all public access blocked, CORS limited to the site."],
    ["Processed S3 bucket", "Stores WebP images and extracted text outputs.", "Private, encrypted, public access blocked; downloads use short-lived signed URLs."],
    ["DynamoDB table", "Stores one record per user/file with state and processing metadata.", "On-demand billing; partition key owner and sort key fileId."],
    ["SNS topic", "Publishes completion and failure events.", "Only the processor Lambda can publish; email subscription is optional."],
    ["ECR repository", "Stores the processor Lambda container image.", "Created and managed through SAM deployment."],
    ["CloudFormation", "Creates, updates, and tracks the entire backend stack.", "Final deployment observed as UPDATE_COMPLETE."],
]
story += [table(resources, [32 * mm, 55 * mm, 70 * mm])]
story.append(PageBreak())

# Flow
story += [p("4. End-to-end data flow", "H1x")]
steps = [
    ["Step", "What happens", "AWS component"],
    ["1", "The user signs in. The browser creates a PKCE verifier, challenge, and state value.", "Cognito + React"],
    ["2", "Cognito returns an authorization code. The browser exchanges it for tokens and stores them in sessionStorage.", "Cognito"],
    ["3", "The user selects a file. The frontend validates type, non-empty size, and the 10 MB limit.", "React"],
    ["4", "POST /upload-url sends name, MIME type, and size with the Cognito ID token.", "API Gateway"],
    ["5", "The API validates the request, creates a UUID and pending DynamoDB record, and returns a 15-minute signed PUT URL.", "API Lambda + DynamoDB"],
    ["6", "The browser uploads the file directly to the private raw bucket with the signed URL.", "Amazon S3"],
    ["7", "S3 ObjectCreated invokes the processor. A conditional DynamoDB update claims the pending file exactly once.", "S3 + Processor Lambda"],
    ["8", "The processor verifies actual content length and MIME type against the approved record.", "Processor Lambda"],
    ["9A", "Image path: validate image, apply EXIF orientation, resize to 1920x1920, watermark, encode WebP at quality 78.", "Pillow"],
    ["9B", "PDF path: extract embedded text with PDFium; render and run Tesseract OCR only for pages with no text layer.", "PDFium + Tesseract"],
    ["10", "Output is written to processed S3; DynamoDB becomes completed or failed; SNS publishes the outcome.", "S3 + DynamoDB + SNS"],
    ["11", "The browser polls GET /files/{fileId} every two seconds and displays the result when terminal state is reached.", "API + React"],
    ["12", "Download requests return a five-minute signed GET URL for the private processed object.", "API Lambda + S3"],
]
story += [table(steps, [12 * mm, 105 * mm, 40 * mm])]
story += [p("State model", "H2x")]
story += [p("pending -> processing -> completed, or pending/processing -> failed", "CodexCode")]
story.append(PageBreak())

# Security
story += [p("5. Authentication, authorization, and security", "H1x")]
story += [p("CloudLens applies security at several independent layers. Authentication proves the user identity; API authorization scopes every file operation to that user's Cognito subject; S3 remains private; and admin authorization is checked in both the token and backend.")]
security = [
    ["Control", "Implementation"],
    ["OAuth protection", "Authorization Code with PKCE prevents a stolen authorization code from being exchanged without the browser's verifier."],
    ["CSRF protection", "A random state value is stored before redirect and compared on return."],
    ["Token handling", "ID and refresh tokens live in sessionStorage, which clears when the browser session ends; no AWS key is stored in the frontend."],
    ["User isolation", "The owner key always comes from requestContext.authorizer.claims.sub. The API never accepts an owner value from the client."],
    ["Private storage", "Both buckets block public ACLs and public bucket policies. Objects are accessed only by Lambda permissions or temporary signed URLs."],
    ["Encryption", "S3 server-side encryption uses AES-256."],
    ["Upload verification", "The processor compares actual S3 size and MIME type against the server-approved DynamoDB record before processing."],
    ["Idempotency", "A conditional DynamoDB update changes pending to processing. Duplicate events fail the condition and are ignored."],
    ["Admin isolation", "The Admin Lambda rejects requests unless cognito:groups contains admins. Membership was added in Cognito, not trusted from the UI."],
    ["Least privilege", "Each Lambda receives only the table, bucket, and SNS actions its role requires."],
    ["CORS", "API and raw S3 CORS allow only the production Amplify origin."],
    ["Input constraints", "File names, types, sizes, PDF page count, render size, and OCR execution time are bounded."],
]
story += [table(security, [42 * mm, 115 * mm])]
story += [p("Admin sign-in", "H2x")]
story += [p("There is no separate admin password. The same Cognito login is used. When a user belongs to the admins group, a newly issued ID token includes the group claim. Therefore the user must sign out and sign in again after membership changes.", "Callout")]
story.append(PageBreak())

# Algorithms
story += [p("6. Processing implementation", "H1x")]
story += [p("Image pipeline", "H2x")]
story += [bullets([
    "Read the private raw object into memory and validate it with Pillow.",
    "Apply EXIF transpose so phone photographs are not rotated incorrectly.",
    "Convert to RGB and preserve aspect ratio while fitting within 1920 x 1920 pixels.",
    "Place a visible CloudLens watermark at the lower-right corner with a contrasting outline.",
    "Encode as WebP using quality 78 and method 6, then store image.webp in the processed bucket.",
    "Write processed size and processing duration to DynamoDB and publish an SNS completion event.",
])]
story += [p("PDF and OCR pipeline", "H2x")]
story += [bullets([
    "Open the PDF using PDFium and reject documents outside the 1-25 page range.",
    "For every page, first read the text layer. This is faster and more accurate than OCR when text already exists.",
    "If a page has no text, enforce a rendered-pixel safety limit, render it at 2x scale, and convert it to PNG.",
    "Run Tesseract with English language data, a 30-second per-page timeout, and captured input/output.",
    "Join page text, reject an entirely unreadable PDF, and save extracted.txt as UTF-8.",
    "Store the first 1,000 characters in DynamoDB for the UI preview while retaining the complete text object in S3.",
])]
story += [p("Important limits", "H2x")]
story += [table([
    ["Limit", "Value", "Reason"],
    ["Upload size", "10 MB", "Bounds browser, S3, memory, and processing cost."],
    ["PDF pages", "25", "Bounds execution time and OCR work."],
    ["Image dimensions", "1920 x 1920", "Creates practical web-ready output."],
    ["Rendered page pixels", "20 million", "Prevents excessive memory use."],
    ["OCR timeout", "30 seconds per page", "Prevents a stuck subprocess from consuming the full Lambda timeout."],
    ["Signed upload URL", "15 minutes", "Short-lived permission for one object."],
    ["Signed download URL", "5 minutes", "Short-lived read access to one output."],
], [39 * mm, 30 * mm, 88 * mm])]
story.append(PageBreak())

# Deployment
story += [p("7. What Codex did to deploy the project", "H1x")]
timeline = [
    ["Phase", "Work completed"],
    ["Account selection", "Separated the personal AWS Free Plan account from a Vocareum lab session; verified account 465247576490, Sydney region, plan status, credits, and remaining plan period."],
    ["Repository audit", "Inspected React code, Python backend, tests, Dockerfile, environment variables, and SAM template. Identified missing deployment wiring and an infrastructure dependency cycle."],
    ["Infrastructure repair", "Removed an unused DynamoDB index, assigned a deterministic raw bucket name, and replaced circular Ref dependencies with stack/account/region substitutions."],
    ["Runtime compatibility", "Changed source Lambda runtimes to Python 3.13 because CloudShell provided Python 3.13 while the unavailable SAM Python 3.12 build image blocked source builds."],
    ["Local validation", "Built the frontend, compiled Python, linted the SAM template, and ran seven unit tests covering API validation, ownership, image processing, text PDF extraction, and OCR fallback."],
    ["Amplify setup", "Created Amplify app d328vlvqzb3w2y and main branch, establishing the final production origin and Cognito callback URL."],
    ["Backend build", "Used AWS CloudShell Docker to build the OCR container and SAM to build the Python functions."],
    ["Backend deployment", "Deployed stack cloudlens with SAM, CloudFormation, CAPABILITY_IAM, resolved S3 artifacts, and resolved image repositories."],
    ["Frontend configuration", "Read stack outputs for API URL, Cognito domain, and client ID; created the production environment; built the Vite bundle; zipped dist contents."],
    ["Frontend publication", "Used Amplify create-deployment, uploaded the zip to the provided URL, started job 1, and observed SUCCEED."],
    ["Production diagnosis", "Reproduced the Failed to fetch issue and proved S3 returned HTTP 307 because signed PUT URLs used the global endpoint."],
    ["Production fix", "Configured a regional S3 endpoint with Signature Version 4, proved HTTP 200 with the expected CORS header, deployed the updated Lambdas, and observed UPDATE_COMPLETE."],
    ["End-to-end verification", "Signed in to the live app and completed both sample photo and sample PDF processing; verified results in My files."],
    ["Admin enablement", "Located the confirmed Cognito user, added it to the existing admins group after confirmation, and verified group membership."],
]
story += [table(timeline, [35 * mm, 122 * mm])]
story.append(PageBreak())

# Debugging
story += [p("8. Main problems encountered and how they were solved", "H1x")]
problems = [
    ["Problem", "Diagnosis", "Solution / lesson"],
    ["Wrong AWS context", "The open browser initially pointed to a Vocareum course lab and local CLI credentials belonged to a different expired account.", "Selected the user's personal AWS Free Plan account and performed authenticated operations in its CloudShell."],
    ["Circular CloudFormation dependency", "The named S3 notification depended on the processor permission and function, while the function environment/policy referenced the bucket resource.", "Made the raw bucket name deterministic and used Sub expressions in the processor configuration to break the Ref cycle."],
    ["Python 3.12 source build unavailable", "CloudShell had Python 3.13, and SAM could not fetch the expected Python 3.12 build container.", "Moved API/Admin Lambdas to supported Python 3.13 while keeping the processor in its own Python 3.12 Docker image."],
    ["Slow container build", "OCR dependencies require a base image, native packages, Pillow, PDFium, Tesseract, and the Lambda runtime client.", "Built it once in CloudShell Docker and let SAM/ECR manage the image artifact."],
    ["Browser reported Failed to fetch", "API records were created but files stayed pending. A controlled curl PUT showed S3 returned TemporaryRedirect 307 to a Sydney-specific endpoint.", "Forced https://s3.ap-southeast-2.amazonaws.com and SigV4 in the shared boto3 S3 client. A real PUT returned 200 and the production app then completed processing."],
    ["Admin tab denied access", "A normal confirmed user had zero Cognito group memberships.", "Added the existing user to admins and required a fresh sign-in so the new ID token contained cognito:groups."],
]
story += [table(problems, [36 * mm, 54 * mm, 67 * mm])]
story += [p("The most important debugging lesson", "H2x")]
story += [p("A successful API response does not prove that a direct browser upload succeeded. CloudLens creates the pending record before the S3 PUT. The decisive evidence came from tracing the system boundary after the API: browser -> presigned URL -> S3 endpoint -> CORS/redirect behavior.", "Quote")]
story.append(PageBreak())

# Testing
story += [p("9. Validation and evidence", "H1x")]
story += [p("Automated and static checks", "H2x")]
checks = [
    ["Check", "Result", "What it proves"],
    ["npm run build", "Passed", "TypeScript compiles and Vite produces a deployable static bundle."],
    ["Python compileall", "Passed", "Backend Python modules are syntactically valid."],
    ["sam validate --lint", "Passed", "The SAM/CloudFormation template is structurally valid after dependency repair."],
    ["Unit tests", "7 passed", "API input validation, owner isolation, download state, image conversion, invalid image rejection, PDF text extraction, and OCR fallback work in isolated tests."],
    ["SAM build", "Exit 0", "Python functions and OCR container build successfully in AWS CloudShell."],
    ["SAM deploy", "Exit 0", "CloudFormation created and later updated the complete stack."],
    ["Amplify job", "SUCCEED", "The production frontend bundle was accepted and published."],
]
story += [table(checks, [40 * mm, 23 * mm, 94 * mm])]
story += [p("Live production checks", "H2x")]
story += [bullets([
    "Loaded the public Amplify URL and confirmed the React upload interface rendered.",
    "Opened Cognito managed sign-in and completed application authentication.",
    "Uploaded the sample photo through a real signed URL; status changed from uploading to processing to completed.",
    "Observed 0.03 MB -> 0.01 MB for the image, consistent with WebP compression.",
    "Uploaded the sample invoice PDF and observed extracted fields including invoice CL-2026-001 and amount 125.00 USD.",
    "Opened My files and confirmed both new records were completed with enabled download actions.",
    "Confirmed the older pending records corresponded to attempts made before the regional S3 fix.",
    "Confirmed Cognito group membership showed admins (1) for the user.",
])]
story += [p("Known limitations", "H2x")]
story += [bullets([
    "The admin metrics implementation scans retained DynamoDB records, which is suitable for a small academic project but should become incremental aggregation at high volume.",
    "OCR is configured for English and its accuracy depends on scan quality.",
    "The interface polls status rather than receiving real-time WebSocket or push updates.",
    "The Free Plan uses credits and has a time limit; resource usage should still be monitored.",
    "SNS email delivery requires a separately confirmed subscription; it is not needed for in-app status updates.",
])]
story.append(PageBreak())

# Cost/ops
story += [p("10. Free Plan, cost awareness, and operations", "H1x")]
story += [p("The deployment was intentionally kept in one region, ap-southeast-2, and used services available to the new AWS Free Plan experience. During deployment, AWS Settings showed the account on the Free Plan with USD 100 in credits and 174 days remaining as of 24 November 2026. These are observed account values, not a guarantee of future availability.", "Callout")]
story += [p("Why the design is economical for a small project", "H2x")]
story += [bullets([
    "Static hosting avoids running a web server continuously.",
    "Lambda charges only for requests and execution duration; no idle compute instance is maintained.",
    "DynamoDB on-demand billing matches irregular project traffic.",
    "S3 is used for binary storage and direct upload, avoiding API Gateway transfer through Lambda.",
    "OCR runs only when a PDF page lacks an embedded text layer.",
    "Resources remain in a single region, avoiding cross-region architecture and transfer complexity.",
])]
story += [p("Operational checklist", "H2x")]
story += [table([
    ["Task", "Where / how"],
    ["Open the application", "https://main.d328vlvqzb3w2y.amplifyapp.com/"],
    ["View deployment state", "CloudFormation stack cloudlens in ap-southeast-2"],
    ["View frontend deploys", "Amplify app d328vlvqzb3w2y, branch main"],
    ["View users/groups", "Cognito user pool ap-southeast-2_VCWLcsYH6"],
    ["View runtime logs", "CloudWatch log groups for API, Admin, and Processor Lambdas"],
    ["View files/status", "Private raw/processed S3 buckets and DynamoDB table created by the stack"],
    ["Control spending", "AWS Billing / Credits; optionally create a budget or credit-usage alert"],
    ["Remove the project", "Delete the CloudFormation stack and Amplify app after first emptying retained storage/repositories as required"],
], [48 * mm, 109 * mm])]
story += [p("Do not present 'free' as unlimited", "H2x")]
story += [p("A correct explanation is: the architecture was selected to fit the Free Plan and consume credits efficiently. Actual usage still consumes credits, and the account can require cleanup or a paid plan after its Free Plan period ends.", "Quote")]
story.append(PageBreak())

# Viva script
story += [p("11. How to explain CloudLens to a professor", "H1x")]
story += [p("Two-minute explanation", "H2x")]
story += [p("CloudLens is an event-driven serverless application for image optimization and PDF text extraction. The frontend is a React application hosted on AWS Amplify. Users authenticate through Amazon Cognito using OAuth Authorization Code with PKCE. Every API route is protected by an API Gateway Cognito authorizer. When a user selects a file, the frontend asks the API Lambda for a short-lived S3 upload URL. The API validates the name, MIME type, and size, creates a pending record in DynamoDB, and returns the URL. The browser uploads directly to a private S3 bucket. That object-created event invokes a container-based Lambda. Images are corrected, resized, watermarked, and converted to WebP. PDFs first use their text layer, and scanned pages use Tesseract OCR. The output goes to a second private bucket, while DynamoDB changes to completed or failed. The frontend polls the API and offers a signed download. An admin group in Cognito grants access to aggregate pipeline metrics. The complete backend is declared with AWS SAM and deployed by CloudFormation.", "Quote")]
story += [p("Likely viva questions", "H2x")]
qa = [
    ["Question", "Suggested answer"],
    ["Why not upload through Lambda?", "Direct S3 upload avoids API Gateway payload constraints and avoids paying Lambda to relay binary data."],
    ["How do you prevent one user reading another user's file?", "The API takes owner from the verified Cognito sub claim and uses it as the DynamoDB partition key and S3 key prefix."],
    ["Why is processing asynchronous?", "Image conversion and OCR can be slow. An S3 event lets upload return quickly and gives the processor an independent timeout and memory allocation."],
    ["Why use a container Lambda?", "Tesseract, PDFium, Pillow, and native libraries need a controlled Linux runtime image."],
    ["How is duplicate processing prevented?", "A conditional DynamoDB update claims only records whose status is still pending."],
    ["How are admin rights implemented?", "Cognito group membership appears in the signed ID token; the Admin Lambda checks admins server-side before reading metrics."],
    ["What was the hardest production bug?", "Global S3 signed URLs caused a 307 redirect in Sydney. Browsers failed the cross-origin PUT. A regional endpoint with SigV4 fixed it."],
    ["What would you improve for production scale?", "Incremental metrics, queues and dead-letter handling, WebSocket status, multi-language OCR, lifecycle policies, and stronger observability."],
]
story += [table(qa, [48 * mm, 109 * mm])]
story.append(PageBreak())

# Appendix
story += [p("12. Reproducible deployment reference", "H1x")]
story += [p("Backend build and deployment", "H2x")]
story += [p("sam build<br/>sam deploy --stack-name cloudlens --region ap-southeast-2 --resolve-s3 --resolve-image-repos --capabilities CAPABILITY_IAM --parameter-overrides FrontendOrigin=https://main.d328vlvqzb3w2y.amplifyapp.com CallbackUrl=https://main.d328vlvqzb3w2y.amplifyapp.com/", "CodexCode")]
story += [p("Production frontend configuration", "H2x")]
story += [p("VITE_API_URL=https://viqn3wmfm2.execute-api.ap-southeast-2.amazonaws.com/prod<br/>VITE_COGNITO_DOMAIN=https://cloudlens-465247576490.auth.ap-southeast-2.amazoncognito.com<br/>VITE_COGNITO_CLIENT_ID=5lg95kk6fon7o2bivrd4s4u3cp", "CodexCode")]
story += [p("Admin membership command", "H2x")]
story += [p("aws cognito-idp admin-add-user-to-group --user-pool-id ap-southeast-2_VCWLcsYH6 --username USER_EMAIL --group-name admins --region ap-southeast-2", "CodexCode")]
story += [p("API routes", "H2x")]
story += [table([
    ["Method and path", "Purpose"],
    ["POST /upload-url", "Validate metadata, create pending record, return signed S3 PUT URL."],
    ["GET /files", "List the signed-in user's files."],
    ["GET /files/{fileId}", "Read one record for polling."],
    ["GET /files/{fileId}/download", "Return signed GET URL only when processing completed."],
    ["DELETE /files/{fileId}", "Delete raw object, processed object, and metadata."],
    ["GET /admin/metrics", "Return aggregate metrics only for admins."],
], [58 * mm, 99 * mm])]
story += [p("Repository map", "H2x")]
story += [table([
    ["Path", "Role"],
    ["template.yaml", "SAM/CloudFormation infrastructure definition."],
    ["backend/api.py", "Authenticated file API and signed URL generation."],
    ["backend/process.py", "Image, PDF, and OCR processing."],
    ["backend/admin.py", "Admin authorization and metrics."],
    ["backend/common.py", "Shared AWS clients, response helpers, status updates, and notifications."],
    ["backend/Dockerfile.processor", "Processor Lambda container with Tesseract."],
    ["src/cloud.ts", "Cognito PKCE, token lifecycle, and API client."],
    ["src/components/UploadView.tsx", "File selection, upload, polling, and result UI."],
    ["tests/", "In-memory API and processing tests."],
], [58 * mm, 99 * mm])]
story += [Spacer(1, 6 * mm), p("End of report", "H2x")]
story += [p("CloudLens demonstrates authentication, direct private storage, event-driven computation, managed metadata, containerized OCR, infrastructure as code, production debugging, and live verification in one compact serverless project.", "Callout")]

doc.build(story)
print(OUT)
