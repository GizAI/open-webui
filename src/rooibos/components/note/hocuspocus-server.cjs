const { Server } = require('@hocuspocus/server');
const { Database } = require('@hocuspocus/extension-database');
const { Logger } = require('@hocuspocus/extension-logger');
const { Redis } = require('@hocuspocus/extension-redis');
const axios = require('axios');
const Y = require('yjs'); // Yjs 임포트

const HOCUSPOCUS_HOST = '0.0.0.0';
const HOCUSPOCUS_PORT = 1234;
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
    
    new Database({
      fetch: async (data) => {
        try {
          const noteId = data.documentName.split(':')[1];
          if (!noteId) return null;
          
          const token = data.requestHeaders.authorization?.replace('Bearer ', '');
          const response = await axios.get(`${API_BASE_URL}/rooibos/notes/${noteId}`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            responseType: 'arraybuffer'
          });
          
          return response.data.note;
        } catch (error) {
          console.error('문서 가져오기 오류:', error);
          return null;
        }
      },
      
      // 저장 함수에 디바운스 적용: 1초 동안 입력이 없으면 저장
      store: async (data) => {
        console.log("!!!!!!!!!!!!!!!!!!!!!!!!");
        const noteId = data.documentName.split(':')[1];
        if (!noteId) return;
        
        // 기존에 타이머가 있으면 취소
        if (debounceMap.has(noteId)) {
          clearTimeout(debounceMap.get(noteId));
        }
        
        // 1초 후 저장 실행
        debounceMap.set(noteId, setTimeout(async () => {
          try {
            // Yjs 문서 업데이트 형식으로 변환
            const update = Y.encodeStateAsUpdate(data.document);
            console.log("=======================");
            console.log(update);
            // 필요에 따라 제목 추출 로직을 추가할 수 있음
            const queryParams = new URLSearchParams({ noteId });
            const res = await fetch(
                `${API_BASE_URL}/rooibos/notes/update/?${queryParams.toString()}`,
                {
                  method: 'PUT',
                  headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({ content: update })
                }
              )

            console.log(`문서 저장 완료: ${noteId}`);
          } catch (error) {
            console.error('문서 저장 오류:', error);
          } finally {
            debounceMap.delete(noteId);
          }
        }, 1000)); // 1000ms = 1초 대기
      }
    })
  ]
});

server.listen();
console.log(`Hocuspocus 협업 서버가 시작되었습니다. (포트: ${HOCUSPOCUS_PORT})`);
