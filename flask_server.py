from flask import Flask, request, jsonify
import os
import uuid
import subprocess
import boto3
from werkzeug.utils import secure_filename

app = Flask(__name__)

# S3 설정
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
S3_BASE_URL = f"https://{S3_BUCKET}.s3.amazonaws.com"

s3 = boto3.client(
    's3',
    region_name='ap-southeast-2',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일 기준
EXAMPLES_DIR = os.path.join(BASE_DIR, 'examples')
DRAWINGS_DIR = os.path.join(EXAMPLES_DIR, 'drawings')

os.makedirs(DRAWINGS_DIR, exist_ok=True)

@app.route('/gif/inside', methods=['POST'])
def generate_gif_inside():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image_file = request.files['image']
    filename = secure_filename(image_file.filename)
    image_path = os.path.join(DRAWINGS_DIR, filename)
    image_file.save(image_path)

    gif_name = str(uuid.uuid4())
    # gif_name 폴더가 EXAMPLES_DIR 바로 아래 생성됨이 맞으므로
    gif_output_dir = os.path.join(EXAMPLES_DIR, gif_name)
    gif_path = os.path.join(gif_output_dir, "video.gif")

    command = f"python image_to_animation.py {image_path} {gif_name}"

    try:
        print(f"[INFO] Running animation command: {command}")
        subprocess.run(command, shell=True, check=True, cwd=BASE_DIR)

        # 애니메이션 생성 후 gif_path 존재 여부 확인
        if not os.path.isfile(gif_path):
            print(f"[ERROR] Gif file not found at expected path: {gif_path}")
            return jsonify({'error': 'Gif file not found after animation'}), 500

        s3_key = f"{gif_name}/video.gif"
        print(f"[INFO] Uploading to S3 bucket: {S3_BUCKET}, key: {s3_key}")

        s3.upload_file(gif_path, S3_BUCKET, s3_key, ExtraArgs={'ContentType': 'image/gif'})
        gif_url = f"{S3_BASE_URL}/{s3_key}"

        return jsonify({'gif_url': gif_url}), 200

    except subprocess.CalledProcessError as e:
        print("[ERROR] Animation generation failed:", e)
        return jsonify({'error': f'Animation generation failed: {e}'}), 500

    except Exception as e:
        print("[ERROR] Server error:", e)
        return jsonify({'error': f'Server error: {e}'}), 500

    finally:
        try:
            if os.path.exists(gif_path):
                os.remove(gif_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print("[WARNING] File cleanup error:", e)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
