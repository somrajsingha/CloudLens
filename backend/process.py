import io
import os
import subprocess
from urllib.parse import unquote_plus

import pypdfium2 as pdfium
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from common import claim_file, get_file, notify, s3, update_file

RAW = os.environ['RAW_BUCKET']
PROCESSED = os.environ['PROCESSED_BUCKET']
MAX_PDF_PAGES = 25
MAX_RENDERED_PIXELS = 20_000_000


def handler(event, _context):
    for record in event['Records']:
        key = unquote_plus(record['s3']['object']['key'])
        parts = key.split('/', 2)
        if len(parts) != 3:
            continue
        item = get_file(parts[0], parts[1])
        if not item or item['rawKey'] != key or item['status'] != 'pending':
            continue
        try:
            claim_file(item)
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
                continue
            raise
        try:
            metadata = s3.head_object(Bucket=RAW, Key=key)
            if metadata['ContentLength'] != item['size'] or metadata['ContentLength'] > 10 * 1024 * 1024:
                raise ValueError('Uploaded size does not match the validated request.')
            if metadata['ContentType'] != item['contentType']:
                raise ValueError('Uploaded content type does not match the validated request.')
            if item['type'] == 'image':
                process_image(item)
            else:
                process_pdf(item)
        except Exception as exc:
            update_file(item, 'failed', error=str(exc)[:500])
            notify(item, 'failed', str(exc)[:500])
            raise


def process_image(item):
    raw = s3.get_object(Bucket=RAW, Key=item['rawKey'])['Body'].read()
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image).convert('RGB')
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError('The image is damaged or unsupported.') from exc
    image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    label = 'CloudLens'
    font = ImageFont.load_default(size=max(15, image.width // 55))
    bbox = draw.textbbox((0, 0), label, font=font)
    x = max(0, image.width - (bbox[2] - bbox[0]) - 18)
    y = max(0, image.height - (bbox[3] - bbox[1]) - 18)
    draw.text((x, y), label, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0), font=font)
    output = io.BytesIO()
    image.save(output, format='WEBP', quality=78, method=6)
    data = output.getvalue()
    output_key = f'{item["owner"]}/{item["fileId"]}/image.webp'
    s3.put_object(Bucket=PROCESSED, Key=output_key, Body=data, ContentType='image/webp')
    update_file(item, 'completed', processedKey=output_key, processedSize=len(data))
    notify(item, 'completed')


def process_pdf(item):
    raw = s3.get_object(Bucket=RAW, Key=item['rawKey'])['Body'].read()
    document = pdfium.PdfDocument(raw)
    try:
        if not 0 < len(document) <= MAX_PDF_PAGES:
            raise ValueError(f'PDF must contain between 1 and {MAX_PDF_PAGES} pages.')
        pages = []
        for index in range(len(document)):
            page = document[index]
            try:
                text_page = page.get_textpage()
                try:
                    text = text_page.get_text_bounded().strip()
                finally:
                    text_page.close()
                if not text:
                    width, height = page.get_size()
                    if width * height * 4 > MAX_RENDERED_PIXELS:
                        raise ValueError(f'Page {index + 1} is too large for OCR.')
                    bitmap = page.render(scale=2)
                    try:
                        image = bitmap.to_pil()
                        try:
                            buffer = io.BytesIO()
                            image.save(buffer, format='PNG')
                        finally:
                            image.close()
                    finally:
                        bitmap.close()
                    try:
                        result = subprocess.run(
                            [os.environ.get('TESSERACT_BIN', 'tesseract'), 'stdin', 'stdout', '-l', 'eng'],
                            input=buffer.getvalue(), capture_output=True, check=True, timeout=30,
                        )
                    except subprocess.TimeoutExpired as exc:
                        raise ValueError(f'OCR timed out on page {index + 1}.') from exc
                    except (OSError, subprocess.CalledProcessError) as exc:
                        raise ValueError(f'OCR failed on page {index + 1}.') from exc
                    text = result.stdout.decode('utf-8', errors='replace').strip()
                pages.append(text)
            finally:
                page.close()
        text = '\n\n'.join(pages).strip()
        if not text:
            raise ValueError('No text could be extracted from this PDF.')
        data = text.encode('utf-8')
        key = f'{item["owner"]}/{item["fileId"]}/extracted.txt'
        s3.put_object(Bucket=PROCESSED, Key=key, Body=data, ContentType='text/plain; charset=utf-8')
        update_file(item, 'completed', processedKey=key, processedSize=len(data), extractedText=text[:1000])
        notify(item, 'completed')
    finally:
        document.close()
