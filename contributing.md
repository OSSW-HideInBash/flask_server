🧠 Contributing to AnimatedDrawings Flask Server
감사합니다! 이 저장소에 기여해 주셔서 감사합니다.
이 문서는 Flask 기반 애니메이션 생성 서버에 기여하기 위한 가이드입니다.

📦 프로젝트 구조
plaintext
복사
편집
.
├── app.py                      # Flask 서버 메인 파일
├── image_to_animation.py       # 기본 애니메이션 스크립트
├── image_to_animation_custom.py# 커스텀 스켈레톤 사용 시 애니메이션 스크립트
├── examples/
│   └── drawings/               # 업로드된 이미지 저장 경로
├── requirements.txt            # 필요한 Python 패키지 목록
└── ...
⚙️ 환경 변수 설정
이 프로젝트는 AWS S3와 연동되며, 다음 환경 변수가 반드시 필요합니다:

환경 변수	설명
S3_BUCKET_NAME	업로드할 S3 버킷 이름
AWS_ACCESS_KEY_ID	AWS IAM Access Key
AWS_SECRET_ACCESS_KEY	AWS IAM Secret Key
AWS_REGION	(선택) AWS 리전, 기본값: ap-southeast-2

.env 파일을 사용할 경우, 루트 디렉토리에 아래처럼 작성:

env
복사
편집
S3_BUCKET_NAME=your_bucket_name
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-southeast-2
🛠 설치 및 실행
bash
복사
편집
# 가상 환경 구성 (선택)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python app.py
서버는 기본적으로 http://localhost:5000 에서 실행됩니다.

🧪 테스트 및 엔드포인트
헬스 체크
bash
복사
편집
GET /health
애니메이션 생성
bash
복사
편집
POST /gif/inside

Form Data:
- image (필수): 업로드할 이미지 파일 (PNG, JPG 등)
- skeleton_json (선택): 커스텀 스켈레톤 JSON
- index (필수): 애니메이션 인덱스 (정수)

Response:
{
  "gif_url": "https://{S3_BUCKET}.s3.amazonaws.com/uuid/video.gif"
}
💡 기여 가이드라인
Fork 후 작업

새로운 브랜치에서 기능 개발

PEP8 스타일 가이드에 맞춰 코드 작성

기능/버그 단위로 커밋

Pull Request 생성 전 아래 확인사항 체크

체크리스트
 서버가 정상적으로 실행됨

 이미지 및 JSON 업로드 테스트 통과

 로그에 에러 없이 성공적으로 S3 업로드됨

 관련 스크립트 존재 확인 (image_to_animation.py, image_to_animation_custom.py)

📄 참고
이미지 최대 크기: 16MB

허용 확장자: .png, .jpg, .jpeg, .gif, .bmp, .webp

타임아웃: 애니메이션 생성 시 최대 5분 (timeout=300)
