# CloudLens

CloudLens is a serverless image and document processing application. The React frontend signs users in with Cognito, uploads JPG, PNG, and PDF files to private S3 storage through signed URLs, and shows live processing results. An S3 event invokes Lambda to resize, watermark, and encode images as WebP or extract PDF text. Scanned PDF pages are rendered with PDFium and read with Tesseract OCR inside the Lambda container. DynamoDB tracks file status and SNS publishes completion and failure events.

## Live deployment

- Site: https://main.d328vlvqzb3w2y.amplifyapp.com/
- AWS account: `465247576490` (Free Plan); region: `ap-southeast-2`
- CloudFormation stack: `cloudlens`; Amplify app: `d328vlvqzb3w2y`, branch: `main`
- Sign in or sign up through the site's **Sign in** button before processing a file.

## Requirements

- Node.js 20 or later
- Python 3.12 or later for local tests
- AWS CLI and AWS SAM CLI
- Docker with a working Linux container engine (the OCR Lambda is packaged as an image). AWS CloudShell in the project's region can be used when Docker is unavailable locally.
- An AWS account with permissions to create the resources in `template.yaml`

This design uses the services AWS lists for its new Free Plan, including ECR, Lambda, Cognito, S3, DynamoDB, SNS, API Gateway, and CloudFormation. It does not use Textract. The AWS account still must be fully activated before deployment. The Free Plan avoids bills while it is active, but usage consumes credits and the plan ends after six months or when credits run out. Verify that the destination account is on the Free Plan in AWS Billing before deploying; do not upgrade it to a Paid Plan for this project. Free Plan limits and service availability can change; check the [current AWS service list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html) and [AWS plan details](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).

## Deploy the backend

Choose the final frontend origin and callback URL before deploying. Cognito requires an exact callback URL, including its trailing slash if present. For an AWS Free Plan project, deploy all resources in that project's selected region. The example below uses an Amplify Hosting `main` branch in Sydney.

```powershell
sam build
sam deploy --stack-name cloudlens --region ap-southeast-2 --resolve-s3 --resolve-image-repos --capabilities CAPABILITY_IAM --parameter-overrides FrontendOrigin=https://main.d328vlvqzb3w2y.amplifyapp.com CallbackUrl=https://main.d328vlvqzb3w2y.amplifyapp.com/
```

The Amplify app ID above belongs to the CloudLens app in AWS account `465247576490`. The API functions use Python 3.13, available in AWS CloudShell; the OCR function uses its own Python 3.12 container. The image build needs a working Docker Linux engine. Deployment creates AWS resources and consumes Free Plan credits.

SAM prints the API URL, Cognito domain, and app client ID as stack outputs. Add them to a `.env` file based on `.env.example`:

```dotenv
VITE_API_URL=https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/prod
VITE_COGNITO_DOMAIN=https://YOUR_DOMAIN.auth.YOUR_REGION.amazoncognito.com
VITE_COGNITO_CLIENT_ID=YOUR_APP_CLIENT_ID
```

For a different frontend origin, update the stack parameters and rebuild the frontend for that origin.

Run the frontend:

```bash
npm ci
npm run dev
```

Build the static site with `npm run build`. Deploy a zip containing the **contents** of `dist/` (with `index.html` at the zip root) to the Amplify Hosting branch used in the stack parameters. The stack creates private storage, not a public frontend host. See [Amplify manual deployments](https://docs.aws.amazon.com/amplify/latest/userguide/manual-deploys.html) for the console flow.

## Admin access and notifications

The Admin tab displays live totals for an account in the Cognito `admins` group. After a user signs up through the Cognito sign-in page, add that user with:

```bash
aws cognito-idp admin-add-user-to-group --user-pool-id YOUR_USER_POOL_ID --username USER_EMAIL --group-name admins
```

The stack outputs `NotificationsTopicArn`. Subscribe an email address if you want SNS completion and failure messages delivered by email:

```bash
aws sns subscribe --topic-arn YOUR_NOTIFICATIONS_TOPIC_ARN --protocol email --notification-endpoint YOU@example.com
```

Confirm the subscription from the email message. The app also polls file status, so subscribed email is optional. SNS messages contain file metadata; use a trusted address for the subscription.

## API

All routes require a Cognito ID token. File routes are scoped to the token's user ID.

| Route | Purpose |
| --- | --- |
| `POST /upload-url` | Validate name, MIME type and size, create a pending record, return a 15 minute S3 PUT URL |
| `GET /files` | List the signed-in user's files and status |
| `GET /files/{fileId}` | Poll one file |
| `GET /files/{fileId}/download` | Return a short-lived download URL for completed output |
| `DELETE /files/{fileId}` | Delete raw and processed objects and metadata |
| `GET /admin/metrics` | Return aggregate counts, failure rate, average latency, and saved bytes to admins |

Images are capped at 1920 × 1920 pixels and saved as WebP. PDF output is extracted UTF-8 text (`.txt`). PDFs can contain up to 25 pages. Pages with an existing text layer use that text directly; scanned pages use English Tesseract OCR. The 10 MB limit is checked both in the browser and in the processing Lambda. A signed PUT can technically upload a larger object, but the Lambda rejects it before processing. OCR latency depends on page count and scan quality.

The dashboard aggregates retained DynamoDB records and is intended for a small project deployment. For high-volume production use, maintain counters incrementally instead of scanning the table. Notifications are topic-level SNS events; they are not automatically addressed to each uploader.

## Validation

```bash
npm run build
python -m compileall -q backend
sam validate --lint
python -m unittest discover -s tests -v
```

The processing tests need local `Pillow` and `pypdfium2` installations. They exercise PDF rendering with a simulated OCR executable; the Lambda container build and real scanned-document OCR require Docker and should be tested before deployment.
