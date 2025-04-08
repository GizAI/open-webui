<script>
	import MyCompanyInfo from '$rooibos/components/mycompany/MyCompanyInfo.svelte';
	import { page } from '$app/stores';
	
	// URL 쿼리 파라미터에서 type 확인
	$: isPrivateCompany = $page.url.searchParams.get('type') === 'private';
	// URL 쿼리 파라미터에서 entity_type 확인
	$: entityType = $page.url.searchParams.get('entity_type') || 'company';
</script>

<MyCompanyInfo {isPrivateCompany} {entityType} />
