# Flask 이미지 to GIF 애니메이션 API

업로드된 이미지를 애니메이션 GIF로 변환하고 Amazon S3에 저장하는 Flask 기반 웹 서비스입니다.

## 주요 기능

- 이미지 파일 업로드 및 애니메이션 GIF 변환
- Amazon S3 자동 저장 및 공개 URL 생성
- 처리 후 파일 자동 정리
- 에러 처리 및 로깅
- RESTful API 엔드포인트 제공
- 파일 형식 지정자(.png, .jpg,...) 제한 추가
- json 형식으로 지정된 관절들의 좌표를 통해 사용자가 수동으로 관절과 뼈의 좌표를 수정할 수 있음.

## 사전 요구사항

- Python 3.x
- Flask
- boto3 (AWS SDK)
- werkzeug
- 동일 디렉토리에 `image_to_animation.py` 스크립트 필요
- 적절한 권한이 설정된 AWS S3 버킷

## 환경 변수 설정

애플리케이션 실행 전 다음 환경 변수를 설정해주세요:

```bash
export S3_BUCKET_NAME=your-s3-bucket-name
export AWS_ACCESS_KEY_ID=your-aws-access-key
export AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

## 설치 방법

1. 프로젝트 파일을 클론하거나 다운로드
2. 필요한 의존성 설치:
   ```bash
   pip install flask boto3 werkzeug
   ```
3. Flask 앱과 같은 디렉토리에 `image_to_animation.py` 파일이 있는지 확인
4. 환경 변수 설정
5. 애플리케이션 실행:
   ```bash
   python app.py
   ```

## API 엔드포인트

### POST `/gif/inside`

업로드된 이미지를 애니메이션 GIF로 변환합니다.

**요청:**
- 메소드: `POST`
- Content-Type: `multipart/form-data`
- 본문: `image` 필드에 이미지 파일을 포함한 Form 데이터

**응답:**
- 성공 (200): 
  ```json
  {
    "gif_url": "https://your-bucket.s3.amazonaws.com/uuid/video.gif"
  }
  ```
- 에러 (400/500):
  ```json
  {
    "error": "에러 설명"
  }
  ```

## 사용 예제

curl 사용:
```bash
curl -X POST \
  http://localhost:5000/gif/inside \
  -F "image=@/path/to/your/image.jpg"
```

Python requests 사용:
```python
import requests

url = "http://localhost:5000/gif/inside"
files = {"image": open("your_image.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

## 디렉토리 구조

```
project/
├── app.py                    # 메인 Flask 애플리케이션
├── image_to_animation.py     # 애니메이션 생성 스크립트
└── examples/
    └── drawings/             # 업로드된 이미지 임시 저장소
```

## 동작 방식

1. 사용자가 `/gif/inside` 엔드포인트로 이미지를 POST 요청으로 업로드
2. 이미지가 `examples/drawings/` 디렉토리에 임시 저장
3. `image_to_animation.py` 스크립트를 호출하여 GIF 생성
4. 생성된 GIF를 고유한 UUID 기반 경로로 S3에 업로드
5. 공개 S3 URL을 사용자에게 반환
6. 임시 파일들을 정리

## 설정

- **서버**: 기본적으로 `0.0.0.0:5000`에서 실행
- **AWS 리전**: `ap-southeast-2` (시드니)
- **파일 보안**: 업로드된 파일에 `secure_filename()` 사용
- **고유 ID**: GIF 명명에 UUID4 사용

## 에러 처리

API는 다양한 오류 상황을 처리합니다:
- 요청에 이미지가 없는 경우
- 애니메이션 생성 실패
- S3 업로드 오류
- 파일 시스템 오류

모든 오류는 적절한 오류 메시지와 HTTP 상태 코드와 함께 로그에 기록됩니다.

## 보안 참고사항

- 경로 탐색 공격을 방지하기 위해 `secure_filename()`으로 파일 처리
- 임시 파일 자동 정리
- AWS 자격 증명은 안전하게 보관하고 하드코딩하지 말 것

## 의존성

- `flask`: 웹 프레임워크
- `boto3`: Python용 AWS SDK
- `werkzeug`: 안전한 파일명 처리를 위한 WSGI 유틸리티
- `uuid`: 고유 식별자 생성
- `subprocess`: 애니메이션 스크립트 실행
- `os`: 파일 시스템 작업

## 주의사항

- `image_to_animation.py` 스크립트가 올바르게 작동하는지 확인
- S3 버킷에 적절한 읽기/쓰기 권한이 설정되어 있는지 확인
- 프로덕션 환경에서는 적절한 보안 설정 추가 고려
