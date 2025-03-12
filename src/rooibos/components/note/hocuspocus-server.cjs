const { Server } = require('@hocuspocus/server');
const { Database } = require('@hocuspocus/extension-database');
const { Logger } = require('@hocuspocus/extension-logger');
const { Redis } = require('@hocuspocus/extension-redis');
const axios = require('axios');
const Y = require('yjs'); // Yjs 임포트

const HOCUSPOCUS_HOST = '0.0.0.0';
const HOCUSPOCUS_PORT = 8444;


const debounceMap = new Map();

const server = Server.configure({
  address: HOCUSPOCUS_HOST,
  port: HOCUSPOCUS_PORT,
  
  async onConnect(data) {
    const { request, requestHeaders, documentName } = data;
    console.log(`사용자가 문서에 연결됨: ${documentName}`);
    
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
   
  ]
});

server.listen();
console.log(`Hocuspocus 협업 서버가 시작되었습니다. (포트: ${HOCUSPOCUS_PORT})`);
