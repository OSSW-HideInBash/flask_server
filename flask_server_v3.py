from flask import Flask, request, jsonify
import os
import uuid
import subprocess
import boto3
import shutil
import logging
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError, NoCredentialsError

app = Flask(__name__)

# --- 설정 및 상수 ---
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Flask 자체 최대 요청 크기 설정
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# S3 설정
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
if not S3_BUCKET:
    raise ValueError("S3_BUCKET_NAME environment variable is required")

S3_BASE_URL = f"https://{S3_BUCKET}.s3.amazonaws.com"

# 기본 디렉토리 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(BASE_DIR, 'examples')
DRAWINGS_DIR = os.path.join(EXAMPLES_DIR, 'drawings')
os.makedirs(DRAWINGS_DIR, exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
)

# S3 클라이언트 초기화
try:
    s3 = boto3.client(
        's3',
        region_name=os.environ.get('AWS_REGION', 'ap-southeast-2'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
    s3.head_bucket(Bucket=S3_BUCKET)
except NoCredentialsError:
    raise ValueError("AWS credentials not found")
except ClientError as e:
    raise ValueError(f"S3 bucket access error: {e}")

# --- 유틸 함수 ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_files(*file_paths):
    for file_path in file_paths:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"Cleaned up file: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                logging.info(f"Cleaned up directory: {file_path}")
        except Exception as e:
            logging.warning(f"Failed to cleanup {file_path}: {e}")

# --- 에러 핸들러 ---
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

# --- 라우터 ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/gif/inside', methods=['POST'])
def generate_gif_inside():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    skeleton_json_file = request.files.get('skeleton_json', None)

    index_str = request.form.get('index')
    if index_str is None:
        return jsonify({'error': 'No index provided'}), 400

    try:
        index = int(index_str)
    except ValueError:
        return jsonify({'error': 'Index must be an integer'}), 400

    if image_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(image_file.filename):
        return jsonify({
            'error': (
                'Invalid file type. Allowed types: '
                f'{", ".join(ALLOWED_EXTENSIONS)}'
            )
        }), 400

    # 파일 크기 확인
    image_file.seek(0, os.SEEK_END)
    file_size = image_file.tell()
    image_file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({
            'error': (
                f'File size exceeds limit '
                f'({MAX_FILE_SIZE // (1024*1024)}MB)'
            )
        }), 413

    unique_id = str(uuid.uuid4())

    filename = secure_filename(image_file.filename)
    safe_filename = f"{unique_id}_{filename}"
    image_path = os.path.join(DRAWINGS_DIR, safe_filename)

    gif_output_dir = os.path.join(BASE_DIR, unique_id)
    gif_path = os.path.join(gif_output_dir, "video.gif")

    skeleton_json_path = os.path.join(gif_output_dir, 'skeleton.json')

    try:
        # 이미지 저장
        image_file.save(image_path)
        logging.info(f"Image saved to: {image_path}")

        # 출력 디렉토리 생성
        os.makedirs(gif_output_dir, exist_ok=True)

        # skeleton_json이 있으면 저장
        if skeleton_json_file:
            skeleton_json_file.save(skeleton_json_path)
            logging.info(f"Skeleton JSON saved to: {skeleton_json_path}")
            command = [
                'python', 'image_to_animation_custom.py',
                image_path, unique_id, str(index), skeleton_json_path
            ]
        else:
            command = [
                'python', 'image_to_animation.py',
                image_path, unique_id, str(index)
            ]

        logging.info(f"Running animation command: {' '.join(command)}")
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        logging.info("Animation script completed successfully")
        logging.info(f"Script stdout: {result.stdout}")
        if result.stderr:
            logging.warning(f"Script stderr: {result.stderr}")

        # S3 업로드
        s3_key = f"{unique_id}/video.gif"
        s3.upload_file(
            gif_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ContentType': 'image/gif',
                'ContentDisposition': (
                    'inline; filename="video.gif"'
                )
            }
        )
        logging.info(f"Uploaded to S3 - Bucket: {S3_BUCKET}, Key: {s3_key}")
        gif_url = f"{S3_BASE_URL}/{s3_key}"
        logging.info(f"Upload successful. URL: {gif_url}")

        return jsonify({'gif_url': gif_url}), 200

    except subprocess.TimeoutExpired:
        logging.error("Animation generation timed out")
        return jsonify({'error': 'Animation generation timed out'}), 408

    except subprocess.CalledProcessError as e:
        logging.error(f"Animation generation failed: {e}")
        logging.error(f"Command output: {e.stdout}")
        logging.error(f"Command stderr: {e.stderr}")
        return jsonify({'error': 'Animation generation failed'}), 500

    except ClientError as e:
        logging.error(f"S3 upload failed: {e}")
        return jsonify({'error': 'File upload failed'}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

    finally:
        cleanup_files(image_path, gif_output_dir)

# --- 메인 실행 ---
if __name__ == '__main__':
    required_env_vars = [
        'S3_BUCKET_NAME',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY'
    ]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)

    animation_script = os.path.join(BASE_DIR, 'image_to_animation.py')
    if not os.path.isfile(animation_script):
        logging.error(f"Animation script not found: {animation_script}")
        exit(1)

    logging.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=False)
