-- ==========================================================
-- 초기 관리자 계정 생성 (개발용)
-- username: admin
-- password: admin
-- ==========================================================

INSERT INTO users (username, password_hash)
VALUES (
  'admin',
  '$2b$12$CFXcKIp5jm3FRZTLneNqwOUrbvqOXZmtAmPKSAe0isbYVg7oD6nMG'
);