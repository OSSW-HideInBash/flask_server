🎞️ AnimatedDrawings GIF 생성 서버
이 서버는 이미지와 JSON 형식의 스켈레톤 정보를 받아 애니메이션 GIF를 생성하고, 이를 AWS S3에 업로드하여 URL로 반환합니다.

📦 기능 개요
/gif/inside
이미지와 스켈레톤 JSON을 받아 내부 애니메이션 스크립트를 실행하고 GIF 생성
생성된 GIF는 S3에 업로드되어 클라이언트에 URL 반환

/health
서버 상태 확인용 헬스체크 API

🏗️ 프로젝트 구조
bash
복사
편집
.
├── app.py                    # Flask 서버 메인 코드
├── image_to_animation.py     # 애니메이션 생성 Python 스크립트
├── examples/
│   └── drawings/             # 업로드된 이미지 저장 디렉토리
├── requirements.txt          # 필요 패키지 명시 (생성 필요)
🚀 실행 방법
1. 환경 변수 설정
다음 환경 변수를 .env 또는 시스템에 설정해야 합니다:

변수 이름	설명
S3_BUCKET_NAME	업로드할 S3 버킷 이름
AWS_ACCESS_KEY_ID	AWS 액세스 키
AWS_SECRET_ACCESS_KEY	AWS 시크릿 키
AWS_REGION	AWS 리전 (기본값: ap-southeast-2)

2. 패키지 설치
bash
복사
편집
pip install -r requirements.txt
boto3, Flask, werkzeug, python-dotenv 등 포함

3. 실행
bash
복사
편집
python app.py
서버는 http://localhost:5000 에서 실행됩니다.

📤 /gif/inside API
✅ 요청
POST /gif/inside
multipart/form-data 형식

필드
image: 이미지 파일 (.jpg, .png, .gif 등)

skeleton_json: 스켈레톤 JSON 파일

index: 정수 인덱스 (예: "0")

예시 (cURL)
bash
복사
편집
curl -X POST http://localhost:5000/gif/inside \
  -F "image=@test.jpg" \
  -F "skeleton_json=@skeleton.json" \
  -F "index=0"
🔁 응답
json
복사
편집
{
  "gif_url": "https://<S3_BUCKET>.s3.amazonaws.com/<uuid>/video.gif"
}
📡 /health
GET /health

서버 헬스체크용

응답
json
복사
편집
{
  "status": "healthy"
}
🧹 기타 기능
파일 크기 제한: 16MB

안전한 파일 이름 처리 및 디렉토리 정리

애니메이션 생성 중 에러/타임아웃 로그 처리

🛠️ 개발자 참고
image_to_animation.py는 다음 인자를 받습니다:

bash
복사
편집
python image_to_animation.py <image_path> <uuid> <skeleton_json_path> <index>
이 스크립트는 내부에서 examples/<uuid>/video.gif를 생성해야 합니다.

🧪 테스트 체크리스트
 이미지 및 JSON 업로드 정상 처리

 잘못된 파일 확장자 처리

 큰 파일 업로드 차단

 S3 업로드 성공 여부 확인

 예외 발생 시 적절한 에러 메시지 반환

 서버 헬스체크 (/health) 동작 확인

📄 라이선스
MIT License © Meta Platforms, Inc. and affiliates.

원하는 형식이나 추가하고 싶은 내용이 있다면 알려주세요. requirements.txt, Dockerfile 등이 필요하면 추가로 작성해드릴 수 있어요.








