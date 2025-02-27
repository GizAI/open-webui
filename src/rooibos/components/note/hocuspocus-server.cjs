// Hocuspocus 서버 실행 파일
// CommonJS 환경에서 TypeScript 파일을 직접 import할 수 없으므로 
// 먼저 TypeScript 파일을 컴파일한 후 사용해야 합니다.

// 컴파일된 JavaScript 파일을 사용
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
  
  // 연결 이벤트 핸들러
  async onConnect(data) {
    const { request, requestHeaders, documentName } = data;
    console.log(`사용자가 문서에 연결됨: ${documentName}`);
    
    try {
      // 토큰 검증 및 사용자 정보 가져오기
    //   const token = requestHeaders.authorization?.replace('Bearer ', '');
    //   if (!token) {
    //     throw new Error('인증 토큰이 없습니다');
    //   }
      
      // 사용자 정보 가져오기 (백엔드 API 호출)
    //   const response = await axios.get(`${API_BASE_URL}/users/me`, {
    //     headers: { Authorization: `Bearer ${token}` }
    //   });
      
    //   const user = {
    //     id: response.data.id,
    //     name: response.data.name,
    //     color: response.data.color || getRandomColor(),
    //     avatar: response.data.avatar
    //   };
      
    //   // 사용자 정보를 요청 객체에 저장
    //   request.user = user;
      
      // 문서 접근 권한 확인
    //   const noteId = documentName.split(':')[1];
    //   const permissionResponse = await axios.get(`${API_BASE_URL}/notes/${noteId}`, {
    //     headers: { Authorization: `Bearer ${token}` }
    //   });
      
    //   if (!permissionResponse.data.canEdit) {
    //     throw new Error('이 문서를 편집할 권한이 없습니다');
    //   }
      
      // 현재 접속 중인 사용자 목록에 추가
    //   const activeUsers = data.instance.getMap('activeUsers');
    //   activeUsers.set(user.id, user);
      
      return true;
    } catch (error) {
      console.error('연결 오류:', error);
      return false;
    }
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
      // 문서 가져오기
      fetch: async (data) => {
        try {
          // 문서 ID 추출 (형식: note:123)
        //   const noteId = data.documentName.split(':')[1];
        //   if (!noteId) return null;
          
          // 백엔드에서 문서 내용 가져오기
        //   const token = data.requestHeaders.authorization?.replace('Bearer ', '');
        //   const response = await axios.get(`${API_BASE_URL}/rooibos/notes/${noteId}`, {
        //     headers: token ? { Authorization: `Bearer ${token}` } : {},
        //     responseType: 'arraybuffer'
        //   });
        let error;
        console.log("!!!!!!!!!!!!!")  
        const res = await fetch(
            `${API_BASE_URL}/rooibos/notes/7c15ef4f-524e-413e-a2fa-ed162422a263`,
            {
              method: 'GET',
              headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json'
              },
            }
          )
            .then(async (res) => {
                debugger
              if (!res.ok) throw await res.json();
              const data = await res.json();
        console.log("================")  
        console.log(data)
              return data.note;
            })
            .catch((err) => {
              error = err.detail;
              return null;
            });
        
          if (error) {
            throw error;
          }
        
          return res;
          
          
        } catch (error) {
          console.error('문서 가져오기 오류:', error);
          return null;
        }
      },
      
      // 문서 저장하기
      store: async (data) => {
        try {
          // 문서 ID 추출
          const noteId = data.documentName.split(':')[1];
          if (!noteId) return;
          
          // 백엔드에 문서 내용 저장
          const token = data.requestHeaders.authorization?.replace('Bearer ', '');
          await axios.post(`${API_BASE_URL}/rooibos/notes/update/`, data.state, {
            headers: {
              Authorization: token ? `Bearer ${token}` : '',
              'Content-Type': 'application/octet-stream'
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