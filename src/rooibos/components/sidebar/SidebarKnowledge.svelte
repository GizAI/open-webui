<script lang="ts">
	import { goto } from '$app/navigation';
	import { mobile, showSidebar, chatId, knowledge } from '$lib/stores';
	import { getKnowledgeBases } from '$lib/apis/knowledge';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Folder from '$lib/components/common/Folder.svelte';

	// 지식베이스 타입 정의
	interface KnowledgeBase {
		id: string;
		name: string;
		description?: string;
		created_at?: number;
		updated_at?: number;
	}

	let knowledgeBases: any[] = [];

	onMount(async () => {
		try {
			const bases = await getKnowledgeBases(localStorage.token);
			knowledge.set(bases);
		} catch (e) {
			toast.error(`${e}`);
		}
	});

	$: knowledgeBases = $knowledge || [];

	const handleAddClick = () => {
		chatId.set('');
		goto('/workspace/knowledge/create');
		if ($mobile) {
			showSidebar.set(false);
		}
	};
</script>

<div class="px-1.5 flex justify-center text-gray-800 dark:text-gray-200">
	<Folder
		className="w-full"
		name="지식 기반"
		onAdd={handleAddClick}
		onAddLabel="새 지식베이스"
	>
		{#each knowledgeBases as base}
			<a
				href="/workspace/knowledge/{base.id}"
				class="flex items-center space-x-3 px-2 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900 transition text-sm"
				on:click={() => {
					if ($mobile) {
						showSidebar.set(false);
					}
				}}
			>
				<div class="flex-1 truncate text-gray-700 dark:text-gray-300">
					{base.name}
				</div>
			</a>
		{/each}
	</Folder>
</div> 