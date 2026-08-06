from app.database.db import Base, engine

# 모든 모델 import (매우 중요)
from app.models import *

Base.metadata.create_all(bind=engine)

print("✅ 모든 테이블이 생성되었습니다.")