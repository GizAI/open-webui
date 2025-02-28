// server.js (또는 실행 파일)
const { Server } = require('@hocuspocus/server');
const { Database } = require('@hocuspocus/extension-database');
const { Logger } = require('@hocuspocus/extension-logger');
const { Redis } = require('@hocuspocus/extension-redis');
const axios = require('axios');

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

function getRandomColor() {
  const colors = [
    '#5D8AA8', '#E32636', '#FFBF00', '#9966CC', '#7CB9E8', 
    '#B2BEB5', '#87A96B', '#FF9966', '#007FFF', '#89CFF0'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

const server = Server.configure({
  address: HOCUSPOCUS_HOST,
  port: HOCUSPOCUS_PORT,
  
  async onConnect(data) {
    const { request, requestHeaders, documentName } = data;
    console.log(`사용자가 문서에 연결됨: ${documentName}`);
    
    try {
      // 토큰 검증 및 사용자 정보 가져오기 (필요 시 주석 해제)
      // const token = requestHeaders.authorization?.replace('Bearer ', '');
      // if (!token) {
      //   throw new Error('인증 토큰이 없습니다');
      // }
      // const response = await axios.get(`${API_BASE_URL}/users/me`, {
      //   headers: { Authorization: `Bearer ${token}` }
      // });
      // const user = {
      //   id: response.data.id,
      //   name: response.data.name,
      //   color: response.data.color || getRandomColor(),
      //   avatar: response.data.avatar
      // };
      // request.user = user;
      
      // 문서 접근 권한 확인 (필요 시 주석 해제)
      // const noteId = documentName.split(':')[1];
      // const permissionResponse = await axios.get(`${API_BASE_URL}/notes/${noteId}`, {
      //   headers: { Authorization: `Bearer ${token}` }
      // });
      // if (!permissionResponse.data.canEdit) {
      //   throw new Error('이 문서를 편집할 권한이 없습니다');
      // }
      
      // 활성 사용자 목록에 추가 (원하는 경우)
      // const activeUsers = data.instance.getMap('activeUsers');
      // activeUsers.set(user.id, user);
      
      return true;
    } catch (error) {
      console.error('연결 오류:', error);
      return false;
    }
  },
  
  // 필요 시 onDisconnect 핸들러 구현
  // async onDisconnect(data) {
  //   const { request, instance } = data;
  //   const user = request.user;
  //   if (user) {
  //     const activeUsers = instance.getMap('activeUsers');
  //     activeUsers.delete(user.id);
  //     console.log(`사용자 연결 해제: ${user.name}`);
  //   }
  // },
  
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
      // 문서 가져오기
      fetch: async (data) => {
    //     try {
    //       const noteId = data.documentName.split(':')[1];
    //       if (!noteId) return null;
          
    //       const token = data.requestHeaders.authorization?.replace('Bearer ', '');
    //       const response = await axios.get(`${API_BASE_URL}/rooibos/notes/${noteId}`, {
    //         headers: token ? { Authorization: `Bearer ${token}` } : {},
    //         responseType: 'arraybuffer'
    //       });
          
    //       return response.data.note;
    //     } catch (error) {
    //       console.error('문서 가져오기 오류:', error);
    //       return null;
    //     }
    //   },
      
      // 문서 저장하기
      store: async (data) => {
        try {
          const noteId = data.documentName.split(':')[1];
          if (!noteId) return;
          
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

server.listen();
console.log(`Hocuspocus 협업 서버가 시작되었습니다. (포트: ${HOCUSPOCUS_PORT})`);
