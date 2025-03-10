const { Server } = require('@hocuspocus/server');
const { Database } = require('@hocuspocus/extension-database');
const { Logger } = require('@hocuspocus/extension-logger');
const { Redis } = require('@hocuspocus/extension-redis');
const axios = require('axios');
const Y = require('yjs'); // Yjs 임포트

const HOCUSPOCUS_HOST = '0.0.0.0';
const HOCUSPOCUS_PORT = 8443;
const API_BASE_URL = 'http://localhost:8080/api/v1'; // 백엔드 API 주소

// Redis 설정 (환경변수 REDIS_URL 사용)
const redisConfig = process.env.REDIS_URL
  ? {
      host: new URL(process.env.REDIS_URL).hostname,
      port: Number(new URL(process.env.REDIS_URL).port) || 6379,
      password: new URL(process.env.REDIS_URL).password || undefined
    }
  : null;

// noteId별 디바운스 타이머를 저장할 맵
const debounceMap = new Map();

const server = Server.configure({
  address: HOCUSPOCUS_HOST,
  port: HOCUSPOCUS_PORT,
  
  async onConnect(data) {
    const { request, requestHeaders, documentName } = data;
    console.log(`사용자가 문서에 연결됨: ${documentName}`);
    // (인증 및 권한 확인 로직 생략)
    return true;
  },
  
  extensions: [
    new Logger({
      onChange: true,
      onLoadDocument: true,
      onStoreDocument: true,
      onConnect: true,
      onDisconnect: true,
      onUpgrade: true,
      onRequest: true,
      onDestroy: true,
      onConfigure: true
    }),
    
    ...(redisConfig
      ? [
          new Redis({
            host: redisConfig.host,
            port: redisConfig.port,
            options: {
              password: redisConfig.password
            }
          })
        ]
      : []),
   
  ]
});

server.listen();
console.log(`Hocuspocus 협업 서버가 시작되었습니다. (포트: ${HOCUSPOCUS_PORT})`);
