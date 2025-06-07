const functions = require('firebase-functions');
const admin = require('firebase-admin');
const cors = require('cors')({ 
  origin: true,
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type'],
  credentials: true 
});

// Firebase Admin 초기화
if (!admin.apps.length) {
  admin.initializeApp();
}

// =================
// 🔥 CORE APIs
// =================

// Firebase 프로젝트 정보 조회
exports.firebaseGetProject = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const app = admin.app();
      const projectId = app.options.projectId;
      
      res.status(200).json({
        success: true,
        data: {
          projectId: projectId,
          displayName: projectId,
          region: 'asia-northeast1'
        }
      });
    } catch (error) {
      console.error('프로젝트 정보 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firebase SDK 설정 조회
exports.firebaseGetSdkConfig = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const app = admin.app();
      const projectId = app.options.projectId;
      
      const config = {
        projectId: projectId,
        authDomain: `${projectId}.firebaseapp.com`,
        storageBucket: `${projectId}.appspot.com`,
        region: 'asia-northeast1'
      };
      
      res.status(200).json({
        success: true,
        data: config
      });
    } catch (error) {
      console.error('SDK 설정 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// =================
// 👤 AUTH APIs
// =================

// 사용자 정보 조회
exports.authGetUser = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { uid, email, phoneNumber } = req.body || req.query;
      
      let userRecord;
      if (uid) {
        userRecord = await admin.auth().getUser(uid);
      } else if (email) {
        userRecord = await admin.auth().getUserByEmail(email);
      } else if (phoneNumber) {
        userRecord = await admin.auth().getUserByPhoneNumber(phoneNumber);
      } else {
        throw new Error('uid, email, 또는 phoneNumber 중 하나는 필수입니다.');
      }
      
      res.status(200).json({
        success: true,
        data: {
          uid: userRecord.uid,
          email: userRecord.email,
          displayName: userRecord.displayName,
          photoURL: userRecord.photoURL,
          disabled: userRecord.disabled,
          emailVerified: userRecord.emailVerified,
          createdAt: userRecord.metadata.creationTime,
          lastSignIn: userRecord.metadata.lastSignInTime
        }
      });
    } catch (error) {
      console.error('사용자 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// 사용자 목록 조회
exports.authListUsers = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { maxResults = 1000, pageToken } = req.body || req.query;
      
      const listUsersResult = await admin.auth().listUsers(maxResults, pageToken);
      
      const users = listUsersResult.users.map(user => ({
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        disabled: user.disabled,
        emailVerified: user.emailVerified,
        createdAt: user.metadata.creationTime
      }));
      
      res.status(200).json({
        success: true,
        data: {
          users: users,
          pageToken: listUsersResult.pageToken
        }
      });
    } catch (error) {
      console.error('사용자 목록 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// =================
// 🗄️ FIRESTORE APIs
// =================

// Firestore 문서 조회
exports.firestoreGetDocuments = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { paths } = req.body || req.query;
      
      if (!paths || !Array.isArray(paths)) {
        throw new Error('paths 배열이 필요합니다.');
      }
      
      const db = admin.firestore();
      const results = [];
      
      for (const path of paths) {
        try {
          const doc = await db.doc(path).get();
          if (doc.exists) {
            results.push({
              path: path,
              data: doc.data(),
              exists: true
            });
          } else {
            results.push({
              path: path,
              data: null,
              exists: false
            });
          }
        } catch (error) {
          results.push({
            path: path,
            error: error.message,
            exists: false
          });
        }
      }
      
      res.status(200).json({
        success: true,
        data: results
      });
    } catch (error) {
      console.error('Firestore 문서 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firestore 컬렉션 조회
exports.firestoreListCollections = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { parentPath = '' } = req.body || req.query;
      
      const db = admin.firestore();
      let ref;
      
      if (parentPath) {
        ref = db.doc(parentPath);
      } else {
        ref = db;
      }
      
      const collections = await ref.listCollections();
      const collectionIds = collections.map(col => col.id);
      
      res.status(200).json({
        success: true,
        data: {
          collections: collectionIds,
          parentPath: parentPath
        }
      });
    } catch (error) {
      console.error('Firestore 컬렉션 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firestore 컬렉션 쿼리
exports.firestoreQueryCollection = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { collectionPath, limit = 10, orderBy, where } = req.body || req.query;
      
      if (!collectionPath) {
        throw new Error('collectionPath가 필요합니다.');
      }
      
      const db = admin.firestore();
      let query = db.collection(collectionPath);
      
      // Where 조건 추가
      if (where && Array.isArray(where)) {
        for (const condition of where) {
          const [field, operator, value] = condition;
          query = query.where(field, operator, value);
        }
      }
      
      // 정렬 추가
      if (orderBy) {
        const [field, direction = 'asc'] = Array.isArray(orderBy) ? orderBy : [orderBy];
        query = query.orderBy(field, direction);
      }
      
      // 제한 추가
      query = query.limit(limit);
      
      const snapshot = await query.get();
      const documents = [];
      
      snapshot.forEach(doc => {
        documents.push({
          id: doc.id,
          path: doc.ref.path,
          data: doc.data()
        });
      });
      
      res.status(200).json({
        success: true,
        data: {
          documents: documents,
          count: documents.length
        }
      });
    } catch (error) {
      console.error('Firestore 컬렉션 쿼리 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// =================
// 📁 STORAGE APIs
// =================

// Storage 파일 다운로드 URL 조회
exports.storageGetDownloadUrl = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { filePath, bucketName } = req.body || req.query;
      
      if (!filePath) {
        throw new Error('filePath가 필요합니다.');
      }
      
      const bucket = bucketName ? admin.storage().bucket(bucketName) : admin.storage().bucket();
      const file = bucket.file(filePath);
      
      // 파일 존재 확인
      const [exists] = await file.exists();
      if (!exists) {
        throw new Error(`파일을 찾을 수 없습니다: ${filePath}`);
      }
      
      // 서명된 URL 생성 (1시간 유효)
      const [url] = await file.getSignedUrl({
        action: 'read',
        expires: Date.now() + 60 * 60 * 1000 // 1시간
      });
      
      res.status(200).json({
        success: true,
        data: {
          downloadUrl: url,
          filePath: filePath,
          bucket: bucket.name
        }
      });
    } catch (error) {
      console.error('Storage 다운로드 URL 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Storage 파일 목록 조회
exports.storageListFiles = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { prefix = '', maxResults = 100, bucketName } = req.body || req.query;
      
      const bucket = bucketName ? admin.storage().bucket(bucketName) : admin.storage().bucket();
      
      const [files] = await bucket.getFiles({
        prefix: prefix,
        maxResults: maxResults
      });
      
      const fileList = files.map(file => ({
        name: file.name,
        size: file.metadata.size,
        contentType: file.metadata.contentType,
        created: file.metadata.timeCreated,
        updated: file.metadata.updated
      }));
      
      res.status(200).json({
        success: true,
        data: {
          files: fileList,
          count: fileList.length,
          bucket: bucket.name
        }
      });
    } catch (error) {
      console.error('Storage 파일 목록 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// =================
// 📋 MCP API 목록 조회
// =================

exports.mcpListApis = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const apis = [
        {
          category: 'Core',
          endpoints: [
            { name: 'firebaseGetProject', description: 'Firebase 프로젝트 정보 조회' }
          ]
        },
        {
          category: 'Firestore',
          endpoints: [
            { name: 'firestoreGetDocuments', description: 'Firestore 문서 조회' }
          ]
        }
      ];
      
      res.status(200).json({
        success: true,
        data: {
          totalCategories: apis.length,
          totalEndpoints: apis.reduce((sum, cat) => sum + cat.endpoints.length, 0),
          apis: apis,
          baseUrl: `https://us-central1-${admin.app().options.projectId}.cloudfunctions.net`
        }
      });
    } catch (error) {
      console.error('API 목록 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
}); 