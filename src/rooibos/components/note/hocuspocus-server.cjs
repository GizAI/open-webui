// Hocuspocus 서버 실행 파일
// CommonJS 환경에서 TypeScript 파일을 직접 import할 수 없으므로 
// 먼저 TypeScript 파일을 컴파일한 후 사용해야 합니다.

// ES 모듈 import 구문을 CommonJS require로 변경
const Y = require('yjs');
const { Server } = require('@hocuspocus/server');
const { Database } = require('@hocuspocus/extension-database');
const { Logger } = require('@hocuspocus/extension-logger');
const { Redis } = require('@hocuspocus/extension-redis');
const axios = require('axios');

// 서버 설정 상수
const HOCUSPOCUS_HOST = '0.0.0.0';
const HOCUSPOCUS_PORT = 1234;
const API_BASE_URL = 'http://localhost:8080/api/v1'; // 백엔드 API 주소

// Redis 설정 (필요한 경우)
const redisConfig = process.env.REDIS_URL ? {
  host: new URL(process.env.REDIS_URL).hostname,
  port: Number(new URL(process.env.REDIS_URL).port) || 6379,
  password: new URL(process.env.REDIS_URL).password || undefined
} : null;

// 랜덤 색상 생성 함수
function getRandomColor() {
  const colors = [
    '#5D8AA8', '#E32636', '#FFBF00', '#9966CC', '#7CB9E8', 
    '#B2BEB5', '#87A96B', '#FF9966', '#007FFF', '#89CFF0'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

// Hocuspocus 서버 설정
const server = Server.configure({
  address: HOCUSPOCUS_HOST,
  port: HOCUSPOCUS_PORT,
  timeout: 30000, // 타임아웃 증가
  debounce: 2000, // 디바운스 시간 증가
  
  // 연결 이벤트 핸들러
  async onConnect(data) {
    const { request, requestHeaders, documentName } = data;
    console.log(`사용자가 문서에 연결됨: ${documentName}`, {
      headers: requestHeaders,
      ip: request.socket.remoteAddress
    });
    
    return true; // 항상 연결 허용 (디버깅용)
  },
  
  // 문서 로드 이벤트
  async onLoadDocument(data) {
    console.log(`문서 로드 요청: ${data.documentName}`, {
      context: data.context,
      requestHeaders: data.requestHeaders
    });
    
    // 문서 로드 시 추가 디버깅 정보
    try {
      const noteId = data.documentName.split(':')[1];
      if (noteId) {
        console.log(`문서 ID: ${noteId} 로드 중`);
      }
    } catch (error) {
      console.error('문서 ID 파싱 오류:', error);
    }
    
    return true;
  },
  
  // 연결 해제 이벤트 핸들러
  async onDisconnect(data) {
    const { request, instance } = data;
    const user = request.user;
    
    if (user) {
      // 접속 중인 사용자 목록에서 제거
      const activeUsers = instance.getMap('activeUsers');
      activeUsers.delete(user.id);
      console.log(`사용자 연결 해제: ${user.name}`);
    }
  },
  
  extensions: [
    // 로깅 확장 기능
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
    
    // Redis 확장 기능 (필요한 경우)
    ...(redisConfig ? [
      new Redis({
        host: redisConfig.host,
        port: redisConfig.port,
        options: {
          password: redisConfig.password
        }
      })
    ] : []),
    
    // 데이터베이스 확장 기능
    new Database({
        fetch: async (data) => {
            const noteId = data.documentName.split(':')[1];
            if (!noteId) {
              console.error('Invalid document name:', data.documentName);
              const emptyDoc = new Y.Doc();
              emptyDoc.getText('prosemirror').insert(0, '');
              return emptyDoc;
            }
          
            try {
              const res = await fetch(`${API_BASE_URL}/rooibos/notes/${noteId}`, {
                method: 'GET',
                headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
              });
          
              if (!res.ok) {
                console.error(`Error fetching note ${noteId}:`, await res.text());
                const emptyDoc = new Y.Doc();
                emptyDoc.getText('prosemirror').insert(0, '');
                return emptyDoc;
              }
          
              const responseData = await res.json();
              const noteData = responseData.note;
          
              if (!noteData) {
                console.error("Invalid response format, missing note data");
                const emptyDoc = new Y.Doc();
                emptyDoc.getText('prosemirror').insert(0, '');
                return emptyDoc;
              }
          
              // Yjs 문서 생성 후 노트 콘텐츠가 있다면 주입
              const yDoc = new Y.Doc();
              const yText = yDoc.getText('prosemirror');
              if (noteData.content) {
                yText.insert(0, noteData.content);
                console.log("Initialized Y.Doc with note content:", noteData.content);
              } else {
                yText.insert(0, '<p></p>');
              }
              return yDoc;
            } catch (error) {
              console.error(`Error in fetch handler for note ${noteId}:`, error);
              const emptyDoc = new Y.Doc();
              emptyDoc.getText('prosemirror').insert(0, '');
              return emptyDoc;
            }
          },
          

      // 문서 저장하기
      store: async (data) => {
        try {
          // 문서 ID 추출
          const noteId = data.documentName.split(':')[1];
          if (!noteId) return;
          
          console.log(`Storing document: ${noteId}`);
          
          // 백엔드에 문서 내용 저장
          const token = data.requestHeaders.authorization?.replace('Bearer ', '');
          
          // 요청 데이터 구조 확인
          const requestData = {
            id: noteId,
            state: Array.from(data.state), // Uint8Array를 일반 배열로 변환
          };
          
          console.log("Sending update request with data:", requestData);
          
          await axios.post(`${API_BASE_URL}/rooibos/notes/update/`, requestData, {
            headers: {
              Authorization: token ? `Bearer ${token}` : '',
              'Content-Type': 'application/json'
            }
          });
          
          console.log(`문서 저장 완료: ${noteId}`);
        } catch (error) {
          console.error('문서 저장 오류:', error);
        }
      }
    })
  ]
});

// 서버 시작
server.listen();

console.log('Hocuspocus 협업 서버가 시작되었습니다. (포트: 1234)'); 