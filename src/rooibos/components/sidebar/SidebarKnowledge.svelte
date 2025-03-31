<script lang="ts">
	import { getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');
	import { goto } from '$app/navigation';
	import { mobile, showSidebar, chatId, knowledge } from '$lib/stores';
	import { getKnowledgeBaseList } from '$lib/apis/knowledge';
	import { toast } from 'svelte-sonner';
	import Folder from '$lib/components/common/Folder.svelte';

	// 지식베이스 타입 정의
	interface KnowledgeBase {
		id: string;
		name: string;
		description?: string;
		created_at?: number;
		updated_at?: number;
		collection_name?: string;
		filename?: string;
		title?: string;
	}

	let knowledgeBases: KnowledgeBase[] = [];

	async function fetchKnowledgeBases() {
		try {
			knowledgeBases = await getKnowledgeBaseList(localStorage.token);
		} catch (e) {
			toast.error(`${e}`);
		}
	}

	onMount(fetchKnowledgeBases);

	// knowledge 스토어가 변경될 때마다 getKnowledgeBaseList 호출
	knowledge.subscribe(() => {
		fetchKnowledgeBases();
	});

	const handleAddClick = () => {
		chatId.set('');
		goto('/workspace/knowledge/create');
		if ($mobile) {
			showSidebar.set(false);
		}
	};

	const handleKnowledgeClick = (baseId: string) => {
		chatId.set('');
		goto(`/workspace/knowledge/${baseId}`);
		if ($mobile) {
			showSidebar.set(false);
		}
	};
	
	const goToKnowledgePage = () => {
		chatId.set('');
		goto('/workspace/knowledge');
		if ($mobile) {
			showSidebar.set(false);
		}
	};
</script>

<div on:click={goToKnowledgePage} class="cursor-pointer">
	<Folder
		className="px-2 mt-0.5"
		name={$i18n.t('Knowledge')}
		onAdd={handleAddClick}
		onAddLabel={$i18n.t('Create a knowledge base')}
	>
		{#each knowledgeBases as base}
			<button
				class="w-full flex items-center space-x-3 px-2 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900 transition text-sm text-left"
				on:click|stopPropagation={() => handleKnowledgeClick(base.id)}
			>
				<div class="flex-1 truncate text-gray-700 dark:text-gray-300">
					{base.name}
				</div>
			</button>
		{/each}
	</Folder>
</div>
