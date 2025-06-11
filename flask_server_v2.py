from flask import Flask, request, jsonify
import os
import uuid
import subprocess
import boto3
import shutil
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError, NoCredentialsError

app = Flask(__name__)

# Configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# S3 설정
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
if not S3_BUCKET:
    raise ValueError("S3_BUCKET_NAME environment variable is required")

S3_BASE_URL = f"https://{S3_BUCKET}.s3.amazonaws.com"

# S3 클라이언트 초기화
try:
    s3 = boto3.client(
        's3',
        region_name=os.environ.get('AWS_REGION', 'ap-southeast-2'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
    # S3 연결 테스트
    s3.head_bucket(Bucket=S3_BUCKET)
except NoCredentialsError:
    raise ValueError("AWS credentials not found")
except ClientError as e:
    raise ValueError(f"S3 bucket access error: {e}")

# 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(BASE_DIR, 'examples')
DRAWINGS_DIR = os.path.join(EXAMPLES_DIR, 'drawings')

# 디렉토리 생성
os.makedirs(DRAWINGS_DIR, exist_ok=True)

def allowed_file(filename):
    """파일 확장자 검증"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_files(*file_paths):
    """파일 정리 함수"""
    for file_path in file_paths:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"[INFO] Cleaned up file: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"[INFO] Cleaned up directory: {file_path}")
        except Exception as e:
            print(f"[WARNING] Failed to cleanup {file_path}: {e}")

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/gif/inside', methods=['POST'])
def generate_gif_inside():
    """이미지를 애니메이션 GIF로 변환하는 엔드포인트"""
    
    # 파일 존재 여부 확인
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    
    # 파일명 확인
    if image_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # 파일 확장자 검증
    if not allowed_file(image_file.filename):
        return jsonify({
            'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # 파일 크기 검증 (클라이언트 측에서도 체크하지만 서버에서 재확인)
    image_file.seek(0, os.SEEK_END)
    file_size = image_file.tell()
    image_file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'File size exceeds limit ({MAX_FILE_SIZE // (1024*1024)}MB)'}), 413
    
    # 고유 ID 생성
    unique_id = str(uuid.uuid4())
    
    # 파일 경로 설정
    filename = secure_filename(image_file.filename)
    # 파일명에 고유 ID 추가하여 충돌 방지
    safe_filename = f"{unique_id}_{filename}"
    image_path = os.path.join(DRAWINGS_DIR, safe_filename)
    
    # GIF 출력 경로 설정
    gif_output_dir = os.path.join(BASE_DIR, unique_id)
    gif_path = os.path.join(gif_output_dir, "video.gif")
    
    try:
        # 파일 저장
        image_file.save(image_path)
        print(f"[INFO] Image saved to: {image_path}")
        
        # 이미지 처리 스크립트 실행
        command = [
            'python', 'image_to_animation.py', 
            image_path, unique_id
        ]
        
        print(f"[INFO] Running animation command: {' '.join(command)}")
        print(f"[INFO] Working directory: {BASE_DIR}")
        print(f"[INFO] Expected output directory: {gif_output_dir}")
        print(f"[INFO] Expected GIF path: {gif_path}")
        
        # 출력 디렉토리가 존재하는지 확인
        if os.path.exists(gif_output_dir):
            print(f"[INFO] Output directory already exists: {gif_output_dir}")
        else:
            print(f"[INFO] Output directory will be created: {gif_output_dir}")
        
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        print(f"[INFO] Animation script completed successfully")
        print(f"[INFO] Script stdout: {result.stdout}")
        if result.stderr:
            print(f"[WARNING] Script stderr: {result.stderr}")
        
       
        # S3 업로드
        # 현재 실행 중인 디렉토리
        

        s3_key = f"{unique_id}/video.gif"
        
        
        s3.upload_file(
            gif_path, 
            S3_BUCKET, 
            s3_key,
            ExtraArgs={
                'ContentType': 'image/gif',
                'ContentDisposition': f'inline; filename="video.gif"'
            }
        )
        print(f"[INFO] Uploading to S3 - Bucket: {S3_BUCKET}, Key: {s3_key}")
        gif_url = f"{S3_BASE_URL}/{s3_key}"
        print(f"[INFO] Upload successful. URL: {gif_url}")
        
        return jsonify({'gif_url': gif_url}), 200
        
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Animation generation timed out")
        return jsonify({'error': 'Animation generation timed out'}), 408
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Animation generation failed: {e}")
        print(f"[ERROR] Command output: {e.stdout}")
        print(f"[ERROR] Command stderr: {e.stderr}")
        return jsonify({'error': 'Animation generation failed'}), 500
        
    except ClientError as e:
        print(f"[ERROR] S3 upload failed: {e}")
        return jsonify({'error': 'File upload failed'}), 500
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
        
    finally:
        # 파일 정리
        cleanup_files(image_path, gif_output_dir)


if __name__ == '__main__':
    # 필요한 환경 변수 확인
    required_env_vars = ['S3_BUCKET_NAME', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    # image_to_animation.py 스크립트 존재 여부 확인
    animation_script = os.path.join(BASE_DIR, 'image_to_animation.py')
    if not os.path.isfile(animation_script):
        print(f"[ERROR] Animation script not found: {animation_script}")
        exit(1)
    
    print("[INFO] Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=False)