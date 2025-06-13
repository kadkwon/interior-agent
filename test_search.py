from interior_agents.agent.address_management_agent import search_addresses_by_keyword

print("=== 1234 주소 검색 테스트 ===")
result = search_addresses_by_keyword('1234')

if result.get('status') == 'success':
    addresses = result.get('addresses', [])
    print(f"검색 결과: {len(addresses)}개 주소 발견")
    
    for i, addr in enumerate(addresses, 1):
        print(f"\n{i}. 주소 정보:")
        print(f"   - 주소: {addr.get('address')}")
        print(f"   - 문서ID: {addr.get('doc_id')}")
        print(f"   - 현장번호: {addr.get('siteNumber')}")
        print(f"   - 생성일: {addr.get('createdAt')}")
        print(f"   - 완료여부: {addr.get('isCompleted')}")
        print(f"   - 유사도: {addr.get('similarity')}")
        print(f"   - 1층 비밀번호: {addr.get('firstFloorPassword')}")
        print(f"   - 유닛 비밀번호: {addr.get('unitPassword')}")
else:
    print("검색 실패:", result.get('message')) 