from rdflib import Graph
from pyld import jsonld
import json
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime
import base64
from PIL import Image, ImageDraw, ImageFont
import qrcode
from pathlib import Path
import random

USED_FILE = "used_randoms.json"

def load_used():
    if Path(USED_FILE).exists():
        with open(USED_FILE, "r") as f:
            return json.load(f)
    return {}

def save_used(data):
    with open(USED_FILE, "w") as f:
        json.dump(data, f)

def generate_unique_random():
    today = datetime.now().strftime('%Y%m%d')
    used = load_used()
    used_today = set(used.get(today, []))

    while True:
        num = random.randint(1, 999)
        if num not in used_today:
            used_today.add(num)
            used[today] = list(used_today)
            save_used(used)
            return f"EDUKG-{today}-{num:03d}"

def generate_certificate(name, level, cert_id, qr_data, png_output_path, pdf_output_path):
    # 加载证书背景图片
    background = Image.open("certificate_template.png").convert("RGB")

    # 准备绘图
    draw = ImageDraw.Draw(background)

    # 加载字体（可替换为你自己的路径和字体）
    font_name = ImageFont.truetype(
        "fonts/SourceSans3-SemiBold.ttf", size=160)
    font_level = ImageFont.truetype(
        "fonts/SourceSans3-Bold.ttf", size=90)
    font_info = ImageFont.truetype(
        "fonts/SourceSans3-Regular.ttf", size=78)

    # 写入文字内容
    # Name
    draw.text((background.width/2, background.height/3+150),
              name, fill="#033753", font=font_name, anchor='mm')
    # Level
    draw.text((background.width/3 - 245, background.height/2 - 112),
              level, fill="black", font=font_level)
    # certification ID
    draw.text(
        (background.width/2 - 12, background.height/2+88), cert_id, fill="black", font=font_info)
    # graph name
    draw.text(
        (background.width/2 - 12, background.height/2+184), "Xlore", fill="black", font=font_info)
    # system
    draw.text(
        (background.width/2 - 12, background.height/2+278), "EduKG Certification Platform", fill="black", font=font_info)
    # date issued
    draw.text(
        (background.width/2 - 12, background.height/2+374), datetime.now().strftime('%B %d, %Y'), fill="black", font=font_info)
    # valid until
    future_year = datetime.now().year + 2  # year calculation
    draw.text(
        (background.width/2 - 12, background.height/2+472), datetime.now().strftime(f'%B %d, {future_year}'), fill="black", font=font_info)

    # 生成二维码（二维码内容可替换为你想要的链接或ID）
    qr = qrcode.make(qr_data)

    # 缩放二维码到适当大小（如 300x300）
    qr = qr.resize((200, 200))

    # 粘贴二维码到背景图上（右下角或其他你想要的位置）
    background.paste(qr, (background.width - 250, background.height - 250))

    # 保存为 PDF
    background.save(png_output_path, "PNG")
    background.save(pdf_output_path, "PDF")


def certify(ttl_document, user_name, level_of_conformance):
    # 1. 加载 TTL 文件
    g = Graph()
    g.parse(ttl_document, format="ttl")

    # 2. 转换为 JSON-LD
    jsonld_data = json.loads(g.serialize(format="json-ld"))

    # 3. 使用 URDNA2015 规范化为 N-Quads
    # Converts the JSON-LD data to a consistent form (so that two logically identical graphs will always produce the exact same output) using the URDNA2015 normalization algorithm
    normalized = jsonld.normalize(
    jsonld_data,
    {"algorithm": "URDNA2015", "format": "application/n-quads"}
    )

    # 4. 对 normalized 数据进行 SHA-256 哈希
    # convert raw binary data into a fixed-size string of bytes (32-byte (256-bit))
    # utf-8 convert strings to bytes
    # .digest() returns the binary hash of the input
    hash_digest = hashlib.sha256(normalized.encode("utf-8")).digest()

    # 5. 加载私钥（例如从 PEM 文件加载）
    # rb: read binary mode
    # with open(...) as key_file: automatically closes file afterwards
    # serialization: read and parse the contents of the PEM file (a standard format for storing cryptographic keys)
    # turns the raw file data into a usable RSA private key object 
    # RSA private key object: digitally sign, decrypt data
    with open("key/private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    # 6. 使用 RSA 对哈希进行签名
    signature = private_key.sign(
    hash_digest,
    padding.PKCS1v15(),  # 或者使用 PSS 作为 padding
    hashes.SHA256()
    )


    # 5. 加载私钥（例如从 PEM 文件加载）
    public_key = private_key.public_key()

    # 获取公钥 PEM
    pub_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    # 生成签名证书结构
    certificate = {
    "signature": base64.b64encode(signature).decode('utf-8'),
    "signed_at": datetime.utcnow().isoformat() + "Z",
    "public_key": {
        "key_type": "RSA",
        "key_size": 2048,
        "pem": pub_pem
    },
    "issuer": {
        "name": "edukg certification office",
        "id": "https://edukg.org",
        "contact": "edukg.org@gmail.com"
    }
    }

    

    # generate ID
    id = generate_unique_random()

    # 写入文件
    with open(f"static/certifications/{id}.json", "w") as f:
        json.dump(certificate, f, indent=2)

    # generate hash string
    hash_hex = hash_digest.hex()

    # generate certificate and save it to '.png'
    generate_certificate(user_name, level_of_conformance, id, hash_hex, f'static/certifications/{id}.png', f'static/certifications/{id}.pdf')
    return f"static/certifications/{id}.json", f'static/certifications/{id}.png', f'static/certifications/{id}.pdf'

# example using the certify function
# certify("biology.ttl", "Rosie Wang", "Level II Conformance")