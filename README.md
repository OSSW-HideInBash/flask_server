# Flask Animation API

이미지를 애니메이션 GIF로 변환하는 Flask 기반 REST API 서비스입니다.

## 🚀 주요 기능

- 이미지 파일을 애니메이션 GIF로 변환
- 스켈레톤 JSON 데이터를 활용한 애니메이션 생성
- AWS S3 자동 업로드 및 URL 반환
- 파일 크기 제한 및 보안 검증
- 자동 임시 파일 정리
- 스켈레톤 JSON 데이터 없는 경우 자동으로 골격 인식

## 📋 요구사항

### 시스템 요구사항
- Python 3.8+
- Flask
- boto3
- 'image_to_animation.py' 스크립트
- -'image_to_animation_custom.py' 스크립트

### AWS 계정 및 S3 버킷
- AWS 계정 및 액세스 키
- S3 버킷 (퍼블릭 읽기 권한 필요)

## 🛠️ 설치 및 설정

### 1. 의존성 설치
```bash
pip install flask boto3 werkzeug
```

### 2. 환경 변수 설정
다음 환경 변수들을 설정해야 합니다:

```bash
export S3_BUCKET_NAME="your-s3-bucket-name"
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_REGION="ap-southeast-2"  # 선택사항 (기본값: ap-southeast-2)
```

또는 `.env` 파일을 생성하여 관리할 수 있습니다.

### 3. 필수 파일 준비
- `image_to_animation.py`: 애니메이션 생성 스크립트
- `examples/drawings/`: 이미지 임시 저장 디렉토리 (uuid 이용하여 자동 생성)

## 🚀 실행
골격을 수동으로 조정하지 않았을 경우
```bash
python image_to_animagetion.py 사진디렉토리 동작종류(0~5 integer)
```
골격을 수동으로 조정한 경우

python image_to_animagetion.py 사진디렉토리 동작종류(0~5 integer) skeleton.json

서버는 `http://0.0.0.0:5000`에서 실행됩니다.

## skeleton.json 예시
{
  "skeleton": [
    { "loc": [278, 446], "name": "root", "parent": null },
    { "loc": [278, 446], "name": "hip", "parent": "root" },
    { "loc": [278, 191], "name": "torso", "parent": "hip" },
    { "loc": [278, 258], "name": "neck", "parent": "torso" },
    { "loc": [142, 200], "name": "right_shoulder", "parent": "torso" },
    { "loc": [96, 161], "name": "right_elbow", "parent": "right_shoulder" },
    { "loc": [58, 123], "name": "right_hand", "parent": "right_elbow" },
    { "loc": [414, 181], "name": "left_shoulder", "parent": "torso" },
    { "loc": [439, 136], "name": "left_elbow", "parent": "left_shoulder" },
    { "loc": [459, 84], "name": "left_hand", "parent": "left_elbow" },
    { "loc": [193, 446], "name": "right_hip", "parent": "root" },
    { "loc": [181, 517], "name": "right_knee", "parent": "right_hip" },
    { "loc": [168, 582], "name": "right_foot", "parent": "right_knee" },
    { "loc": [362, 446], "name": "left_hip", "parent": "root" },
    { "loc": [375, 511], "name": "left_knee", "parent": "left_hip" },
    { "loc": [394, 569], "name": "left_foot", "parent": "left_knee" }
  ]
}

## 📡 API 엔드포인트

### 1. 헬스 체크
```
GET /health
```

**응답:**
```json
{
  "status": "healthy"
}
```

### 2. 애니메이션 GIF 생성
```
POST /gif/inside
```

**요청 파라미터:**
- `image` (파일): 애니메이션으로 변환할 이미지 파일
- `skeleton_json` (파일): 스켈레톤 데이터 JSON 파일
- `index` (폼 데이터): 애니메이션 인덱스 (정수)

**지원 이미지 형식:**
- PNG, JPG, JPEG, GIF, BMP, WEBP

**파일 크기 제한:**
- 최대 16MB

**성공 응답:**
```json
{
  "gif_url": "https://your-bucket.s3.amazonaws.com/unique-id/video.gif"
}
```

**에러 응답:**
```json
{
  "error": "Error message"
}
```

## 🔧 사용 예시

### cURL 사용
```bash
curl -X POST \
  -F "image=@/path/to/image.jpg" \
  -F "skeleton_json=@/path/to/skeleton.json" \
  -F "index=1" \
  http://localhost:5000/gif/inside
```

### Python requests 사용
```python
import requests

url = "http://localhost:5000/gif/inside"
files = {
    'image': open('image.jpg', 'rb'),
    'skeleton_json': open('skeleton.json', 'rb')
}
data = {'index': 1}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result['gif_url'])
```

## ⚠️ 에러 코드

| 상태 코드 | 설명 |
|-----------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (파일 누락, 잘못된 형식 등) |
| 408 | 타임아웃 (애니메이션 생성 시간 초과) |
| 413 | 파일 크기 초과 |
| 500 | 서버 내부 오류 |

## 🔒 보안 고려사항

- 파일명 보안 처리 (`secure_filename` 사용)
- 파일 크기 제한 (16MB)
- 허용된 파일 확장자만 처리
- 임시 파일 자동 정리
- 타임아웃 설정 (300초)

## 📁 프로젝트 구조

```
project/
├── app.py                  # 메인 Flask 애플리케이션
├── image_to_animation.py   # 애니메이션 생성 스크립트
├── examples/
│   └── drawings/          # 임시 이미지 저장 디렉토리
└── README.md
```

## 🐛 트러블슈팅

### 1. AWS 자격 증명 오류
```
ValueError: AWS credentials not found
```
- AWS 환경 변수가 올바르게 설정되었는지 확인
- AWS CLI 설정 확인: `aws configure list`

### 2. S3 버킷 접근 오류
```
ValueError: S3 bucket access error
```
- S3 버킷 이름이 올바른지 확인
- 버킷 권한 설정 확인
- 리전 설정 확인

### 3. 애니메이션 스크립트 오류
```
Animation script not found
```
- `image_to_animation.py` 파일이 존재하는지 확인
- 파일 실행 권한 확인

## 📝 개발 노트

- 모든 임시 파일은 요청 완료 후 자동으로 정리됩니다
- 애니메이션 생성 타임아웃은 300초로 설정되어 있습니다
- 로깅은 INFO 레벨로 설정되어 있습니다
- 프로덕션 환경에서는 `debug=False`로 설정됩니다

## 📄 라이센스

이 프로젝트의 라이센스에 대한 정보는 별도로 제공됩니다.
