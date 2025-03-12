<script>
	import KnowledgeBase from '$lib/components/workspace/Knowledge/KnowledgeBase.svelte';
	import { page } from '$app/stores';
</script>

{#key $page.params.id}
	<KnowledgeBase />
{/key}
