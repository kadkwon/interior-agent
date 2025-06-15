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

// MCP 호환: 단일 Firestore 문서 조회
exports.firestoreGetDocument = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { collectionPath, documentId } = req.body || req.query;
      
      if (!collectionPath) {
        throw new Error('collectionPath가 필요합니다.');
      }
      
      if (!documentId) {
        throw new Error('documentId가 필요합니다.');
      }
      
      const db = admin.firestore();
      const docRef = db.collection(collectionPath).doc(documentId);
      const doc = await docRef.get();
      
      if (!doc.exists) {
        res.status(404).json({
          success: false,
          message: `문서를 찾을 수 없습니다: ${collectionPath}/${documentId}`,
          data: {
            exists: false,
            path: docRef.path
          }
        });
        return;
      }
      
      res.status(200).json({
        success: true,
        data: {
          id: doc.id,
          path: doc.ref.path,
          data: doc.data(),
          exists: true,
          createTime: doc.createTime,
          updateTime: doc.updateTime
        }
      });
    } catch (error) {
      console.error('Firestore 단일 문서 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// MCP 호환: 고급 Firestore 문서 목록 조회
exports.firestoreListDocuments = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { 
        collectionPath, 
        limit = 10, 
        offset = 0,
        orderBy,
        orderDirection = 'asc',
        where,
        startAfter,
        endBefore,
        select
      } = req.body || req.query;
      
      if (!collectionPath) {
        throw new Error('collectionPath가 필요합니다.');
      }
      
      const db = admin.firestore();
      let query = db.collection(collectionPath);
      
      // Where 조건 추가 (배열 형태: [field, operator, value])
      if (where && Array.isArray(where)) {
        for (const condition of where) {
          if (Array.isArray(condition) && condition.length === 3) {
            const [field, operator, value] = condition;
            query = query.where(field, operator, value);
          }
        }
      }
      
      // 정렬 추가
      if (orderBy) {
        const direction = orderDirection.toLowerCase() === 'desc' ? 'desc' : 'asc';
        query = query.orderBy(orderBy, direction);
      }
      
      // 페이지네이션: startAfter (커서 기반)
      if (startAfter) {
        // startAfter는 문서 ID 또는 정렬 필드 값
        if (orderBy) {
          query = query.startAfter(startAfter);
        } else {
          // 문서 ID 기반 페이지네이션
          const startDoc = await db.collection(collectionPath).doc(startAfter).get();
          if (startDoc.exists) {
            query = query.startAfter(startDoc);
          }
        }
      }
      
      // 페이지네이션: endBefore (커서 기반)
      if (endBefore) {
        if (orderBy) {
          query = query.endBefore(endBefore);
        } else {
          const endDoc = await db.collection(collectionPath).doc(endBefore).get();
          if (endDoc.exists) {
            query = query.endBefore(endDoc);
          }
        }
      }
      
      // 오프셋 처리 (비효율적이지만 호환성을 위해 지원)
      if (offset > 0 && !startAfter) {
        query = query.offset(offset);
      }
      
      // 제한 추가
      query = query.limit(Math.min(limit, 1000)); // 최대 1000개 제한
      
      // 특정 필드만 선택 (select)
      if (select && Array.isArray(select) && select.length > 0) {
        query = query.select(...select);
      }
      
      const snapshot = await query.get();
      const documents = [];
      
      snapshot.forEach(doc => {
        documents.push({
          id: doc.id,
          path: doc.ref.path,
          data: doc.data(),
          createTime: doc.createTime,
          updateTime: doc.updateTime
        });
      });
      
      // 다음 페이지 커서 정보
      let nextPageToken = null;
      if (documents.length === limit && documents.length > 0) {
        const lastDoc = documents[documents.length - 1];
        nextPageToken = orderBy ? lastDoc.data[orderBy] : lastDoc.id;
      }
      
      res.status(200).json({
        success: true,
        data: {
          documents: documents,
          count: documents.length,
          hasMore: documents.length === limit,
          nextPageToken: nextPageToken,
          query: {
            collectionPath,
            limit,
            offset,
            orderBy,
            orderDirection,
            where: where || [],
            select: select || []
          }
        }
      });
    } catch (error) {
      console.error('Firestore 문서 목록 조회 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firestore 문서 조회 (기존 - 여러 문서 경로)
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

// Firestore 문서 생성
exports.firestoreAddDocument = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { collectionPath, data, documentId } = req.body;
      
      if (!collectionPath) {
        throw new Error('collectionPath가 필요합니다.');
      }
      
      if (!data || typeof data !== 'object') {
        throw new Error('data 객체가 필요합니다.');
      }
      
      const db = admin.firestore();
      let docRef;
      
      // 문서 ID가 지정된 경우
      if (documentId) {
        docRef = db.collection(collectionPath).doc(documentId);
        await docRef.set(data);
      } else {
        // 자동 ID 생성
        docRef = await db.collection(collectionPath).add(data);
      }
      
      res.status(201).json({
        success: true,
        data: {
          id: docRef.id,
          path: docRef.path,
          data: data
        }
      });
    } catch (error) {
      console.error('Firestore 문서 생성 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firestore 문서 업데이트
exports.firestoreUpdateDocument = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { collectionPath, documentId, data, merge = true } = req.body;
      
      if (!collectionPath) {
        throw new Error('collectionPath가 필요합니다.');
      }
      
      if (!documentId) {
        throw new Error('documentId가 필요합니다.');
      }
      
      if (!data || typeof data !== 'object') {
        throw new Error('data 객체가 필요합니다.');
      }
      
      const db = admin.firestore();
      const docRef = db.collection(collectionPath).doc(documentId);
      
      // 문서 존재 확인
      const doc = await docRef.get();
      if (!doc.exists) {
        throw new Error(`문서를 찾을 수 없습니다: ${collectionPath}/${documentId}`);
      }
      
      // 업데이트 실행
      if (merge) {
        await docRef.update(data);
      } else {
        await docRef.set(data);
      }
      
      // 업데이트된 데이터 조회
      const updatedDoc = await docRef.get();
      
      res.status(200).json({
        success: true,
        data: {
          id: updatedDoc.id,
          path: updatedDoc.ref.path,
          data: updatedDoc.data()
        }
      });
    } catch (error) {
      console.error('Firestore 문서 업데이트 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firestore 문서 삭제
exports.firestoreDeleteDocument = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      // 기존 클라이언트 호환성을 위해 documentPath도 지원
      let { collectionPath, documentId, documentPath } = req.body || req.query;
      
      // documentPath가 제공된 경우 분리 처리
      if (documentPath && !collectionPath && !documentId) {
        const pathParts = documentPath.split('/');
        if (pathParts.length === 2) {
          collectionPath = pathParts[0];
          documentId = pathParts[1];
        } else {
          throw new Error('documentPath 형식이 올바르지 않습니다. collection/document 형식이어야 합니다.');
        }
      }
      
      if (!collectionPath) {
        throw new Error('collectionPath가 필요합니다.');
      }
      
      if (!documentId) {
        throw new Error('documentId가 필요합니다.');
      }
      
      const db = admin.firestore();
      const docRef = db.collection(collectionPath).doc(documentId);
      
      // 문서 존재 확인
      const doc = await docRef.get();
      if (!doc.exists) {
        throw new Error(`문서를 찾을 수 없습니다: ${collectionPath}/${documentId}`);
      }
      
      // 삭제 전 데이터 백업
      const deletedData = doc.data();
      
      // 문서 삭제
      await docRef.delete();
      
      res.status(200).json({
        success: true,
        data: {
          id: documentId,
          path: docRef.path,
          deletedData: deletedData,
          message: '문서가 성공적으로 삭제되었습니다.'
        }
      });
    } catch (error) {
      console.error('Firestore 문서 삭제 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firestore 문서 설정 (덮어쓰기)
exports.firestoreSetDocument = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { collectionPath, documentId, data } = req.body;
      
      if (!collectionPath) {
        throw new Error('collectionPath가 필요합니다.');
      }
      
      if (!documentId) {
        throw new Error('documentId가 필요합니다.');
      }
      
      if (!data || typeof data !== 'object') {
        throw new Error('data 객체가 필요합니다.');
      }
      
      const db = admin.firestore();
      const docRef = db.collection(collectionPath).doc(documentId);
      
      // 문서 완전 덮어쓰기
      await docRef.set(data);
      
      res.status(200).json({
        success: true,
        data: {
          id: docRef.id,
          path: docRef.path,
          data: data
        }
      });
    } catch (error) {
      console.error('Firestore 문서 설정 오류:', error);
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  });
});

// Firestore 주소 검색 (description 필드 기준)
exports.firestoreSearchByDescription = functions.https.onRequest((req, res) => {
  return cors(req, res, async () => {
    try {
      const { searchTerm, collectionPath = 'addressesJson', limit = 50, exactMatch = false } = req.body || req.query;
      
      if (!searchTerm) {
        throw new Error('searchTerm이 필요합니다.');
      }
      
      const db = admin.firestore();
      const collection = db.collection(collectionPath);
      
      let query;
      
      if (exactMatch) {
        // 정확한 매칭
        query = collection.where('description', '==', searchTerm).limit(limit);
      } else {
        // 부분 매칭을 위해 모든 문서를 가져와서 필터링
        query = collection.limit(1000); // 최대 1000개 문서 검색
      }
      
      const snapshot = await query.get();
      const results = [];
      
      snapshot.forEach(doc => {
        const data = doc.data();
        const description = data.description || '';
        
        if (exactMatch) {
          // 정확한 매칭인 경우 모든 결과 포함
          results.push({
            id: doc.id,
            path: doc.ref.path,
            description: description,
            dataJson: data.dataJson || '{}',
            relevanceScore: 1.0
          });
        } else {
          // 부분 매칭 확인
          const searchTermLower = searchTerm.toLowerCase();
          const descriptionLower = description.toLowerCase();
          
          if (descriptionLower.includes(searchTermLower)) {
            // 단순한 관련성 점수 계산
            const exactPos = descriptionLower.indexOf(searchTermLower);
            const relevanceScore = exactPos === 0 ? 1.0 : 
                                 exactPos > 0 ? 0.8 : 
                                 descriptionLower.includes(searchTermLower) ? 0.6 : 0.0;
            
            results.push({
              id: doc.id,
              path: doc.ref.path,
              description: description,
              dataJson: data.dataJson || '{}',
              relevanceScore: relevanceScore
            });
          }
        }
      });
      
      // 관련성 점수로 정렬
      results.sort((a, b) => b.relevanceScore - a.relevanceScore);
      
      // 결과 수 제한
      const limitedResults = results.slice(0, limit);
      
      res.status(200).json({
        success: true,
        data: {
          searchTerm: searchTerm,
          exactMatch: exactMatch,
          totalFound: limitedResults.length,
          results: limitedResults
        }
      });
    } catch (error) {
      console.error('Firestore 주소 검색 오류:', error);
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
            { name: 'firebaseGetProject', description: 'Firebase 프로젝트 정보 조회' },
            { name: 'firebaseGetSdkConfig', description: 'Firebase SDK 설정 조회' }
          ]
        },
        {
          category: 'Authentication',
          endpoints: [
            { name: 'authGetUser', description: '사용자 정보 조회' },
            { name: 'authListUsers', description: '사용자 목록 조회' }
          ]
        },
        {
          category: 'Firestore',
          endpoints: [
            { name: 'firestoreGetDocument', description: 'MCP 호환: 단일 Firestore 문서 조회' },
            { name: 'firestoreListDocuments', description: 'MCP 호환: 고급 Firestore 문서 목록 조회 (필터링/정렬/페이지네이션)' },
            { name: 'firestoreGetDocuments', description: 'Firestore 문서 조회 (여러 경로)' },
            { name: 'firestoreListCollections', description: 'Firestore 컬렉션 목록 조회' },
            { name: 'firestoreQueryCollection', description: 'Firestore 컬렉션 쿼리' },
            { name: 'firestoreAddDocument', description: 'Firestore 문서 생성' },
            { name: 'firestoreUpdateDocument', description: 'Firestore 문서 업데이트' },
            { name: 'firestoreDeleteDocument', description: 'Firestore 문서 삭제' },
            { name: 'firestoreSetDocument', description: 'Firestore 문서 설정 (덮어쓰기)' },
            { name: 'firestoreSearchByDescription', description: 'Firestore 주소 검색 (description 필드 기준)' }
          ]
        },
        {
          category: 'Storage',
          endpoints: [
            { name: 'storageGetDownloadUrl', description: 'Storage 파일 다운로드 URL 조회' },
            { name: 'storageListFiles', description: 'Storage 파일 목록 조회' }
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