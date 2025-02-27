// hocuspocus.ts
import { Server, type Configuration } from '@hocuspocus/server';
import { Database } from '@hocuspocus/extension-database';
import { Logger } from '@hocuspocus/extension-logger';
import { Redis } from '@hocuspocus/extension-redis';
import axios from 'axios';
import 'reflect-metadata';
import { IncomingMessage } from 'http';

const HOCUSPOCUS_HOST = '0.0.0.0';
const HOCUSPOCUS_PORT = 1234;
const WEBUI_API_BASE_URL = 'http://localhost:8080///api/v1'; // 백엔드 API 주소

interface FetchParams {
  documentName: string;
  requestHeaders: Record<string, any>;
}

interface storePayload {
  documentName: string;
  state: {
    slice(...args: any[]): {
      buffer: ArrayBuffer;
    };
  };
  requestHeaders: Record<string, any>;
}

interface StoreParams {
  documentName: string;
  state: {
    slice(...args: any[]): {
      buffer: ArrayBuffer;
    };
  };
  requestHeaders: Record<string, any>;
}

interface User {
  id: string;
  name: string;
  color: string;
  avatar?: string;
}

declare module 'http' {
  interface IncomingMessage {
    user?: User;
  }
}

declare module '@hocuspocus/server' {
  interface Hocuspocus {
    getMap(name: string): any;
  }
}

declare module '@hocuspocus/server' {
  interface onDisconnectPayload {
    request: IncomingMessage;
  }
}

const redisConfig = process.env.REDIS_URL ? {
  host: new URL(process.env.REDIS_URL).hostname,
  port: Number(new URL(process.env.REDIS_URL).port) || 6379,
  password: new URL(process.env.REDIS_URL).password || undefined
} : null;

const serverConfig: Partial<Configuration> = {
  address: HOCUSPOCUS_HOST,
  port: HOCUSPOCUS_PORT,
  
  async onConnect(data) {
    const { request, requestHeaders, documentName } = data;
    console.log(`사용자가 문서에 연결됨: ${documentName}`);
    
    try {
      const token = requestHeaders.authorization?.replace('Bearer ', '');
      if (!token) {
        throw new Error('인증 토큰이 없습니다');
      }
      
      const response = await axios.get(`${WEBUI_API_BASE_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const user: User = {
        id: response.data.id,
        name: response.data.name,
        color: response.data.color || getRandomColor(),
        avatar: response.data.avatar
      };
      
      request.user = user;
      
      const noteId = documentName.split(':')[1];
    //   const permissionResponse = await axios.get(`${API_BASE_URL}/notes/${noteId}/permission`, {
    //     headers: { Authorization: `Bearer ${token}` }
    //   });
      
    //   if (!permissionResponse.data.canEdit) {
    //     throw new Error('이 문서를 편집할 권한이 없습니다');
    //   }
      
      const activeUsers = data.instance.getMap('activeUsers');
      activeUsers.set(user.id, user);
      
      return true;
    } catch (error) {
      console.error('연결 오류:', error);
      return false;
    }
  },
  
  async onDisconnect(data) {
    const { request, instance } = data;
    const user = request.user;
    
    if (user) {
      const activeUsers = instance.getMap('activeUsers');
      activeUsers.delete(user.id);
      console.log(`사용자 연결 해제: ${user.name}`);
    }
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
    
    ...(redisConfig ? [
      new Redis({
        host: redisConfig.host,
        port: redisConfig.port,
        options: { password: redisConfig.password }
      })
    ] : []),
    
    new Database({
      fetch: async ({ documentName, requestHeaders }: FetchParams) => {
        try {
          const noteId = documentName.split(':')[1];
          if (!noteId) return null;
          
          const token = requestHeaders.authorization?.replace('Bearer ', '');
          const response = await axios.get(`${WEBUI_API_BASE_URL}/rooibos/notes/${noteId}`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            responseType: 'arraybuffer'
          });
          
          return response.data?.length ? response.data : null;
        } catch (error) {
          console.error('문서 가져오기 오류:', error);
          return null;
        }
      },
      
      store: async (data: storePayload) => {
        try {
          const noteId = data.documentName.split(':')[1];
          if (!noteId) return;
          
          const token = data.requestHeaders.authorization?.replace('Bearer ', '');
          await axios.post(`${WEBUI_API_BASE_URL}/rooibos/notes/${noteId}`, data.state.slice(0).buffer, {
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
};

const serverConfigWithCors = {
  ...serverConfig,
  cors: {
    allowedOrigins: ['http://localhost:3000', 'http://localhost:5000', '*'],
    allowedHeaders: ['Authorization', 'Content-Type'],
    credentials: true
  }
} as any;

function getRandomColor(): string {
  const colors = [
    '#5D8AA8', '#E32636', '#FFBF00', '#9966CC', '#7CB9E8', 
    '#B2BEB5', '#87A96B', '#FF9966', '#007FFF', '#89CFF0'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

const server = Server.configure(serverConfigWithCors);
server.listen();

export default server;
